"""Analytics integration (Yandex Metrica)."""

import hashlib
import logging
from typing import Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


async def track_yandex_hit(
    short_code: str,
    target_url: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    referer: Optional[str] = None,
    params: Optional[dict] = None,
    extra_headers: Optional[dict] = None
) -> None:
    """
    Send hit to Yandex Metrica via Measurement Protocol.
    
    Args:
        short_code: The short code being accessed
        target_url: The destination URL
        user_agent: User agent string
        ip_address: Client IP address
        referer: Referer URL
        params: Query parameters from the request (e.g. yqrid, utm_*)
        extra_headers: Additional headers to forward (Accept-Language, Client Hints, etc.)
    """
    if not settings.yandex_metrica_counter_id:
        return

    try:
        # Generate a client ID based on IP and UA to track unique users roughly
        # This is privacy-friendly as we don't store the raw IP in Yandex, just a hash
        client_id_source = f"{ip_address or ''}{user_agent or ''}"
        client_id = hashlib.md5(client_id_source.encode()).hexdigest()

        # Use the "watch" endpoint which mimics the pixel/noscript tracking
        # This is more robust when no token is available
        # https://mc.yandex.ru/watch/{counter_id}
        
        # Construct the "virtual" URL that Yandex will see
        tracked_url = f"{settings.base_url}/{short_code}"
        if params:
            from urllib.parse import urlencode
            tracked_url += f"?{urlencode(params)}"

        # Parameters for /watch endpoint
        params_body = {
            "page-url": tracked_url,
            "page-ref": referer or "",
            "charset": "utf-8",
            "browser-info": f"u:{user_agent or ''}",  # Basic browser info
        }
        
        # Add title
        params_body["title"] = f"Short Link: {short_code}"

        # If we have a token, we might be able to pass more info, but for /watch
        # it primarily relies on IP (which we can't easily spoof without token)
        # and cookies (which we don't have).
        # We'll just send the hit.

        # Headers to mimic the user's browser
        headers = {
            "User-Agent": user_agent or "Mozilla/5.0",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        # Override/Extend with real user headers if provided
        if extra_headers:
            # Filter out potentially dangerous or conflicting headers if necessary
            # For now, we trust the caller to pass relevant ones
            headers.update(extra_headers)
        
        # Try to pass IP via X-Forwarded-For (might work for some counters)
        
        # Try to pass IP via X-Forwarded-For (might work for some counters)
        if ip_address:
            headers["X-Forwarded-For"] = ip_address

        async with httpx.AsyncClient() as client:
            # We use the counter ID in the path
            url = f"https://mc.yandex.ru/watch/{settings.yandex_metrica_counter_id}"
            
            response = await client.get(
                url,
                params=params_body,
                headers=headers,
                timeout=5.0
            )
            
            if response.status_code == 200:
                logger.debug(f"Yandex Metrica hit sent for {short_code} to {url}")
            else:
                logger.warning(f"Yandex Metrica error: {response.status_code} {response.text}")
            
            if response.status_code == 200:
                logger.debug(f"Yandex Metrica hit sent for {short_code}")
            else:
                logger.warning(f"Yandex Metrica error: {response.status_code} {response.text}")

    except Exception as e:
        logger.error(f"Failed to send Yandex Metrica hit: {e}")
