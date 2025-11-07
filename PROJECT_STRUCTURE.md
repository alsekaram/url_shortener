# 📁 Project Structure

Complete overview of the Doctor Link Tracker project.

## 🗂️ Directory Layout

```
url_shortener/
├── 📄 Configuration Files
│   ├── .python-version         # Python version (3.12)
│   ├── .gitignore             # Git ignore rules
│   ├── .dockerignore          # Docker ignore rules
│   ├── pyproject.toml         # Python dependencies (uv)
│   ├── docker-compose.yml     # Docker Compose config
│   ├── Makefile               # Convenience commands
│   ├── env.template           # Environment variables template
│   └── .env                   # Environment variables (create this!)
│
├── 📚 Documentation
│   ├── README.md              # Main documentation (⭐️ start here)
│   ├── START_HERE.md          # Quick start guide
│   ├── QUICKSTART.md          # Step-by-step setup
│   ├── ENV_SETUP.md           # Environment setup
│   └── PROJECT_STRUCTURE.md   # This file
│
├── 🐳 Docker
│   └── docker/
│       └── Dockerfile         # Multi-stage Docker build
│
├── 💾 Data (created at runtime)
│   └── data/
│       └── links.db           # SQLite database
│
└── 🐍 Source Code
    └── src/
        ├── __init__.py        # Package init
        ├── __main__.py        # CLI entry point
        ├── main.py            # FastAPI web server ⭐️
        ├── cli.py             # Typer CLI commands ⭐️
        ├── database.py        # Async SQLite operations ⭐️
        ├── telegram.py        # Telegram bot integration ⭐️
        ├── scheduler.py       # APScheduler service ⭐️
        ├── models.py          # Pydantic data models
        └── config.py          # Settings from .env
```

## 📝 File Descriptions

### Configuration Files

#### `.python-version`
- Python version specification (3.12)
- Used by `pyenv` and `uv`

#### `.gitignore`
- Git ignore patterns
- Excludes: `__pycache__/`, `*.pyc`, `.env`, `data/`, virtual environments

#### `.dockerignore`
- Docker build context ignore patterns
- Reduces image size by excluding unnecessary files

#### `pyproject.toml`
- Python project metadata
- Dependencies managed by `uv`:
  - FastAPI, Uvicorn
  - aiosqlite
  - Typer, Rich
  - httpx (Telegram)
  - APScheduler
  - Pydantic

#### `docker-compose.yml`
- Three services:
  1. **init** - Database initialization (runs once)
  2. **web** - FastAPI server (port 8000)
  3. **scheduler** - APScheduler for reports
- Volume: `./data:/app/data`
- Health checks enabled

#### `Makefile`
- Convenience commands:
  - `make up/down/restart` - Service management
  - `make create/update/delete` - Link management
  - `make list/stats` - View data
  - `make report-daily/weekly` - Send reports
  - `make logs/shell` - Debugging

#### `env.template`
- Environment variables template
- Copy to `.env` and customize

### Documentation Files

#### `README.md` ⭐️
- **Start here!** Main documentation
- Complete feature overview
- Installation instructions
- All commands and examples
- Troubleshooting guide
- Production deployment tips

#### `START_HERE.md`
- Quick start in 3 steps
- Basic commands cheatsheet
- Usage examples

#### `QUICKSTART.md`
- Step-by-step setup guide
- Prerequisites check
- Configuration walkthrough

#### `ENV_SETUP.md`
- Environment variables explanation
- How to get Telegram credentials
- Configuration examples

#### `PROJECT_STRUCTURE.md`
- This file
- Complete project layout
- File descriptions

### Docker Files

#### `docker/Dockerfile`
- Base: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- Installs: curl (for healthcheck)
- Copies: `pyproject.toml`, `.python-version`, `src/`
- Runs: `uv sync` to install dependencies
- Creates: `/app/data` directory
- Exposes: port 8000

### Source Code

#### `src/__init__.py`
- Package initialization
- Version: 0.1.0

