"""CLI commands for link management."""

import asyncio
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.config import settings
from src.database import (
    create_link,
    create_tables,
    delete_link,
    get_all_links,
    get_link_clicks,
    get_link_stats,
    get_total_clicks,
    reset_link_clicks,
    update_link,
)
from src.telegram import send_daily_report, send_weekly_report

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = typer.Typer(help="Doctor Link Tracker CLI")
console = Console()


@app.command()
def init_db():
    """Initialize database tables."""
    try:
        asyncio.run(create_tables())
        console.print("✓ Database initialized successfully", style="green bold")
    except Exception as e:
        console.print(f"✗ Failed to initialize database: {e}", style="red bold")
        raise typer.Exit(code=1)


@app.command()
def create(
    code: str = typer.Argument(..., help="Short code for the link"),
    url: str = typer.Argument(..., help="Target URL"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Link title/description")
):
    """Create a new short link."""
    try:
        link = asyncio.run(create_link(code, url, title))
        console.print(f"✓ Created: [blue bold]{code}[/blue bold] → {url}", style="green")
        if title:
            console.print(f"  Title: {title}", style="dim")
    except Exception as e:
        console.print(f"✗ Failed to create link: {e}", style="red bold")
        raise typer.Exit(code=1)


@app.command()
def update(
    code: str = typer.Argument(..., help="Short code of the link to update"),
    url: str = typer.Argument(..., help="New target URL")
):
    """Update target URL of an existing link."""
    try:
        success = asyncio.run(update_link(code, url))
        if success:
            console.print(f"✓ Updated: [blue bold]{code}[/blue bold] → {url}", style="green")
        else:
            console.print(f"✗ Link not found: {code}", style="red bold")
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"✗ Failed to update link: {e}", style="red bold")
        raise typer.Exit(code=1)


@app.command()
def delete(
    code: str = typer.Argument(..., help="Short code of the link to delete")
):
    """Delete a short link."""
    try:
        success = asyncio.run(delete_link(code))
        if success:
            console.print(f"✓ Deleted: [blue bold]{code}[/blue bold]", style="green")
        else:
            console.print(f"✗ Link not found: {code}", style="red bold")
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"✗ Failed to delete link: {e}", style="red bold")
        raise typer.Exit(code=1)


@app.command()
def reset_clicks(
    code: str = typer.Argument(..., help="Short code of the link to reset clicks for"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """Reset click counter for a specific link."""
    try:
        # Get current total clicks before reset
        current_clicks = asyncio.run(get_total_clicks(code))
        
        if current_clicks == 0:
            console.print(f"Link [blue bold]{code}[/blue bold] already has 0 clicks", style="yellow")
            return
        
        # Confirm action unless force flag is used
        if not force:
            console.print(f"\n⚠️  Warning: This will delete [red bold]{current_clicks}[/red bold] click records for [blue bold]{code}[/blue bold]")
            if not typer.confirm("Are you sure you want to continue?"):
                console.print("Operation cancelled", style="yellow")
                raise typer.Exit()
        
        deleted_count = asyncio.run(reset_link_clicks(code))
        console.print(
            f"✓ Reset clicks for [blue bold]{code}[/blue bold]: {deleted_count} records removed",
            style="green bold"
        )
        
    except ValueError as e:
        console.print(f"✗ {e}", style="red bold")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"✗ Failed to reset clicks: {e}", style="red bold")
        raise typer.Exit(code=1)


@app.command("list")
def list_links(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of links to show")
):
    """List all short links with statistics."""
    try:
        links = asyncio.run(get_all_links(limit))
        
        if not links:
            console.print("No links found", style="yellow")
            return
        
        table = Table(title=f"All Links (showing {len(links)})")
        table.add_column("Code", style="cyan bold", no_wrap=True)
        table.add_column("URL", style="blue")
        table.add_column("Title", style="white")
        table.add_column("Clicks", justify="right", style="green")
        table.add_column("Created", style="dim")
        
        for link in links:
            url_display = link['target_url']
            if len(url_display) > 60:
                url_display = url_display[:57] + "..."
            
            title_display = link['title'] or "-"
            if len(title_display) > 30:
                title_display = title_display[:27] + "..."
            
            created_at = link['created_at'][:10] if link['created_at'] else "-"
            
            table.add_row(
                link['short_code'],
                url_display,
                title_display,
                str(link['clicks']),
                created_at
            )
        
        console.print(table)
        console.print(f"\nTotal links: {len(links)}", style="dim")
        
    except Exception as e:
        console.print(f"✗ Failed to list links: {e}", style="red bold")
        raise typer.Exit(code=1)


@app.command()
def stats(
    code: str = typer.Argument(..., help="Short code to get statistics for"),
    days: int = typer.Option(7, "--days", "-d", help="Number of days to analyze")
):
    """Get detailed statistics for a specific link."""
    try:
        data = asyncio.run(get_link_stats(code, days))
        
        console.print(f"\n📊 Statistics: [blue bold]{code}[/blue bold]", style="bold")
        if data['title']:
            console.print(f"   Title: {data['title']}", style="dim")
        console.print()
        console.print(f"Last {days} days: [green bold]{data['clicks']}[/green bold] clicks")
        console.print(f"Total all time: [cyan bold]{data['total_clicks']}[/cyan bold] clicks")
        console.print(f"Average per day: [yellow bold]{data['avg_per_day']:.1f}[/yellow bold] clicks")
        console.print()
        
    except ValueError as e:
        console.print(f"✗ {e}", style="red bold")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"✗ Failed to get statistics: {e}", style="red bold")
        raise typer.Exit(code=1)


