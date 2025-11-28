"""FastAPI web server for link redirects."""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from src.analytics import track_yandex_hit
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
    # Get real client IP from proxy headers or fall back to direct connection
    ip_address = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
        request.headers.get("x-real-ip") or
        (request.client.host if request.client else None)
    )
    referer = request.headers.get("referer")
    
    referer = request.headers.get("referer")
    
    # Extract additional headers for fingerprinting
    extra_headers = {}
    for header in ["accept-language", "accept", "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform"]:
        if value := request.headers.get(header):
            extra_headers[header] = value

    # Log click in background (internal stats)
    background_tasks.add_task(
        log_click,
        link_id=link.id,
        user_agent=user_agent,
        ip_address=ip_address,
        referer=referer
    )
    
    logger.info(f"Redirecting {code} -> {link.target_url}")
    
    # Client-side redirect for better tracking
    if settings.yandex_metrica_counter_id:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Redirecting...</title>
            <!-- Yandex.Metrika counter -->
            <script type="text/javascript">
               (function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
               m[i].l=1*new Date();
               for (var j = 0; j < document.scripts.length; j++) {{if (document.scripts[j].src === r) {{ return; }}}}
               k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
               }})(window, document, "script", "https://mc.yandex.ru/metrika/tag.js?id={settings.yandex_metrica_counter_id}", "ym");

               ym({settings.yandex_metrica_counter_id}, "init", {{
                    clickmap:true,
                    trackLinks:true,
                    accurateTrackBounce:true
               }});
            </script>
            <noscript><div><img src="https://mc.yandex.ru/watch/{settings.yandex_metrica_counter_id}" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
            <!-- /Yandex.Metrika counter -->
            
            <script>
                setTimeout(function() {{
                    window.location.replace("{link.target_url}");
                }}, 100);
            </script>
            <meta http-equiv="refresh" content="1;url={link.target_url}">
        </head>
        <body>
            <p>Redirecting to <a href="{link.target_url}">{link.target_url}</a>...</p>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    # Fallback to server-side redirect if no counter ID
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
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )


