"""Airflow DAG – 매일 신규 chunk summary 생성.

이 DAG는 game_knowledge 테이블에서 summary 가 없는 row를 가져와
OpenAI로 1문장 요약을 생성 후 metadata.summary 필드를 채운다.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from data_ingest.common.sentry import init_sentry
from data_ingest.common.metrics import init_metrics
from data_ingest.common import db, logger
from data_ingest.common.summarizer import summarize_chunks

BATCH_LIMIT = 200
PARALLEL = 4


def _run_summarizer(**context):  # type: ignore[override]
    init_metrics()
    init_sentry()
    asyncio.run(_process())


async def _process():
    rows = await db.fetch_chunks_without_summary(BATCH_LIMIT)
    if not rows:
        logger.info("No chunks require summary")
        return

    texts = [r["text"] for r in rows]
    summaries = await summarize_chunks(texts)

    tasks = []
    for row, summary in zip(rows, summaries):
        meta = row["metadata"] or {}
        meta["summary"] = summary
        tasks.append(
            db.upsert_game_knowledge(
                doc_id=row["doc_id"],
                chunk_id=row["chunk_id"],
                text=row["text"],
                score=row["score"],
                embedding=None,  # embedding deprecated
                metadata=meta,
            )
        )
        if len(tasks) >= PARALLEL:
            await asyncio.gather(*tasks)
            tasks.clear()

    if tasks:
        await asyncio.gather(*tasks)

    logger.info("Summaries updated", extra={"count": len(summaries)})


def _default_args():
    return {
        "owner": "data_ingest",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=10),
    }


dag = DAG(
    dag_id="daily_chunk_summarizer",
    schedule_interval="0 6 * * *",  # 매일 06:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=_default_args(),
    description="Generate 1-line summary for new chunks",
    tags=["ingest", "summary"],
)

with dag:
    summarize_task = PythonOperator(
        task_id="summarize_chunks",
        python_callable=_run_summarizer,
        provide_context=True,
    ) 