from __future__ import annotations

"""OP.GG LoL 챔피언 빌드 크롤러.

챔피언-포지션 별 빌드 페이지(https://op.gg/ko/lol/champions/<champion>/build/<role>)를
HTML 파싱하여 RawDoc 으로 생성한다.

CLI 사용 예::
    python -m data_ingest.sources.opgg --mode initial

Note:
    • OP.GG 에서는 전체 챔피언 목록을 제공하는 index 페이지가 있으나 레이아웃이 자주 변한다.
      본 구현은 간단히 index 페이지를 파싱해 slug 리스트를 추출한다.
    • role 슬러그는 OP.GG 기준("top", "jungle", "mid", "adc", "support") 를 사용.
    • 페이지 구조가 바뀔 경우 `_parse_build_page` 로직을 수정해야 한다.
"""

import argparse
import asyncio
import hashlib
import re
from datetime import datetime
from typing import AsyncIterator, Dict, List, Set

import aiohttp
from bs4 import BeautifulSoup

from .base import BaseCrawler, RawDoc
from data_ingest.common import logger

__all__ = ["OPGGCrawler"]


class OPGGCrawler(BaseCrawler):
    """OP.GG 빌드 데이터 수집기."""

    source = "opgg_build"

    _INDEX_URL = "https://op.gg/ko/lol/champions"
    _BUILD_URL_TMPL = "https://op.gg/ko/lol/champions/{champion}/build/{role}"

    # OP.GG 표준 포지션 슬러그
    ROLES: List[str] = ["top", "jungle", "mid", "adc", "support"]

    # -----------------------------------------------------
    # Helper – HTML utilities
    # -----------------------------------------------------

    @staticmethod
    def _html_to_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for el in soup(["script", "style"]):
            el.decompose()
        txt = soup.get_text(" ")
        return " ".join(txt.split())

    @staticmethod
    def _sha1(text: str) -> str:
        return hashlib.sha1(text.encode()).hexdigest()[:10]

    # -----------------------------------------------------
    # Index helpers
    # -----------------------------------------------------

    async def _fetch_champion_slugs(self, session: aiohttp.ClientSession) -> List[str]:
        """챔피언 index 페이지를 파싱하여 slug 리스트를 반환."""
        async with session.get(self._INDEX_URL, timeout=30) as resp:
            resp.raise_for_status()
            html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        slugs: Set[str] = set()
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            # href 예: /ko/lol/champions/jinx/build/adc
            m = re.match(r"/ko/lol/champions/([a-z0-9\-]+)/build", href)
            if m:
                slugs.add(m.group(1))
        if not slugs:
            logger.warning("OPGG: 챔피언 slug를 찾지 못했습니다 – 파싱 로직 확인 필요")
        return sorted(slugs)

    async def _fetch_build_html(self, session: aiohttp.ClientSession, champion: str, role: str) -> str | None:
        url = self._BUILD_URL_TMPL.format(champion=champion, role=role)
        async with self._bounded():
            try:
                async with session.get(url, timeout=30) as resp:
                    if resp.status != 200:
                        logger.debug("OPGG: %s %s page status %s", champion, role, resp.status)
                        return None
                    return await resp.text()
            except Exception as e:  # noqa: BLE001
                logger.exception("OPGG: fetch error %s %s – %s", champion, role, e)
                return None

    def _make_doc_id(self, champion: str, role: str, text: str) -> str:
        return f"opgg:{champion}:{role}:{self._sha1(text)}"

    # -----------------------------------------------------
    # BaseCrawler 구현
    # -----------------------------------------------------

    async def crawl_initial(self) -> AsyncIterator[RawDoc]:
        async with aiohttp.ClientSession() as session:
            champions = await self._fetch_champion_slugs(session)
            for champ in champions:
                for role in self.ROLES:
                    html = await self._fetch_build_html(session, champ, role)
                    if not html:
                        continue
                    text = self._html_to_text(html)
                    if not text:
                        continue
                    doc_id = self._make_doc_id(champ, role, text)
                    metadata: Dict = {
                        "champion": champ,
                        "role": role,
                        "source": "opgg",
                    }
                    yield RawDoc(doc_id=doc_id, text=text, metadata=metadata)

    async def crawl_incremental(self, since: datetime):
        """OP.GG 는 실시간 빌드 데이터를 제공하지만, 간단히 전체 재수집으로 대체."""
        async for doc in self.crawl_initial():
            yield doc


# -----------------------------------------------------------------
# CLI entry
# -----------------------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(description="OP.GG LoL build crawler")
    p.add_argument(
        "--mode",
        choices=["initial", "incremental"],
        default="incremental",
        help="crawl mode",
    )
    return p


def main():
    args = _build_parser().parse_args()
    crawler = OPGGCrawler()

    if args.mode == "initial":
        asyncio.run(crawler.run_initial())
    else:
        asyncio.run(crawler.run_incremental())


if __name__ == "__main__":
    main() 