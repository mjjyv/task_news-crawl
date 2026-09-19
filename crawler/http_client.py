"""HTTP Client with anti-blocking features, rotating User-Agent, retry, and rate limiting."""

import asyncio
import logging
import random
import time
from typing import Dict, Optional

import httpx

from crawler.config import settings

logger = logging.getLogger(__name__)


class HttpClient:
    """HTTP Client tailored for scraping VnExpress with rate limiting and retry mechanism."""

    def __init__(
        self,
        min_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.min_delay = min_delay if min_delay is not None else settings.download_delay_min
        self.max_delay = max_delay if max_delay is not None else settings.download_delay_max
        self.timeout = timeout if timeout is not None else settings.request_timeout
        self.max_retries = max_retries if max_retries is not None else settings.max_retries
        self._last_request_time: float = 0.0

        self._sync_client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

    def _get_random_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        ua = random.choice(settings.user_agents)
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def _apply_delay_sync(self):
        elapsed = time.time() - self._last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request_time = time.time()

    async def _apply_delay_async(self):
        elapsed = time.time() - self._last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last_request_time = time.time()

    def get_sync_client(self) -> httpx.Client:
        if self._sync_client is None or self._sync_client.is_closed:
            try:
                import h2
                has_h2 = True
            except ImportError:
                has_h2 = False
            self._sync_client = httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                http2=has_h2,
            )
        return self._sync_client

    def get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            try:
                import h2
                has_h2 = True
            except ImportError:
                has_h2 = False
            self._async_client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                http2=has_h2,
            )
        return self._async_client

    def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Fetch URL synchronously with retry and delay."""
        client = self.get_sync_client()
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            self._apply_delay_sync()
            req_headers = self._get_random_headers(headers)
            try:
                logger.debug("Fetching (sync) [%d/%d]: %s", attempt, self.max_retries, url)
                response = client.get(url, headers=req_headers)
                if response.status_code in (429, 500, 502, 503, 504):
                    logger.warning("HTTP %d for %s (attempt %d/%d)", response.status_code, url, attempt, self.max_retries)
                    backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                    time.sleep(backoff)
                    continue
                response.raise_for_status()
                return response
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exception = exc
                logger.warning("Request error on %s: %s (attempt %d/%d)", url, exc, attempt, self.max_retries)
                backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                time.sleep(backoff)

        raise RuntimeError(f"Failed to fetch {url} after {self.max_retries} attempts: {last_exception}")

    async def fetch_async(self, url: str, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Fetch URL asynchronously with retry and delay."""
        client = self.get_async_client()
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            await self._apply_delay_async()
            req_headers = self._get_random_headers(headers)
            try:
                logger.debug("Fetching (async) [%d/%d]: %s", attempt, self.max_retries, url)
                response = await client.get(url, headers=req_headers)
                if response.status_code in (429, 500, 502, 503, 504):
                    logger.warning("HTTP %d for %s (attempt %d/%d)", response.status_code, url, attempt, self.max_retries)
                    backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                    await asyncio.sleep(backoff)
                    continue
                response.raise_for_status()
                return response
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exception = exc
                logger.warning("Request error on %s: %s (attempt %d/%d)", url, exc, attempt, self.max_retries)
                backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                await asyncio.sleep(backoff)

        raise RuntimeError(f"Failed to fetch {url} after {self.max_retries} attempts: {last_exception}")

    def close(self):
        if self._sync_client and not self._sync_client.is_closed:
            self._sync_client.close()

    async def aclose(self):
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
