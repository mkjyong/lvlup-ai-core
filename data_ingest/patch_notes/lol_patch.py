from __future__ import annotations

"""League of Legends Patch Notes RSS → raw_data 테이블 인서트.

Riot 공식 RSS 피드가 없으므로, Cloudflare Workers 기반 community feed를 사용한다.
필요시 ENV `LOL_PATCH_RSS` 로 다른 피드 URL 주입 가능.
"""

# pylint: disable=too-many-locals
import asyncio
import os
import re
from urllib.parse import urljoin
from typing import List

import aiohttp
from bs4 import BeautifulSoup, Comment

from data_ingest.common import db, logger, init_metrics
from data_ingest.common.sentry import init_sentry
from data_ingest.common.http import fetch_text, DEFAULT_USER_AGENT

# 공식 패치노트 태그 페이지
INDEX_URL = os.getenv(
    "LOL_PATCH_INDEX_URL",
    "https://www.leagueoflegends.com/ko-kr/news/tags/patch-notes/",
)
SOURCE = "lol_patch"

# Helpers -----------------------------------------------------


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # remove scripts/styles/comments
    for el in soup(["script", "style"]):
        el.decompose()
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()

    text = soup.get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ------------------------------------------------------------
# Crawl functions
# ------------------------------------------------------------


async def _fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    return await fetch_text(url, session)


async def _extract_article_urls(session: aiohttp.ClientSession, limit: int = 50) -> List[str]:
    """Return latest patch note article URLs from index page."""
    html = await _fetch_html(session, INDEX_URL)
    soup = BeautifulSoup(html, "html.parser")

    links: List[str] = []
    for a in soup.select("a[href]"):
        href: str = a["href"]
        if "/news/game-updates/" in href and href not in links:
            links.append(urljoin(INDEX_URL, href))
        if len(links) >= limit:
            break
    return links


async def _process_article(session: aiohttp.ClientSession, url: str):
    html = await _fetch_html(session, url)
    text = _html_to_text(html)

    # doc_id: slug part of URL (e.g., patch-14-5-notes)
    doc_id = url.rstrip("/").split("/")[-1]

    await db.upsert_raw_data(doc_id=doc_id, source=SOURCE, text=text)
    logger.info("LoL patch saved", extra={"url": url})


async def ingest_once(limit: int = 20):
    """Crawl latest LoL patch note articles and insert into raw_data."""

    init_metrics()
    init_sentry()

    async with aiohttp.ClientSession(headers={"User-Agent": DEFAULT_USER_AGENT}) as session:
        urls = await _extract_article_urls(session, limit)

        tasks: List[asyncio.Task] = []
        for url in urls:
            tasks.append(asyncio.create_task(_process_article(session, url)))

        if tasks:
            await asyncio.gather(*tasks)

    logger.info("LoL patch ingest complete", extra={"count": len(urls)})


if __name__ == "__main__":
    asyncio.run(ingest_once()) 