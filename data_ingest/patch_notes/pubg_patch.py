from __future__ import annotations

"""PUBG 공식 패치노트 크롤러 → raw_data.

공식 목록 페이지: https://pubg.com/ko/news?category=patch_notes
각 카드의 링크를 따라가 전체 본문을 HTML → 텍스트로 변환 후 저장한다.

Usage::
    python -m data_ingest.patch_notes.pubg_patch
"""

import asyncio
import re
from urllib.parse import urljoin
from typing import List

import aiohttp
from bs4 import BeautifulSoup, Comment

from data_ingest.common import db, logger, init_metrics
from data_ingest.common.sentry import init_sentry
from data_ingest.common.http import fetch_text, DEFAULT_USER_AGENT

INDEX_URL = "https://pubg.com/ko/news?category=patch_notes"
SOURCE = "pubg_patch"


# -----------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------

def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for el in soup(["script", "style"]):
        el.decompose()
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    text = soup.get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def _fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    return await fetch_text(url, session)


async def _extract_article_urls(session: aiohttp.ClientSession, limit: int = 30) -> List[str]:
    """Parse the index page and return latest patch note URLs."""
    html = await _fetch_html(session, INDEX_URL)
    soup = BeautifulSoup(html, "html.parser")

    links: List[str] = []
    # 뉴스 카드 div 에 a 태그가 두 개 이상일 수 있음 → href 중 "/update" 포함 체크
    for a in soup.select("a[href]"):
        href: str = a["href"]
        if "/patch-note" in href or "/patch-notes" in href or "/update" in href:
            full = urljoin(INDEX_URL, href)
            if full not in links:
                links.append(full)
        if len(links) >= limit:
            break
    return links


async def _process_article(session: aiohttp.ClientSession, url: str):
    html = await _fetch_html(session, url)
    text = _html_to_text(html)
    slug = url.rstrip("/").split("/")[-1]
    doc_id = slug
    await db.upsert_raw_data(doc_id=doc_id, source=SOURCE, text=text)
    logger.info("PUBG patch saved", extra={"url": url})


async def ingest_once(limit: int = 20):
    """Entry point for standalone run."""
    init_metrics()
    init_sentry()

    async with aiohttp.ClientSession(headers={"User-Agent": DEFAULT_USER_AGENT}) as session:
        urls = await _extract_article_urls(session, limit)
        tasks = [asyncio.create_task(_process_article(session, u)) for u in urls]
        if tasks:
            await asyncio.gather(*tasks)
    logger.info("PUBG patch ingest complete", extra={"count": len(urls)})


if __name__ == "__main__":
    asyncio.run(ingest_once()) 