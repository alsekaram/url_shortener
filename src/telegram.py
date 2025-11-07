"""Telegram bot integration for sending reports."""

import logging
from datetime import datetime, timedelta

import httpx

from src.config import settings
from src.database import get_daily_stats, get_weekly_stats

logger = logging.getLogger(__name__)


async def send_telegram_message(text: str) -> bool:
    """
    Send a message to Telegram.
    
    Args:
        text: Message text (supports Telegram markdown)
        
    Returns:
        True if message sent successfully
    """
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info("Telegram message sent successfully")
            return True
    except httpx.HTTPError as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram message: {e}")
        return False


def format_change_percent(change: float | None) -> str:
    """Format change percentage with emoji indicator."""
    if change is None:
        return ""
    
    if change > 0:
        return f"+{change:.0f}% 📈"
    elif change < 0:
        return f"{change:.0f}% 📉"
    else:
        return "0% ➡️"


async def send_daily_report() -> None:
    """Send daily statistics report to Telegram."""
    logger.info("Generating daily report...")
    
    try:
        stats = await get_daily_stats()
        
        if not stats:
            logger.info("No activity to report for today")
            # Optionally send "no activity" message
            # await send_telegram_message("📊 Сегодня переходов не было")
            return
        
        # Calculate total
        total_clicks = sum(s.clicks_period for s in stats)
        
        # Format date
        today = datetime.now().strftime("%d.%m.%Y")
        
        # Build report message
        lines = [
            "📊 <b>Статистика за 24 часа</b>",
            f"📅 {today}",
            "━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        
        for stat in stats:
            title = stat.title or stat.short_code
            lines.append(f"👨‍⚕️ <b>{title}</b>")
            lines.append(f"├─ Сегодня: <b>{stat.clicks_period}</b> 👆")
            lines.append(f"├─ Всего: {stat.total_clicks}")
            
            if stat.change_percent is not None:
                change_text = format_change_percent(stat.change_percent)
                lines.append(f"└─ {change_text}")
            else:
                lines.append("└─")
            
            lines.append("")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"<b>Всего:</b> {total_clicks} переходов")
        
        message = "\n".join(lines)
        
        await send_telegram_message(message)
        logger.info("Daily report sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send daily report: {e}")
        raise


async def send_weekly_report() -> None:
    """Send weekly statistics report to Telegram."""
    logger.info("Generating weekly report...")
    
    try:
        stats = await get_weekly_stats()
        
        if not stats:
            logger.info("No activity to report for this week")
            return
        
        # Calculate dates
        today = datetime.now()
        week_start = (today - timedelta(days=7)).strftime("%d.%m")
        week_end = today.strftime("%d.%m.%Y")
        
        # Calculate totals
        total_clicks = sum(s.clicks_period for s in stats)
        
        # Build report message
        lines = [
            "📈 <b>Отчет за неделю</b>",
            f"📅 {week_start} - {week_end}",
            "━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        
        # Show top 3 with detailed stats
        for i, stat in enumerate(stats[:3], 1):
            title = stat.title or stat.short_code
            lines.append(f"👨‍⚕️ <b>{title}</b>")
            lines.append(f"├─ За неделю: <b>{stat.clicks_period}</b> 👆")
            lines.append(f"├─ В день: ~{stat.avg_per_day:.1f}")
            lines.append(f"└─ Всего: {stat.total_clicks}")
            lines.append("")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        
        # Show top links summary
        if len(stats) > 0:
            lines.append("🏆 <b>ТОП ссылок:</b>")
            lines.append("")
            
            for i, stat in enumerate(stats[:5], 1):
                emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"][i-1]
                title = stat.title or stat.short_code
                lines.append(f"{emoji} {title} → {stat.clicks_period}")
            
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━")
        
        lines.append(f"<b>Всего за неделю:</b> {total_clicks} переходов")
        
        message = "\n".join(lines)
        
        await send_telegram_message(message)
        logger.info("Weekly report sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send weekly report: {e}")
        raise


async def send_test_message() -> None:
    """Send a test message to verify Telegram integration."""
    message = (
        "✅ <b>Тест успешен!</b>\n\n"
        "Бот для отслеживания ссылок настроен и готов к работе.\n\n"
        "Вы будете получать автоматические отчеты:\n"
        f"• Ежедневно в {settings.daily_report_time}\n"
        f"• Еженедельно по {settings.weekly_report_day} в {settings.weekly_report_time}"
    )
    
    await send_telegram_message(message)


