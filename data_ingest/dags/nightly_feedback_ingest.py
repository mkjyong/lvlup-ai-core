"""Airflow DAG – 전날 rag_feedback(hit=false) 분석하여 review_queue에 적재."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from data_ingest.common.metrics import init_metrics
from data_ingest.common.sentry import init_sentry
from data_ingest.common import db, logger

MAX_QUEUE = 1000


def _run_feedback_ingest(**context):  # type: ignore[override]
    init_metrics()
    init_sentry()
    asyncio.run(_process())


async def _process():
    # Select yesterday's failed feedback
    since = datetime.utcnow() - timedelta(days=1)
    sql = """
    SELECT chunk_id, unnest(chunk_ids) AS cid, query
    FROM rag_feedback
    WHERE hit = false AND created_at >= $1
    """
    async with db.connection() as conn:
        rows = await conn.fetch(sql, since)

    if not rows:
        logger.info("No failed feedback rows")
        return

    queued = 0
    for r in rows:
        await db.queue_chunk_for_review(r["cid"], r["chunk_id"], "hit_false")
        queued += 1
        if queued >= MAX_QUEUE:
            break
    logger.info("Queued %d chunks for review", queued)


def _default_args():
    return {
        "owner": "data_ingest",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=15),
    }


dag = DAG(
    dag_id="nightly_feedback_ingest",
    schedule_interval="0 3 * * *",  # 매일 03:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=_default_args(),
    description="Analyze rag_feedback and populate review_queue",
    tags=["feedback", "review"],
)

with dag:
    task = PythonOperator(
        task_id="feedback_to_review_queue",
        python_callable=_run_feedback_ingest,
        provide_context=True,
    ) 