@app.command()
def clicks(
    code: str = typer.Argument(..., help="Short code to get click details for"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of recent clicks to show")
):
    """Show recent clicks with IP addresses and user agents."""
    try:
        clicks_data = asyncio.run(get_link_clicks(code, limit))
        
        if not clicks_data:
            console.print(f"\nNo clicks found for [blue bold]{code}[/blue bold]", style="yellow")
            return
        
        console.print(f"\n🖱️  Recent clicks for [blue bold]{code}[/blue bold]:", style="bold")
        console.print(f"Showing last {len(clicks_data)} clicks\n")
        
        table = Table(title=f"Click Details")
        table.add_column("Time", style="cyan", no_wrap=True)
        table.add_column("IP Address", style="yellow")
        table.add_column("User Agent", style="white")
        table.add_column("Referer", style="dim")
        
        for click in clicks_data:
            # Format timestamp
            timestamp = click['clicked_at']
            if timestamp:
                # Extract just date and time (remove microseconds)
                time_display = timestamp.replace('T', ' ')[:19] if 'T' in timestamp else timestamp[:19]
            else:
                time_display = "-"
            
            # Format IP
            ip_display = click['ip_address'] or "-"
            
            # Format User Agent (truncate if too long)
            user_agent = click['user_agent'] or "-"
            if len(user_agent) > 80:
                user_agent = user_agent[:77] + "..."
            
            # Format Referer (truncate if too long)
            referer = click['referer'] or "-"
            if len(referer) > 40:
                referer = referer[:37] + "..."
            
            table.add_row(time_display, ip_display, user_agent, referer)
        
        console.print(table)
        console.print(f"\nTotal clicks shown: {len(clicks_data)}", style="dim")
        
    except ValueError as e:
        console.print(f"✗ {e}", style="red bold")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"✗ Failed to get click details: {e}", style="red bold")
        raise typer.Exit(code=1)


@app.command()
def send_report(
    report_type: str = typer.Argument(
        "daily",
        help="Report type: 'daily' or 'weekly'"
    )
):
    """Manually send a report to Telegram (sends even if no activity)."""
    try:
        report_type = report_type.lower()
        
        if report_type == "daily":
            # skip_if_empty=False для ручной отправки
            asyncio.run(send_daily_report(skip_if_empty=False))
            console.print("✓ Daily report sent to Telegram", style="green bold")
        elif report_type == "weekly":
            # skip_if_empty=False для ручной отправки
            asyncio.run(send_weekly_report(skip_if_empty=False))
            console.print("✓ Weekly report sent to Telegram", style="green bold")
        else:
            console.print(
                f"✗ Invalid report type: {report_type}. Use 'daily' or 'weekly'",
                style="red bold"
            )
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"✗ Failed to send report: {e}", style="red bold")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()


