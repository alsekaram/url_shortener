.PHONY: help build up down restart logs logs-web logs-scheduler shell db-shell clean init test reset-clicks

# Default target
help:
	@echo "Doctor Link Tracker - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make init          - Initial setup (create .env, data dir)"
	@echo "  make build         - Build Docker images"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo ""
	@echo "Management:"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - View logs (all services)"
	@echo "  make logs-web      - View web server logs"
	@echo "  make logs-scheduler - View scheduler logs"
	@echo "  make shell         - Open shell in web container"
	@echo "  make db-shell      - Open SQLite database shell"
	@echo ""
	@echo "CLI Commands:"
	@echo "  make create CODE=<code> URL=<url> [TITLE=<title>]  - Create link"
	@echo "  make update CODE=<code> URL=<url>                   - Update link"
	@echo "  make delete CODE=<code>                             - Delete link"
	@echo "  make reset-clicks CODE=<code> [FORCE=1]             - Reset click counter"
	@echo "  make list                                           - List all links"
	@echo "  make stats CODE=<code> [DAYS=7]                     - Show statistics"
	@echo "  make report-daily                                   - Send daily report"
	@echo "  make report-weekly                                  - Send weekly report"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Remove containers and volumes"
	@echo "  make rebuild       - Rebuild and restart services"

# Setup commands
init:
	@echo "Creating .env file from example..."
	@if [ ! -f .env ]; then \
		cp .env.example .env 2>/dev/null || echo "# Create .env manually from README" > .env; \
		echo "✓ .env created - please edit with your settings"; \
	else \
		echo "✓ .env already exists"; \
	fi
	@echo "Creating data directory..."
	@mkdir -p data
	@echo "✓ Setup complete! Edit .env and run 'make up'"

# Docker commands
build:
	docker compose build

up:
	docker compose up -d
	@echo "✓ Services started"
	@echo "  Web: http://localhost:8000"
	@echo "  Health: http://localhost:8000/health"

down:
	docker compose down

restart:
	docker compose restart

rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d

# Logs
logs:
	docker compose logs -f

logs-web:
	docker compose logs -f web

logs-scheduler:
	docker compose logs -f scheduler

# Shell access
shell:
	docker compose exec web bash

db-shell:
	docker compose exec web sqlite3 /app/data/links.db

# CLI commands (require CODE, URL, TITLE, DAYS variables)
create:
	@if [ -z "$(CODE)" ] || [ -z "$(URL)" ]; then \
		echo "Usage: make create CODE=<code> URL=<url> [TITLE=<title>]"; \
		exit 1; \
	fi
	@if [ -n "$(TITLE)" ]; then \
		docker compose exec web uv run python -m src.cli create $(CODE) $(URL) --title "$(TITLE)"; \
	else \
		docker compose exec web uv run python -m src.cli create $(CODE) $(URL); \
	fi

update:
	@if [ -z "$(CODE)" ] || [ -z "$(URL)" ]; then \
		echo "Usage: make update CODE=<code> URL=<url>"; \
		exit 1; \
	fi
	docker compose exec web uv run python -m src.cli update $(CODE) $(URL)

delete:
	@if [ -z "$(CODE)" ]; then \
		echo "Usage: make delete CODE=<code>"; \
		exit 1; \
	fi
	docker compose exec web uv run python -m src.cli delete $(CODE)

reset-clicks:
	@if [ -z "$(CODE)" ]; then \
		echo "Usage: make reset-clicks CODE=<code> [FORCE=1]"; \
		exit 1; \
	fi
	@if [ "$(FORCE)" = "1" ]; then \
		docker compose exec web uv run python -m src.cli reset-clicks $(CODE) --force; \
	else \
		docker compose exec -it web uv run python -m src.cli reset-clicks $(CODE); \
	fi

list:
	docker compose exec web uv run python -m src.cli list

stats:
	@if [ -z "$(CODE)" ]; then \
		echo "Usage: make stats CODE=<code> [DAYS=7]"; \
		exit 1; \
	fi
	@if [ -n "$(DAYS)" ]; then \
		docker compose exec web uv run python -m src.cli stats $(CODE) --days $(DAYS); \
	else \
		docker compose exec web uv run python -m src.cli stats $(CODE); \
	fi

report-daily:
	docker compose exec scheduler uv run python -m src.cli send-report daily

report-weekly:
	docker compose exec scheduler uv run python -m src.cli send-report weekly

# Cleanup
clean:
	docker compose down -v
	@echo "✓ Containers and volumes removed"
	@echo "  Note: data/ directory preserved"

# Health check
health:
	@curl -f http://localhost:8000/health || echo "Service not responding"


