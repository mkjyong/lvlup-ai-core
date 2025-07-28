from __future__ import annotations

"""MetaSRC LoL 챔피언 빌드 크롤러.

주의: MetaSRC 는 비공개 API(JSON)를 사용하므로, 본 구현은 Public HTML 페이지를
단순 파싱한다. 사이트 구조가 빈번히 변할 수 있으므로 오류 발생 시 `_fetch_build_html`
및 `_html_to_text` 로직을 수정해야 한다.
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

__all__ = ["MetaSRCCrawler"]


class MetaSRCCrawler(BaseCrawler):
    """MetaSRC 빌드 데이터 수집기."""

    source = "metasrc_build"

    _INDEX_URL = "https://www.metasrc.com/lol/champions"
    # role slug는 메타소스에서 upper-case("ADC") 하지만 lower-case 허용 URL 리다이렉트
    _BUILD_URL_TMPL = "https://www.metasrc.com/lol/champion/{champion}/{role}"

    ROLES: List[str] = ["top", "jungle", "mid", "adc", "support"]

    # -----------------------------------------------------
    # HTML helpers
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
        async with session.get(self._INDEX_URL, timeout=30) as resp:
            resp.raise_for_status()
            html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        slugs: Set[str] = set()
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            # e.g. /lol/champion/jinx/adc
            m = re.match(r"/lol/champion/([a-z0-9\-]+)/[a-z]+", href)
            if m:
                slugs.add(m.group(1))
        if not slugs:
            logger.warning("MetaSRC: 챔피언 slug 파싱 실패 – 로직 검토 필요")
        return sorted(slugs)

    async def _fetch_build_html(self, session: aiohttp.ClientSession, champion: str, role: str) -> str | None:
        url = self._BUILD_URL_TMPL.format(champion=champion, role=role)
        async with self._bounded():
            try:
                async with session.get(url, timeout=30) as resp:
                    if resp.status != 200:
                        logger.debug("MetaSRC: %s %s page status %s", champion, role, resp.status)
                        return None
                    return await resp.text()
            except Exception as e:  # noqa: BLE001
                logger.exception("MetaSRC fetch error %s %s – %s", champion, role, e)
                return None

    def _make_doc_id(self, champion: str, role: str, text: str) -> str:
        return f"metasrc:{champion}:{role}:{self._sha1(text)}"

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
                        "source": "metasrc",
                    }
                    yield RawDoc(doc_id=doc_id, text=text, metadata=metadata)

    async def crawl_incremental(self, since: datetime):
        # 단순 전체 재수집
        async for doc in self.crawl_initial():
            yield doc


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(description="MetaSRC LoL build crawler")
    p.add_argument(
        "--mode",
        choices=["initial", "incremental"],
        default="incremental",
        help="crawl mode",
    )
    return p


def main():
    args = _build_parser().parse_args()
    crawler = MetaSRCCrawler()

    if args.mode == "initial":
        asyncio.run(crawler.run_initial())
    else:
        asyncio.run(crawler.run_incremental())


if __name__ == "__main__":
    main() 