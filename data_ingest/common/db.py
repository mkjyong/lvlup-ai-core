"""데이터베이스 커넥션 풀 래퍼.

- 환경변수 `PG_CONN_STR` 로 접속 문자열 주입
- `Database.connection()` async context manager 제공
- CRUD 헬퍼 함수(fetch_raw_data, upsert_game_knowledge)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterator, List

# Metrics
from data_ingest.common.metrics import UPSERT_LATENCY_SECONDS

import asyncpg

PG_CONN_STR = os.getenv("PG_CONN_STR", "postgresql://postgres:postgres@localhost:5432/postgres")
PG_SSL_MODE = os.getenv("PG_SSL_MODE")  # e.g. "require" for Supabase, "disable" for local


class Database:
    """AsyncPG 기반 단일톤 커넥션 풀."""

    def __init__(self, dsn: str = PG_CONN_STR, min_size: int = 1, max_size: int = 10):
        self._dsn = self._normalize_dsn(dsn)
        self._min_size = min_size
        self._max_size = max_size
        self._pool: asyncpg.Pool | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_dsn(dsn: str) -> str:  # noqa: D401
        """Convert SQLAlchemy-style DSN (postgresql+asyncpg://) → asyncpg DSN.

        asyncpg expects schemes like ``postgresql://`` or ``postgres://``.
        If a driver suffix exists (e.g. ``+asyncpg``), it is stripped.
        """

        import re

        return re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", dsn)

    async def init(self) -> None:
        if self._pool is None:
            pool_kwargs = dict(
                dsn=self._dsn,
                min_size=self._min_size,
                max_size=self._max_size,
                command_timeout=60,
            )
            # Enable SSL if PG_SSL_MODE is set (recommended for Supabase)
            if PG_SSL_MODE:
                pool_kwargs["ssl"] = PG_SSL_MODE

            self._pool = await asyncpg.create_pool(**pool_kwargs)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[asyncpg.Connection]:
        """Acquire & release a connection from the pool."""
        if self._pool is None:
            await self.init()
        assert self._pool is not None
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    # -----------------------------------------------------
    # Helper query methods
    # -----------------------------------------------------

    async def fetch_raw_data(
        self,
        since: datetime,
        limit: int = 1000,
        source: str | None = None,
    ) -> List[asyncpg.Record]:
        """미처리 raw_data 레코드 조회.

        Args:
            since: 조회 시작 시각(이후).
            limit: 최대 행 수.
            source: 특정 데이터 소스(raw_data.source)로 필터링. None이면 전체.
        """

        if source is None:
            sql = """
            SELECT id, doc_id, text
            FROM raw_data
            WHERE processed=false
              AND created_at >= $1
            ORDER BY created_at ASC
            LIMIT $2;
            """
            params = [since, limit]
        else:
            sql = """
            SELECT id, doc_id, text
            FROM raw_data
            WHERE processed=false
              AND created_at >= $1
              AND source = $2
            ORDER BY created_at ASC
            LIMIT $3;
            """
            params = [since, source, limit]

        async with self.connection() as conn:
            return await conn.fetch(sql, *params)

    async def mark_processed(self, ids: List[int]) -> None:
        if not ids:
            return
        sql = "UPDATE raw_data SET processed=true WHERE id = ANY($1::int[])"
        async with self.connection() as conn:
            await conn.execute(sql, ids)

    async def upsert_game_knowledge(
        self,
        doc_id: str,
        chunk_id: int,
        text: str,
        score: float,
        *,
        embedding: list[float] | None = None,
        metadata: dict | None = None,
        raw_text: str | None = None,
    ) -> None:
        """`game_knowledge` 테이블 UPSERT.

        Args:
            doc_id: 원본 문서 식별자
            chunk_id: 순차 번호
            text: 압축(clean)된 텍스트(임베딩 대상)
            embedding: 벡터 값
            score: 품질 점수
            metadata: 추가 메타데이터(JSONB)
            raw_text: 압축 이전 원문 문단(선택)
        """

        sql = """
        INSERT INTO game_knowledge (doc_id, chunk_id, text, raw_text, embedding, score, metadata, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, now())
        ON CONFLICT (doc_id, chunk_id)
        DO UPDATE SET text=$3, raw_text=$4, embedding=$5, score=$6, metadata=$7, updated_at=now();
        """
        async with self.connection() as conn:
            with UPSERT_LATENCY_SECONDS.time():
                await conn.execute(sql, doc_id, chunk_id, text, raw_text, embedding, score, metadata)

    # -------------------------------------------------------------
    # Helper for novelty check
    # -------------------------------------------------------------

    async def fetch_existing_texts(self, source: str, limit: int = 100) -> List[str]:
        """Return sample of existing texts for given source to compute novelty."""
        sql = """
        SELECT text FROM game_knowledge
        WHERE metadata->>'source' = $1
        ORDER BY updated_at DESC
        LIMIT $2;
        """
        async with self.connection() as conn:
            rows = await conn.fetch(sql, source, limit)
        return [r["text"] for r in rows]

    # ---------------------------------------------
    # Raw data insert / upsert helpers
    # ---------------------------------------------

    async def upsert_raw_data(
        self,
        doc_id: str,
        source: str,
        text: str,
    ) -> None:
        """Insert raw_data row if not exists (doc_id unique within source).

        Duplicate (doc_id, source) rows will be ignored to keep idempotency.
        """
        sql = """
        INSERT INTO raw_data (doc_id, source, text, processed, created_at)
        VALUES ($1, $2, $3, false, now())
        ON CONFLICT (doc_id, source) DO NOTHING;
        """
        async with self.connection() as conn:
            await conn.execute(sql, doc_id, source, text)

    # -------------------------------------------------------------
    # Summarizer helpers
    # -------------------------------------------------------------

    async def fetch_chunks_without_summary(self, limit: int = 500):
        """Return rows from game_knowledge where summary is missing in metadata."""
        sql = """
        SELECT doc_id, chunk_id, text, embedding, score, metadata
        FROM game_knowledge
        WHERE (metadata->>'summary') IS NULL
        ORDER BY updated_at ASC
        LIMIT $1
        """
        async with self.connection() as conn:
            return await conn.fetch(sql, limit)

    # -------------------------------------------------------------
    # Feedback helpers
    # -------------------------------------------------------------

    async def insert_rag_feedback(
        self,
        query: str,
        answer: str | None,
        chunk_ids: list[int] | None,
        hit: bool,
        model_version: str | None = None,
    ) -> None:
        sql = """
        INSERT INTO rag_feedback (query, answer, chunk_ids, hit, model_version)
        VALUES ($1, $2, $3, $4, $5);
        """
        async with self.connection() as conn:
            await conn.execute(sql, query, answer, chunk_ids, hit, model_version)

    async def queue_chunk_for_review(self, chunk_id: int, doc_id: str, reason: str) -> None:
        """Insert into review_queue if not exists."""
        sql = """
        INSERT INTO review_queue (chunk_id, doc_id, reason)
        VALUES ($1, $2, $3)
        ON CONFLICT (chunk_id) DO NOTHING;
        """
        async with self.connection() as conn:
            await conn.execute(sql, chunk_id, doc_id, reason)

    async def fetch_pending_reviews(self, limit: int = 500):
        sql = """
        SELECT rq.id, rq.chunk_id, rq.doc_id, gk.text, gk.score, gk.embedding, gk.metadata
        FROM review_queue rq
        JOIN game_knowledge gk USING(chunk_id, doc_id)
        WHERE rq.status = 'pending'
        ORDER BY rq.created_at ASC
        LIMIT $1;
        """
        async with self.connection() as conn:
            return await conn.fetch(sql, limit)

    async def mark_review_done(self, review_ids: list[int]):
        if not review_ids:
            return
        sql = "UPDATE review_queue SET status='done', updated_at=NOW() WHERE id = ANY($1::int[])"
        async with self.connection() as conn:
            await conn.execute(sql, review_ids)


db = Database() 