"""FastAPI web server for link redirects."""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

from src.config import settings
from src.database import ensure_database_exists, get_link_by_code, log_click

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager."""
    # Startup
    logger.info("Starting Link Tracker API...")
    try:
        await ensure_database_exists()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Link Tracker API...")


app = FastAPI(
    title="Doctor Link Tracker",
    description="Short link tracking service with Telegram reports",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "link-tracker",
        "version": "0.1.0"
    }


@app.get("/{code}")
async def redirect_link(
    code: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Redirect short link to target URL and log the click.
    
    Args:
        code: Short link code
        request: FastAPI request object
        background_tasks: Background tasks manager
        
    Returns:
        RedirectResponse to target URL
        
    Raises:
        HTTPException: If link not found
    """
    logger.info(f"Redirect request for code: {code}")
    
    # Get link from database
    link = await get_link_by_code(code)
    
    if not link:
        logger.warning(f"Link not found: {code}")
        raise HTTPException(status_code=404, detail="Link not found")
    
    # Extract request metadata
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    referer = request.headers.get("referer")
    
    # Log click in background
    background_tasks.add_task(
        log_click,
        link_id=link.id,
        user_agent=user_agent,
        ip_address=ip_address,
        referer=referer
    )
    
    logger.info(f"Redirecting {code} -> {link.target_url}")
    
    # Redirect to target URL
    return RedirectResponse(url=link.target_url, status_code=302)


@app.get("/api/links/{code}/stats")
async def get_link_stats(code: str):
    """
    Get statistics for a specific link.
    
    Args:
        code: Short link code
        
    Returns:
        Link statistics
    """
    from src.database import get_link_stats as get_stats
    
    try:
        stats = await get_stats(code, days=7)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler."""
    return {
        "error": "not_found",
        "message": "The requested resource was not found",
        "path": str(request.url.path)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )


