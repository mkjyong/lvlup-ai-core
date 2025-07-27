from __future__ import annotations

"""Generic Game Blog Crawler → raw_data.

Usage::
    python -m data_ingest.blogs.crawler https://example.com/article

스크립트는 단일 URL 또는 URL 목록 파일을 입력받아 HTML → 텍스트 추출 후 `raw_data` 테이블에 저장한다.
"""

import asyncio
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import List

import aiohttp
from bs4 import BeautifulSoup, Comment

from data_ingest.common import db, clean_text, logger, init_metrics
from data_ingest.common.sentry import init_sentry

SOURCE = "blogs"


async def _fetch(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, timeout=20) as resp:
        resp.raise_for_status()
        return await resp.text()


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts/styles/comments
    for el in soup(["script", "style"]):
        el.decompose()
    for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
        c.extract()
    text = soup.get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def _process_url(session: aiohttp.ClientSession, url: str) -> None:
    html = await _fetch(session, url)
    text = _html_to_text(html)
    # Use URL hash as doc_id for idempotency
    doc_id = hashlib.sha256(url.encode()).hexdigest()
    await db.upsert_raw_data(doc_id=doc_id, source=SOURCE, text=text)
    logger.info("Blog crawled", extra={"url": url})


async def crawl(urls: List[str]) -> None:
    init_metrics()
    init_sentry()

    async with aiohttp.ClientSession() as session:
        tasks = [_process_url(session, u) for u in urls]
        await asyncio.gather(*tasks)
    logger.info("Blog crawl complete", extra={"count": len(urls)})


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: crawler.py <url> [url ...] or crawler.py -f url_list.txt")
        sys.exit(1)

    if sys.argv[1] == "-f":
        path = Path(sys.argv[2])
        urls_list = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    else:
        urls_list = sys.argv[1:]

    asyncio.run(crawl(urls_list)) 