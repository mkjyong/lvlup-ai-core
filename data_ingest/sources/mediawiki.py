from __future__ import annotations

"""MediaWiki 기반 사이트(Fandom, Liquipedia, StrategyWiki) 공통 크롤러."""

import asyncio
import hashlib
from datetime import datetime, timezone
from typing import AsyncIterator, Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

from .base import BaseCrawler, RawDoc
from data_ingest.common import logger


class MediaWikiCrawler(BaseCrawler):
    """MediaWiki REST API(v1)/api.php 를 사용하는 범용 크롤러."""

    # 하위 클래스에서 설정해야 하는 값들
    api_endpoint: str = ""  # 예: https://liquipedia.net/dota2/api.php
    site_tag: str = "mediawiki"

    # MediaWiki 요청 파라미터
    _DEFAULT_LIMIT = 500

    # -----------------------------------------
    # HTML → text helper
    # -----------------------------------------

    @staticmethod
    def _html_to_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        # 스크립트/스타일 제거
        for el in soup(["script", "style"]):
            el.decompose()
        text = soup.get_text(" ")
        return " ".join(text.split())

    # -----------------------------------------
    # API helpers
    # -----------------------------------------

    async def _fetch_json(self, session: aiohttp.ClientSession, params: Dict) -> Dict:
        params.setdefault("format", "json")
        async with session.get(self.api_endpoint, params=params, timeout=30) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _fetch_page_extract(self, session: aiohttp.ClientSession, pageid: int) -> Optional[str]:
        params = {
            "action": "parse",
            "pageid": pageid,
            "prop": "text",
            "formatversion": 2,
        }
        data = await self._fetch_json(session, params)
        html = data.get("parse", {}).get("text")
        if not html:
            return None
        return self._html_to_text(html)

    async def _iter_all_pageids(self, session: aiohttp.ClientSession) -> AsyncIterator[int]:
        """allpages API 를 통해 pageid 스트림 생성."""
        apcontinue = None
        while True:
            params = {
                "action": "query",
                "list": "allpages",
                "aplimit": self._DEFAULT_LIMIT,
            }
            if apcontinue:
                params["apcontinue"] = apcontinue
            data = await self._fetch_json(session, params)
            pages = data["query"]["allpages"]
            for p in pages:
                yield p["pageid"]
            if "continue" in data and "apcontinue" in data["continue"]:
                apcontinue = data["continue"]["apcontinue"]
            else:
                break

    async def _iter_recent_pageids(self, session: aiohttp.ClientSession, since: datetime) -> AsyncIterator[int]:
        rccontinue = None
        since_unix = int(since.replace(tzinfo=timezone.utc).timestamp())
        while True:
            params = {
                "action": "query",
                "list": "recentchanges",
                "rcstart": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "rcdir": "newer",
                "rctype": "edit|new",
                "rclimit": self._DEFAULT_LIMIT,
            }
            if rccontinue:
                params["rccontinue"] = rccontinue
            data = await self._fetch_json(session, params)
            for rc in data["query"].get("recentchanges", []):
                yield rc["pageid"]
            if "continue" in data and "rccontinue" in data["continue"]:
                rccontinue = data["continue"]["rccontinue"]
            else:
                break

    # -----------------------------------------
    # BaseCrawler 구현
    # -----------------------------------------

    async def crawl_initial(self) -> AsyncIterator[RawDoc]:
        async with aiohttp.ClientSession() as session:
            async for pageid in self._iter_all_pageids(session):
                text = await self._fetch_page_extract(session, pageid)
                if not text:
                    continue
                doc_id = self._make_doc_id(pageid, text)
                yield RawDoc(doc_id=doc_id, text=text)

    async def crawl_incremental(self, since: datetime) -> AsyncIterator[RawDoc]:
        async with aiohttp.ClientSession() as session:
            async for pageid in self._iter_recent_pageids(session, since):
                text = await self._fetch_page_extract(session, pageid)
                if not text:
                    continue
                doc_id = self._make_doc_id(pageid, text)
                yield RawDoc(doc_id=doc_id, text=text)

    # -----------------------------------------
    # Dedup helper – include content hash
    # -----------------------------------------

    @staticmethod
    def _sha1(text: str) -> str:
        import hashlib

        return hashlib.sha1(text.encode()).hexdigest()[:10]

    def _make_doc_id(self, pageid: int, text: str) -> str:
        """pageid + hash 조합으로 동일 내용 재임베딩 방지."""
        return f"{self.site_tag}:{pageid}:{self._sha1(text)}" 