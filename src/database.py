"""Async database operations with SQLite."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiosqlite

from src.config import settings
from src.models import Link, LinkStats

logger = logging.getLogger(__name__)


def get_db_path() -> str:
    """Get database path, ensuring parent directory exists."""
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)


async def create_tables() -> None:
    """Create database tables if they don't exist."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT UNIQUE NOT NULL,
                target_url TEXT NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link_id INTEGER NOT NULL,
                clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT,
                ip_address TEXT,
                referer TEXT,
                FOREIGN KEY (link_id) REFERENCES links(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_clicks_link_id 
            ON clicks(link_id)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_clicks_clicked_at 
            ON clicks(clicked_at)
        """)
        
        await db.commit()
        logger.info("Database tables created successfully")


async def ensure_database_exists() -> None:
    """Ensure database and tables exist."""
    try:
        await create_tables()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def create_link(short_code: str, target_url: str, title: Optional[str] = None) -> Link:
    """Create a new short link."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            """
            INSERT INTO links (short_code, target_url, title)
            VALUES (?, ?, ?)
            """,
            (short_code, target_url, title)
        )
        await db.commit()
        
        link_id = cursor.lastrowid
        row = await db.execute_fetchall(
            "SELECT * FROM links WHERE id = ?", (link_id,)
        )
        
        if row:
            return _row_to_link(row[0])
        
        raise ValueError("Failed to create link")


async def get_link_by_code(short_code: str) -> Optional[Link]:
    """Get link by short code."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            "SELECT * FROM links WHERE short_code = ?",
            (short_code,)
        )
        row = await cursor.fetchone()
        
        if row:
            return _row_to_link(row)
        
        return None


async def update_link(short_code: str, target_url: str) -> bool:
    """Update link target URL."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            """
            UPDATE links 
            SET target_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE short_code = ?
            """,
            (target_url, short_code)
        )
        await db.commit()
        
        return cursor.rowcount > 0


async def delete_link(short_code: str) -> bool:
    """Delete a link."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            "DELETE FROM links WHERE short_code = ?",
            (short_code,)
        )
        await db.commit()
        
        return cursor.rowcount > 0


async def reset_link_clicks(short_code: str) -> int:
    """Reset all clicks for a specific link. Returns number of deleted clicks."""
    link = await get_link_by_code(short_code)
    if not link:
        raise ValueError(f"Link '{short_code}' not found")
    
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            "DELETE FROM clicks WHERE link_id = ?",
            (link.id,)
        )
        await db.commit()
        logger.info(f"Reset {cursor.rowcount} clicks for link '{short_code}'")
        return cursor.rowcount


async def get_all_links(limit: int = 50) -> list[dict]:
    """Get all links with click counts."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            """
            SELECT 
                l.id,
                l.short_code,
                l.target_url,
                l.title,
                l.created_at,
                COUNT(c.id) as clicks
            FROM links l
            LEFT JOIN clicks c ON l.id = c.link_id
            GROUP BY l.id
            ORDER BY l.created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = await cursor.fetchall()
        
        return [dict(row) for row in rows]


