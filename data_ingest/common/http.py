from __future__ import annotations

"""HTTP helper utilities with unified User-Agent and retry logic."""

import os
import asyncio
import aiohttp
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

DEFAULT_USER_AGENT = os.getenv("USER_AGENT", "data-ingest-bot/1.0")
DEFAULT_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "3"))

# Concurrency limit per process
MAX_CONCURRENCY = int(os.getenv("HTTP_CONCURRENCY", "10"))

_SEM = asyncio.Semaphore(MAX_CONCURRENCY)

# Shared TCPConnector with per-host limit
_CONNECTOR = aiohttp.TCPConnector(limit_per_host=5)


class _HttpError(Exception):
    """Custom wrapper so tenacity can retry on aiohttp errors."""


@retry(
    wait=wait_exponential(min=1, max=10),
    stop=stop_after_attempt(MAX_RETRIES),
    retry=retry_if_exception_type(_HttpError),
)
async def fetch_text(url: str, session: aiohttp.ClientSession | None = None) -> str:
    """Fetch text content with unified headers & exponential backoff."""
    close_session = False
    if session is None:
        session = aiohttp.ClientSession(headers={"User-Agent": DEFAULT_USER_AGENT}, connector=_CONNECTOR)
        close_session = True

    try:
        async with _SEM:
            async with session.get(url, timeout=DEFAULT_TIMEOUT) as resp:
                resp.raise_for_status()
                return await resp.text()
    except (aiohttp.ClientError, aiohttp.ClientResponseError, asyncio.TimeoutError) as exc:  # type: ignore[name-defined]
        raise _HttpError(str(exc)) from exc
    finally:
        if close_session:
            await session.close() 