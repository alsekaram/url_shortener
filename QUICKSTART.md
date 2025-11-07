# 🚀 Quick Start Guide

Get Doctor Link Tracker running in 5 minutes!

## Step 1: Prerequisites

Ensure you have:
- ✅ Docker installed
- ✅ Docker Compose v2 installed

```bash
# Check Docker
docker --version
docker compose version
```

## Step 2: Clone & Setup

```bash
# Clone repository (if not already)
cd /path/to/url_shortener

# Create data directory
mkdir -p data

# Create .env file
cat > .env << 'EOF'
HOST=0.0.0.0
PORT=8000
DATABASE_PATH=/app/data/links.db
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
DAILY_REPORT_TIME=09:00
WEEKLY_REPORT_DAY=monday
WEEKLY_REPORT_TIME=09:00
TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
EOF
```

## Step 3: Configure Telegram

1. **Create bot**: Message [@BotFather](https://t.me/BotFather) → `/newbot`
2. **Get your ID**: Message [@userinfobot](https://t.me/userinfobot)
3. **Update .env**: Replace `YOUR_BOT_TOKEN` and `YOUR_CHAT_ID`

```bash
# Edit .env
nano .env
```

## Step 4: Launch! 🚀

```bash
# Build and start all services
docker compose up -d

# Wait a few seconds, then check
curl http://localhost:8000/health
```

Expected output:
```json
{"status":"healthy","service":"link-tracker","version":"0.1.0"}
```

## Step 5: Create Your First Link

```bash
# Create a short link
docker compose exec web uv run python -m src.cli create \
  doctor1 \
  https://instagram.com/doctor1 \
  --title "Doctor Smith"

# Test it
curl -L http://localhost:8000/doctor1
```

## Step 6: View Stats

```bash
# List all links
docker compose exec web uv run python -m src.cli list

# Get statistics
docker compose exec web uv run python -m src.cli stats doctor1 --days 7

# Send test report
docker compose exec scheduler uv run python -m src.cli send-report daily
```

## Step 7: Use Makefile (Optional)

For convenience, use Makefile commands:

```bash
# Create link
make create CODE=doctor1 URL=https://instagram.com/doctor1 TITLE="Doctor Smith"

# List links
make list

# View stats
make stats CODE=doctor1

# View logs
make logs

# Send report
make report-daily
```

## 🎉 You're Ready!

Your link tracker is now running at **http://localhost:8000**

- 📊 Check logs: `docker compose logs -f`
- 🛑 Stop: `docker compose down`
- 🔄 Restart: `docker compose restart`
- 📖 Full docs: See [README.md](README.md)

## Common Commands Cheatsheet

```bash
# Management
docker compose up -d          # Start
docker compose down           # Stop
docker compose logs -f        # View logs
docker compose restart        # Restart

# CLI (through docker)
docker compose exec web uv run python -m src.cli create <code> <url> --title "Title"
docker compose exec web uv run python -m src.cli list
docker compose exec web uv run python -m src.cli stats <code>
docker compose exec web uv run python -m src.cli delete <code>

# Or use Makefile
make up / down / restart / logs
make create / list / stats / delete
make report-daily / report-weekly
```

## Need Help?

- 📖 Read full [README.md](README.md)
- 🔍 Check [Troubleshooting section](README.md#-troubleshooting)
- 📊 View logs: `make logs`

Happy tracking! 🎯