#### `src/__main__.py`
- Entry point for `python -m src.cli`
- Launches CLI app

#### `src/config.py`
**Purpose**: Configuration management

**Key Classes**:
- `Settings` - Pydantic settings model
- Loads from `.env` file
- Type-safe configuration access

**Settings**:
- Server: `host`, `port`, `database_path`
- Telegram: `telegram_bot_token`, `telegram_chat_id`
- Schedule: `daily_report_time`, `weekly_report_day`, etc.
- Logging: `log_level`

#### `src/models.py`
**Purpose**: Pydantic data models

**Models**:
- `LinkCreate` - Creating new links
- `LinkUpdate` - Updating links
- `Link` - Full link data
- `Click` - Click event data
- `LinkStats` - Statistics data
- `DailyReport` - Daily report structure
- `WeeklyReport` - Weekly report structure

#### `src/database.py` ⭐️
**Purpose**: Async SQLite database operations

**Key Functions**:
- `create_tables()` - Initialize DB schema
- `ensure_database_exists()` - Startup check
- `create_link()` - Add new short link
- `get_link_by_code()` - Retrieve link
- `update_link()` - Modify target URL
- `delete_link()` - Remove link
- `get_all_links()` - List all with stats
- `log_click()` - Record click event
- `get_link_stats()` - Individual link stats
- `get_daily_stats()` - 24-hour statistics
- `get_weekly_stats()` - 7-day statistics

**Tables**:
1. **links**
   - `id` (PK)
   - `short_code` (UNIQUE)
   - `target_url`
   - `title`
   - `created_at`
   - `updated_at`

2. **clicks**
   - `id` (PK)
   - `link_id` (FK)
   - `clicked_at`
   - `user_agent`
   - `ip_address`
   - `referer`

#### `src/main.py` ⭐️
**Purpose**: FastAPI web server

**Endpoints**:
- `GET /health` - Health check
- `GET /{code}` - Redirect to target URL (logs click in background)
- `GET /api/links/{code}/stats` - JSON statistics

**Features**:
- Async/await throughout
- Background task for click logging
- Lifespan context manager
- Custom 404 handler
- Logging configured

#### `src/cli.py` ⭐️
**Purpose**: Command-line interface (Typer)

**Commands**:
- `init-db` - Initialize database
- `create <code> <url>` - Create link
- `update <code> <url>` - Update link
- `delete <code>` - Delete link
- `list [--limit]` - List all links
- `stats <code> [--days]` - Show statistics
- `send-report <type>` - Send Telegram report

**Features**:
- Rich console output
- Beautiful tables
- Color-coded messages
- Async operations

#### `src/telegram.py` ⭐️
**Purpose**: Telegram bot integration

**Key Functions**:
- `send_telegram_message()` - Send message via API
- `send_daily_report()` - Format & send daily stats
- `send_weekly_report()` - Format & send weekly stats
- `send_test_message()` - Test integration
- `format_change_percent()` - Format % change with emoji

**Features**:
- HTML formatting
- Emoji indicators (📊📈📉👆)
- Error handling
- httpx async client

#### `src/scheduler.py` ⭐️
**Purpose**: Automatic report scheduling

**Key Components**:
- `ReportScheduler` class
  - `setup_jobs()` - Configure cron triggers
  - `start()` - Start scheduler
  - `stop()` - Graceful shutdown
  - `run()` - Main loop

**Features**:
- APScheduler with AsyncIO
- Cron triggers for reports
- Signal handlers (SIGINT, SIGTERM)
- Graceful shutdown
- Timezone support

**Schedule**:
- Daily report: Configurable time (default 09:00)
- Weekly report: Configurable day/time (default Monday 09:00)

## 🔄 Application Flow

### 1. Startup Flow

