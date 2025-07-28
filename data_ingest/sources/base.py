from __future__ import annotations

"""크롤러 공통 베이스.

새로운 크롤러는 `BaseCrawler` 를 상속하고 `source` 식별자와
`crawl_initial`, `crawl_incremental` 메서드를 구현하면 된다.

각 Raw 문서는 raw_data 테이블에 저장된다. (중복 방지 위해 doc_id 고유)
증분 수집을 위해 crawler_state 테이블에 마지막 타임스탬프를 기록한다.
"""

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Dict, List

import asyncpg

from data_ingest.common import db, logger

# -----------------------------------------------------
# Dataclass / types
# -----------------------------------------------------


@dataclass(slots=True)
class RawDoc:
    """수집된 단일 문서 단위."""

    doc_id: str  # site::unique_id 형태 권장
    text: str
    metadata: Dict | None = None  # 추가 메타데이터 (url, title, license 등)


# -----------------------------------------------------
# Base crawler
# -----------------------------------------------------


class BaseCrawler(ABC):
    """새 크롤러 구현을 위한 추상 클래스."""

    #: raw_data.source 에 저장될 식별자. 하위 클래스에서 오버라이드.
    source: str = "base"

    def __init__(self) -> None:
        self._sem = asyncio.Semaphore(5)  # 기본 동시 요청 제한

    # ---------------------------------------------
    # 메인 엔드포인트 (override)
    # ---------------------------------------------

    @abstractmethod
    async def crawl_initial(self) -> AsyncIterator[RawDoc]:
        """최초 전체 수집."""

    @abstractmethod
    async def crawl_incremental(self, since: datetime) -> AsyncIterator[RawDoc]:
        """`since` 이후 변경분 수집."""

    # ---------------------------------------------
    # Helper – crawler_state
    # ---------------------------------------------

    async def _get_last_ts(self) -> datetime | None:
        sql = "SELECT last_ts FROM crawler_state WHERE source = $1"
        async with db.connection() as conn:
            row = await conn.fetchrow(sql, self.source)
        return row["last_ts"] if row else None

    async def _set_last_ts(self, ts: datetime) -> None:
        sql = """
        INSERT INTO crawler_state (source, last_ts)
        VALUES ($1, $2)
        ON CONFLICT (source) DO UPDATE SET last_ts = EXCLUDED.last_ts;
        """
        async with db.connection() as conn:
            await conn.execute(sql, self.source, ts)

    # ---------------------------------------------
    # Save helper
    # ---------------------------------------------

    async def _save_raw_doc(self, doc: RawDoc) -> None:
        await db.upsert_raw_data(doc_id=doc.doc_id, source=self.source, text=doc.text)

    # ---------------------------------------------
    # Public runners
    # ---------------------------------------------

    async def run_initial(self) -> None:
        logger.info("Initial crawl start", extra={"source": self.source})
        count = 0
        async for doc in self.crawl_initial():
            await self._save_raw_doc(doc)
            count += 1
        await self._set_last_ts(datetime.now(timezone.utc))
        logger.info("Initial crawl complete", extra={"source": self.source, "count": count})

    async def run_incremental(self) -> None:
        since = await self._get_last_ts()
        if since is None:
            logger.warning("No last_ts found – fallback to initial crawl", extra={"source": self.source})
            await self.run_initial()
            return

        logger.info("Incremental crawl start", extra={"source": self.source, "since": since.isoformat()})
        count = 0
        async for doc in self.crawl_incremental(since):
            await self._save_raw_doc(doc)
            count += 1
        await self._set_last_ts(datetime.now(timezone.utc))
        logger.info("Incremental crawl complete", extra={"source": self.source, "count": count})

    # ---------------------------------------------
    # Rate-limit helper (context manager)
    # ---------------------------------------------

    @asynccontextmanager
    async def _bounded(self):  # noqa: D401 – not a public fn
        """`async with self._bounded(): …` 패턴으로 사용되는 rate-limit helper."""
        async with self._sem:
            yield 