# 🧠 Context for AI Assistants

## 📋 Project Overview
**Name:** Doctor Link Tracker (URL Shortener)
**Purpose:** Self-hosted URL shortener with Telegram reporting and detailed statistics.
**Stack:**
- **Language:** Python 3.11+
- **Database:** SQLite (async via `aiosqlite`)
- **Containerization:** Docker & Docker Compose
- **Package Manager:** uv
- **Interface:** CLI (Typer) & Telegram Bot

## 🏗 Architecture

### Components
1. **Web Service (`src/main.py`)**:
   - FastAPI-based web server
   - Handles redirects (`GET /{short_code}`)
   - Logs clicks to database (async)

2. **Scheduler (`src/scheduler.py`)**:
   - APScheduler running in separate container
   - Sends daily/weekly reports to Telegram
   - Uses `src/telegram.py` for messaging

3. **CLI (`src/cli.py`)**:
   - Management interface (create, list, stats)
   - Entry point for manual reports

### Database Schema (`src/database.py`)
- **links**: `id`, `short_code`, `target_url`, `title`, `created_at`, `updated_at`
- **clicks**: `id`, `link_id`, `clicked_at`, `user_agent`, `ip_address`, `referer`
  - `clicked_at`: TIMESTAMP (UTC, format "YYYY-MM-DD HH:MM:SS")

## 🔑 Key Logic

### Statistics Calculation
- **Timezone:** Database stores UTC. Python must use `datetime.utcnow()` for comparisons.
- **Date Format:** SQLite timestamps use space separator. Python comparisons must use `.strftime("%Y-%m-%d %H:%M:%S")` (NOT `.isoformat()`).
- **Daily Stats:** Compares last 24h vs previous 24h (rolling window).

### Deployment
- Server path: `/opt/url_shortener`
- Data path: `./data/links.db` (mounted to `/app/data/links.db`)
- Environment: `.env` file (not in git)

## 🛠 Common Commands (Makefile)
- `make up` - Start services
- `make rebuild` - Rebuild and restart services (use after code updates)
- `make logs` - View logs
- `make report-daily` - Send manual daily report
- `make stats CODE=xxx` - View stats for a link
- `make shell` - Access container shell

## ⚠️ Known Issues / Gotchas
1. **Timezone Mismatch:** Always use UTC in Python code to match SQLite `CURRENT_TIMESTAMP`.
2. **String Comparison:** Never compare SQLite timestamp strings with Python `.isoformat()` (T vs space).
3. **Docker Volumes:** Database is persisted in `./data` on host.

## 📝 Coding Standards
- Async/Await for all I/O
- Type hints required
- Pydantic models for data structures
- Logging instead of print
