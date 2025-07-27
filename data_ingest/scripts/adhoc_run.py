#!/usr/bin/env python3
"""임시 CLI 진입점.

`python scripts/adhoc_run.py --source video_transcripts --since 2024-01-01 --parallel 4`
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from data_ingest.common import (
    db,
    clean_text,
    compute_score,
    logger,
    init_metrics,
    INGEST_PROCESSED_TOTAL,
    INGEST_LATENCY_SECONDS,
    QUALITY_SCORE_HISTOGRAM,
)
from data_ingest.common.openai_vector import upsert_text
from data_ingest.common.relevance import get_llm_relevance
from data_ingest.common.sentry import init_sentry
from data_ingest.common import config as _cfg
from data_ingest.common.filters import get_keywords, fast_keyword_pass

app = typer.Typer(add_completion=False)


@app.command()
def run(
    source: str = typer.Option(..., help="데이터 소스 식별자(raw_data.source)", prompt=True),
    since: str = typer.Option("1970-01-01", help="YYYY-MM-DD 형식"),
    parallel: int = typer.Option(1, min=1, help="동시 임베딩 병렬 수"),
    limit: int = typer.Option(1000, help="최대 처리 레코드 수"),
    batch_size: int = typer.Option(100, help="fetch_raw_data batch size"),
    min_score: float = typer.Option(_cfg.MIN_QUALITY_SCORE, help="임계 품질 점수"),
    dry_run: bool = typer.Option(False, help="DB upsert 수행하지 않음"),
):
    """Raw 데이터(특정 source) → clean/score/chunk/embed/upsert."""

    since_dt = datetime.fromisoformat(since)

    # Start Prometheus exporter once
    init_metrics()

    # Init Sentry if configured
    init_sentry()

    logger.info("Starting adhoc ingest", extra={"source": source, "since": since, "limit": limit})

    asyncio.run(_process(source, since_dt, limit, parallel, batch_size, min_score, dry_run))


async def _process(
    source: str,
    since_dt: datetime,
    limit: int,
    parallel: int,
    batch_size: int = 100,
    min_score: float = _cfg.MIN_QUALITY_SCORE,
    dry_run: bool = False,
) -> None:

    processed_ids: list[int] = []

    # Fetch in batches
    offset_dt = since_dt
    total_fetched = 0

    while total_fetched < limit:
        to_fetch = min(batch_size, limit - total_fetched)
        with INGEST_LATENCY_SECONDS.time():
            rows = await db.fetch_raw_data(offset_dt, to_fetch, source)

        if not rows:
            break

        total_fetched += len(rows)

        # metrics
        INGEST_PROCESSED_TOTAL.labels(source=source).inc(len(rows))
        logger.info("Fetched batch", extra={"rows": len(rows), "total": total_fetched})

        tasks = []
        results: list[tuple[int, bool]] = []  # (row id, success)

        async def _wrap(row):
            ok = await _handle_row(row, min_score, dry_run, source)
            return (row["id"], ok)

        for row in rows:
            tasks.append(_wrap(row))
            if len(tasks) >= parallel:
                results.extend(await asyncio.gather(*tasks))
                tasks.clear()

        if tasks:
            results.extend(await asyncio.gather(*tasks))

        # collect successful ids
        processed_ids.extend([rid for rid, ok in results if ok])

        # update offset_dt to last created_at (assumes ordered)
        offset_dt = datetime.utcnow()

        if dry_run:
            logger.info("Dry-run mode – skipping mark_processed")
        else:
            await db.mark_processed([rid for rid, ok in results if ok])

    if not dry_run:
        logger.info("Finished ingest", extra={"rows": len(processed_ids)})

    # Close pool
    await db.close()


async def _handle_row(row, min_score: float, dry_run: bool, source: str | None = None) -> bool:
    text: str = row["text"]
    doc_id: str = row["doc_id"]

    cleaned = clean_text(text)

    # Fast keyword pre-filter
    kw_list = get_keywords(source or "")
    if kw_list and not fast_keyword_pass(cleaned, kw_list):
        logger.debug("Skip by keyword filter", extra={"id": row["id"]})
        return False

    # LLM relevance 분류 + 요약(JSON) (캐시 포함)
    llm_relevance, llm_summary = await get_llm_relevance(cleaned)

    # Retrieve existing texts for novelty calculation
    existing_texts = await db.fetch_existing_texts(source or "", limit=100)

    score = compute_score(
        cleaned,
        keywords=kw_list,
        existing_texts=existing_texts,
        llm_relevance=llm_relevance,
    )

    QUALITY_SCORE_HISTOGRAM.observe(score)

    if score < min_score:
        logger.debug("Skip low score", extra={"id": row["id"], "score": score})
        return False

    # Metadata 구성
    language = None
    try:
        from langdetect import detect  # type: ignore

        language = detect(cleaned)
    except Exception:
        pass

    metadata_common: dict[str, str | float | None] = {
        "source": source,
        "language": language,
        "model_version": "vector_store", # Assuming vector store doesn't have a model version
    }

    # 요약 추가 (있을 때만)
    if llm_summary:
        metadata_common["summary"] = llm_summary

    # Patch version 추출(예: 14.5)
    import re

    m = re.search(r"(\d+\.\d+)", text)
    if m:
        metadata_common["patch_version"] = m.group(1)

    if dry_run:
        logger.info("Dry-run: would upload doc %s to Vector Store", doc_id)
        return True

    try:
        await upsert_text(doc_id, cleaned, metadata_common)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Vector Store 업로드 실패 doc %s: %s", doc_id, exc)
        return False 