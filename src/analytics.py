"""Analytics integration (Yandex Metrica)."""

import hashlib
import logging
import time
import random
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
    """Send hit to Yandex Metrica via Measurement Protocol."""
    logger.info(f"track_yandex_hit called for {short_code}")

    if not settings.yandex_metrica_counter_id:
        logger.warning("No Yandex counter ID configured")
        return

    try:
        # Construct the tracked URL
        tracked_url = f"{settings.base_url}/{short_code}"
        if params:
            from urllib.parse import urlencode
            tracked_url += f"?{urlencode(params)}"

        # browser-info в правильном формате Яндекса
        # pv:1 - pageview
        # vf:1 - ???
        # fu:1 - first user visit
        # en:utf-8 - encoding
        # la:ru - language
        # st:{timestamp} - время на странице
        # rqn:1 - request number
        browser_info_parts = [
            "pv:1",           # pageview - ОБЯЗАТЕЛЬНО
            "vf:1",
            "fu:0",
            "en:utf-8",
            "la:ru",
            f"st:{int(time.time())}",
            "rqn:1"
        ]
        browser_info = ":".join(browser_info_parts)

        params_body = {
            "page-url": tracked_url,
            "page-ref": referer or "",
            "browser-info": browser_info,
            "rn": random.randint(1, 999999999),  # cache buster - ВАЖНО
        }

        headers = {
            "User-Agent": user_agent or "Mozilla/5.0",  # Fallback only if absolutely no UA provided
        }
        
        if extra_headers:
            headers.update(extra_headers)
        
        if ip_address:
            headers["X-Forwarded-For"] = ip_address

        async with httpx.AsyncClient() as client:
            url = f"https://mc.yandex.ru/watch/{settings.yandex_metrica_counter_id}"
            
            logger.info(f"Sending request to {url} with params {params_body}")
            
            response = await client.get(
                url,
                params=params_body,
                headers=headers,
                timeout=5.0,
                follow_redirects=True
            )
            
            logger.info(f"Yandex Metrica: {response.status_code}, {len(response.content)} bytes")
            logger.debug(f"Request URL: {response.url}")

    except Exception as e:
        logger.error(f"Failed to send Yandex Metrica hit: {e}", exc_info=True)
