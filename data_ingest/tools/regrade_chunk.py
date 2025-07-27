#!/usr/bin/env python3
"""CLI: Process review_queue chunks, recompute score & embedding, update DB.

Usage:
    python -m data_ingest.tools.regrade_chunk --limit 500 --min_score 0.75
"""

from __future__ import annotations

import asyncio
import typer

from data_ingest.common import (
    db,
    clean_text,
    compute_score,
    logger,
    QUALITY_SCORE_HISTOGRAM,
)

app = typer.Typer(add_completion=False)


@app.command()
def run(limit: int = 500, min_score: float = 0.75):
    """Re-evaluate chunks listed in review_queue (status=pending)."""
    asyncio.run(_process(limit, min_score))


async def _process(limit: int, min_score: float):
    rows = await db.fetch_pending_reviews(limit)
    if not rows:
        logger.info("No pending reviews")
        return

    processed_review_ids = []

    for r in rows:
        review_id: int = r["id"]
        text: str = r["text"]
        doc_id: str = r["doc_id"]
        chunk_id: int = r["chunk_id"]

        cleaned = clean_text(text)
        score = compute_score(cleaned, keywords=[], llm_relevance=None)
        QUALITY_SCORE_HISTOGRAM.observe(score)

        if score < min_score:
            # deactivate chunk by setting score 0 and metadata flag
            meta = r["metadata"] or {}
            meta["deprecated"] = True
            await db.upsert_game_knowledge(
                doc_id=doc_id,
                chunk_id=chunk_id,
                text=text,
                score=score,
                embedding=r["embedding"],
                metadata=meta,
            )
            processed_review_ids.append(review_id)
            continue

        # 벡터를 다시 계산하지 않고 메타·점수만 업데이트
        await db.upsert_game_knowledge(
            doc_id=doc_id,
            chunk_id=chunk_id,
            text=cleaned,
            score=score,
            embedding=None,
            metadata=r["metadata"],
        )
        processed_review_ids.append(review_id)

    await db.mark_review_done(processed_review_ids)
    logger.info("Regraded %d chunks", len(processed_review_ids))


if __name__ == "__main__":
    run() 