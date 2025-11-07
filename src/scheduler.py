"""Scheduler for automatic reports using APScheduler."""

import asyncio
import logging
import signal
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import settings
from src.telegram import send_daily_report, send_weekly_report

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Scheduler for automatic Telegram reports."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = AsyncIOScheduler(timezone=settings.timezone)
        self.shutdown_event = asyncio.Event()
        
    def setup_jobs(self):
        """Set up scheduled jobs."""
        # Parse daily report time
        try:
            hour, minute = map(int, settings.daily_report_time.split(':'))
            self.scheduler.add_job(
                send_daily_report,
                CronTrigger(hour=hour, minute=minute, timezone=settings.timezone),
                id='daily_report',
                name='Daily Report',
                replace_existing=True
            )
            logger.info(f"Daily report scheduled at {settings.daily_report_time} ({settings.timezone})")
        except Exception as e:
            logger.error(f"Failed to schedule daily report: {e}")
        
        # Parse weekly report time and day
        try:
            hour, minute = map(int, settings.weekly_report_time.split(':'))
            # Convert day name to number (0 = Monday, 6 = Sunday)
            day_map = {
                'monday': 0, 'mon': 0,
                'tuesday': 1, 'tue': 1,
                'wednesday': 2, 'wed': 2,
                'thursday': 3, 'thu': 3,
                'friday': 4, 'fri': 4,
                'saturday': 5, 'sat': 5,
                'sunday': 6, 'sun': 6
            }
            day_of_week = day_map.get(settings.weekly_report_day.lower(), 0)
            
            self.scheduler.add_job(
                send_weekly_report,
                CronTrigger(
                    day_of_week=day_of_week,
                    hour=hour,
                    minute=minute,
                    timezone=settings.timezone
                ),
                id='weekly_report',
                name='Weekly Report',
                replace_existing=True
            )
            logger.info(
                f"Weekly report scheduled on {settings.weekly_report_day} "
                f"at {settings.weekly_report_time} ({settings.timezone})"
            )
        except Exception as e:
            logger.error(f"Failed to schedule weekly report: {e}")
    
    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("📅 Scheduler started successfully")
        
        # Print next run times
        jobs = self.scheduler.get_jobs()
        if jobs:
            logger.info("Scheduled jobs:")
            for job in jobs:
                next_run = job.next_run_time
                if next_run:
                    logger.info(f"  - {job.name}: next run at {next_run}")
    
    def stop(self):
        """Stop the scheduler gracefully."""
        logger.info("Stopping scheduler...")
        self.scheduler.shutdown(wait=True)
        self.shutdown_event.set()
        logger.info("Scheduler stopped")
    
    async def run(self):
        """Run the scheduler until interrupted."""
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start scheduler
        self.start()
        
        # Keep running until shutdown event
        try:
            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            logger.info("Scheduler cancelled")
            self.stop()


async def main():
    """Main entry point for the scheduler."""
    logger.info("Starting Link Tracker Scheduler...")
    
    try:
        scheduler = ReportScheduler()
        scheduler.setup_jobs()
        await scheduler.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        sys.exit(1)
    finally:
        logger.info("Scheduler shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())