async def log_click(
    link_id: int,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    referer: Optional[str] = None
) -> None:
    """Log a click event."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            """
            INSERT INTO clicks (link_id, user_agent, ip_address, referer)
            VALUES (?, ?, ?, ?)
            """,
            (link_id, user_agent, ip_address, referer)
        )
        await db.commit()


async def get_total_clicks(short_code: str) -> int:
    """Get total number of clicks for a link."""
    link = await get_link_by_code(short_code)
    if not link:
        raise ValueError(f"Link '{short_code}' not found")
    
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM clicks WHERE link_id = ?",
            (link.id,)
        )
        row = await cursor.fetchone()
        return row["count"] if row else 0


async def get_link_clicks(short_code: str, limit: int = 50) -> list[dict]:
    """Get recent clicks for a specific link with metadata."""
    link = await get_link_by_code(short_code)
    if not link:
        raise ValueError(f"Link '{short_code}' not found")
    
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            """
            SELECT 
                clicked_at,
                ip_address,
                user_agent,
                referer
            FROM clicks
            WHERE link_id = ?
            ORDER BY clicked_at DESC
            LIMIT ?
            """,
            (link.id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_link_stats(short_code: str, days: int = 7) -> dict:
    """Get statistics for a specific link."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        # Get link info
        link = await get_link_by_code(short_code)
        if not link:
            raise ValueError(f"Link '{short_code}' not found")
        
        # Get clicks in period
        since_date = datetime.now() - timedelta(days=days)
        cursor = await db.execute(
            """
            SELECT COUNT(*) as count
            FROM clicks
            WHERE link_id = ? AND clicked_at >= ?
            """,
            (link.id, since_date.isoformat())
        )
        row = await cursor.fetchone()
        clicks_period = row["count"] if row else 0
        
        # Get total clicks
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM clicks WHERE link_id = ?",
            (link.id,)
        )
        row = await cursor.fetchone()
        total_clicks = row["count"] if row else 0
        
        avg_per_day = clicks_period / days if days > 0 else 0
        
        return {
            "short_code": short_code,
            "title": link.title,
            "clicks": clicks_period,
            "total_clicks": total_clicks,
            "avg_per_day": avg_per_day,
            "days": days
        }


async def get_daily_stats() -> list[LinkStats]:
    """Get statistics for the last 24 hours."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        yesterday = datetime.now() - timedelta(days=1)
        day_before = datetime.now() - timedelta(days=2)
        
        cursor = await db.execute(
            """
            SELECT 
                l.short_code,
                l.title,
                COUNT(CASE WHEN c.clicked_at >= ? THEN 1 END) as clicks_today,
                COUNT(CASE WHEN c.clicked_at >= ? AND c.clicked_at < ? THEN 1 END) as clicks_yesterday,
                COUNT(c.id) as total_clicks
            FROM links l
            LEFT JOIN clicks c ON l.id = c.link_id
            GROUP BY l.id
            HAVING clicks_today > 0 OR clicks_yesterday > 0
            ORDER BY clicks_today DESC
            """,
            (yesterday.isoformat(), day_before.isoformat(), yesterday.isoformat())
        )
        
        rows = await cursor.fetchall()
        stats = []
        
        for row in rows:
            clicks_today = row["clicks_today"]
            clicks_yesterday = row["clicks_yesterday"]
            
            change_percent = None
            if clicks_yesterday > 0:
                change_percent = ((clicks_today - clicks_yesterday) / clicks_yesterday) * 100
            
            stats.append(LinkStats(
                short_code=row["short_code"],
                title=row["title"],
                clicks_period=clicks_today,
                total_clicks=row["total_clicks"],
                avg_per_day=clicks_today,
                change_percent=change_percent
            ))
        
        return stats


async def get_weekly_stats() -> list[LinkStats]:
    """Get statistics for the last 7 days."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        week_ago = datetime.now() - timedelta(days=7)
        
        cursor = await db.execute(
            """
            SELECT 
                l.short_code,
                l.title,
                COUNT(CASE WHEN c.clicked_at >= ? THEN 1 END) as clicks_week,
                COUNT(c.id) as total_clicks
            FROM links l
            LEFT JOIN clicks c ON l.id = c.link_id
            GROUP BY l.id
            HAVING clicks_week > 0
            ORDER BY clicks_week DESC
            LIMIT 10
            """,
            (week_ago.isoformat(),)
        )
        
        rows = await cursor.fetchall()
        stats = []
        
        for row in rows:
            clicks_week = row["clicks_week"]
            avg_per_day = clicks_week / 7
            
            stats.append(LinkStats(
                short_code=row["short_code"],
                title=row["title"],
                clicks_period=clicks_week,
                total_clicks=row["total_clicks"],
                avg_per_day=avg_per_day
            ))
        
        return stats


def _row_to_link(row: aiosqlite.Row) -> Link:
    """Convert database row to Link model."""
    return Link(
        id=row["id"],
        short_code=row["short_code"],
        target_url=row["target_url"],
        title=row["title"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"])
    )


