"""Airflow DAG – 주1회 Vector Store 파일 TTL 기반 정리.

Vector Store 파일 중 마지막 조회가 60일 이상 지난 항목을 삭제한다.
Slack 알림, 백업 등은 추후 구현으로 남겨둔다.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator

import structlog

try:
    from openai import OpenAI  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("openai 패키지가 필요합니다: pip install openai") from exc

import os

VECTOR_STORE_ID: str | None = os.getenv("OPENAI_VECTOR_STORE_ID")
TTL_DAYS: int = int(os.getenv("VECTOR_STORE_TTL_DAYS", "60"))

logger = structlog.get_logger()

CLIENT = OpenAI()


def _cleanup():
    if not VECTOR_STORE_ID:
        logger.warning("Vector store id not set – cleanup skipped")
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=TTL_DAYS)

    files = CLIENT.beta.vector_stores.files.list(vector_store_id=VECTOR_STORE_ID, limit=1000)
    removed = 0
    for f in files.data:
        last_accessed = getattr(f, "last_accessed_at", None)
        if last_accessed and last_accessed < cutoff:
            CLIENT.beta.vector_stores.files.delete(vector_store_id=VECTOR_STORE_ID, file_id=f.id)
            removed += 1
    logger.info("Vector cleanup finished", removed=removed)


def _make_task(dag: DAG):
    return PythonOperator(
        task_id="vector_cleanup",
        python_callable=_cleanup,
        dag=dag,
    )


def _build_dag() -> DAG:
    default_args = {
        "owner": "data_ingest",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=10),
    }

    dag = DAG(
        dag_id="weekly_vector_cleanup",
        default_args=default_args,
        description="Remove stale Vector Store files (TTL days)",
        schedule_interval="0 3 * * 1",  # 매주 월요일 03:00 UTC
        start_date=datetime(2024, 1, 1),
        catchup=False,
        tags=["cleanup", "vector", "weekly"],
    )

    with dag:
        _make_task(dag)

    return dag


globals()["dag"] = _build_dag() 