# Environment Setup

Create a `.env` file in the root directory with the following content:

```bash
# Server
HOST=0.0.0.0
PORT=8000
DATABASE_PATH=/app/data/links.db

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Reports Schedule
DAILY_REPORT_TIME=09:00
WEEKLY_REPORT_DAY=monday
WEEKLY_REPORT_TIME=09:00
TIMEZONE=Europe/Moscow

# Logging
LOG_LEVEL=INFO
```

## How to get Telegram credentials

### Get BOT_TOKEN:
1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot` command
3. Follow instructions
4. Copy the token (format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Get CHAT_ID:
1. Start a chat with [@userinfobot](https://t.me/userinfobot)
2. Copy your ID (format: `123456789`)

Or for group:
1. Add bot to the group
2. Send any message
3. Open: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find `"chat":{"id":...}` in response

## Quick start

```bash
# 1. Copy this template
cat ENV_SETUP.md

# 2. Create .env file
cat > .env << 'EOF'
HOST=0.0.0.0
PORT=8000
DATABASE_PATH=/app/data/links.db
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
DAILY_REPORT_TIME=09:00
WEEKLY_REPORT_DAY=monday
WEEKLY_REPORT_TIME=09:00
TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
EOF

# 3. Edit with your values
nano .env

# 4. Start the service
make up
```