```
docker-compose up
    ↓
[init service]
    ├─→ Run: python -m src.cli init-db
    ├─→ Create tables
    └─→ Exit (restart: no)
    ↓
[web service]
    ├─→ Run: uvicorn src.main:app
    ├─→ FastAPI lifespan: ensure_database_exists()
    └─→ Listen on port 8000
    ↓
[scheduler service]
    ├─→ Run: python -m src.scheduler
    ├─→ Setup cron jobs
    └─→ Start APScheduler
```

### 2. Redirect Flow

```
User visits: http://localhost:8000/ivanov
    ↓
FastAPI: GET /{code}
    ↓
Database: get_link_by_code('ivanov')
    ↓
Found? → RedirectResponse (302)
    ├─→ Background: log_click()
    └─→ User redirected to target URL
    ↓
Not Found? → HTTPException (404)
```

### 3. CLI Flow

```
$ docker-compose exec web uv run python -m src.cli create ivanov https://...
    ↓
Typer: parse arguments
    ↓
asyncio.run(create_link('ivanov', 'https://...'))
    ↓
Database: INSERT INTO links
    ↓
Rich Console: Print success message
```

### 4. Report Flow

```
Cron Trigger: 09:00 daily
    ↓
APScheduler: send_daily_report()
    ↓
Database: get_daily_stats()
    ↓
Format HTML message with emojis
    ↓
httpx POST: Telegram Bot API
    ↓
User receives report in Telegram
```

## 🎯 Key Design Decisions

### 1. **Why uv?**
- Fast dependency management
- Built-in virtual environment
- Modern Python packaging
- Better than pip

### 2. **Why SQLite?**
- Simple deployment
- No separate DB server
- Good performance for this use case
- Easy backups (single file)

### 3. **Why async/await?**
- Better performance
- Non-blocking I/O
- Modern Python best practices
- FastAPI requires it

### 4. **Why Docker?**
- Consistent environment
- Easy deployment
- Isolated services
- Production-ready

### 5. **Why Separate Services?**
- `web` - Handles HTTP requests
- `scheduler` - Runs background jobs
- Separation of concerns
- Can scale independently

### 6. **Why APScheduler?**
- Cron-like scheduling
- Timezone support
- Easy to configure
- Python-native

## 🔧 Extension Points

### Add New Endpoints
Edit `src/main.py`:
```python
@app.get("/api/links")
async def list_all_links():
    # Implementation
```

### Add New CLI Command
Edit `src/cli.py`:
```python
@app.command()
def export(format: str = "json"):
    # Implementation
```

### Add New Report Type
Edit `src/telegram.py`:
```python
async def send_monthly_report():
    # Implementation
```

### Modify Schedule
Edit `.env`:
```bash
DAILY_REPORT_TIME=18:00
WEEKLY_REPORT_DAY=friday
```

## 📊 Database Schema

```sql
-- Links table
CREATE TABLE links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code TEXT UNIQUE NOT NULL,
    target_url TEXT NOT NULL,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clicks table
CREATE TABLE clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id INTEGER NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address TEXT,
    referer TEXT,
    FOREIGN KEY (link_id) REFERENCES links(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_clicks_link_id ON clicks(link_id);
CREATE INDEX idx_clicks_clicked_at ON clicks(clicked_at);
```

## 🚀 Deployment Checklist

- [ ] Copy `env.template` to `.env`
- [ ] Set Telegram credentials
- [ ] Configure timezone
- [ ] Set report schedule
- [ ] Run `docker-compose up -d`
- [ ] Check health: `curl http://localhost:8000/health`
- [ ] Create first link
- [ ] Test redirect
- [ ] Test Telegram report
- [ ] Setup backups for `data/links.db`
- [ ] Configure nginx (production)
- [ ] Setup monitoring (optional)

## 📖 Further Reading

- **FastAPI**: https://fastapi.tiangolo.com/
- **Typer**: https://typer.tiangolo.com/
- **APScheduler**: https://apscheduler.readthedocs.io/
- **uv**: https://docs.astral.sh/uv/
- **Docker Compose**: https://docs.docker.com/compose/

---

**Ready to go! All components are production-ready.** 🚀


