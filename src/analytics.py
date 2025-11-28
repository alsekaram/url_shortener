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
    params: Optional[dict] = None
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
    """
    if not settings.yandex_metrica_counter_id:
        return

    try:
        # Generate a client ID based on IP and UA to track unique users roughly
        # This is privacy-friendly as we don't store the raw IP in Yandex, just a hash
        client_id_source = f"{ip_address or ''}{user_agent or ''}"
        client_id = hashlib.md5(client_id_source.encode()).hexdigest()

        # Prepare parameters for Measurement Protocol
        # https://yandex.com/support/metrica/code/measurement-protocol.html
        
        # Construct the "virtual" URL that Yandex will see
        # We append the query params here so Yandex sees ?yqrid=... etc.
        tracked_url = f"{settings.base_url}/{short_code}"
        if params:
            from urllib.parse import urlencode
            tracked_url += f"?{urlencode(params)}"

        params_body = {
            "tid": settings.yandex_metrica_counter_id,
            "cid": client_id,
            "url": tracked_url,
            "referer": referer or "",
            "ua": user_agent or "",
            "uip": ip_address or "",  # User IP (requires token)
        }
        
        # Add title if possible, or just use short code
        params_body["dt"] = f"Short Link: {short_code}"

        # If we have a token, we can send IP address for better geo-location
        # Note: 'uip' parameter requires the 'ms' (token) parameter to work
        if settings.yandex_metrica_token:
            params_body["ms"] = settings.yandex_metrica_token
        else:
            # If no token, remove uip as it won't be processed
            params_body.pop("uip", None)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://mc.yandex.ru/watch",
                params=params_body,
                timeout=5.0
            )
            
            if response.status_code == 200:
                logger.debug(f"Yandex Metrica hit sent for {short_code}")
            else:
                logger.warning(f"Yandex Metrica error: {response.status_code} {response.text}")

    except Exception as e:
        logger.error(f"Failed to send Yandex Metrica hit: {e}")
