"""Airflow DAG – 매일 04:00 UTC 게임 패치노트·블로그 인제스트."""

from __future__ import annotations

from datetime import datetime, timedelta
import asyncio

from data_ingest.common.metrics import init_metrics
from data_ingest.common.sentry import init_sentry

from airflow import DAG
from airflow.operators.python import PythonOperator

from data_ingest.scripts.adhoc_run import _process

SOURCES = ["lol_patch", "pubg_patch", "namu_wiki", "reddit_tips"]
DEFAULT_PARALLEL = 4
DEFAULT_LIMIT = 500


def _run_source(source: str):
    since_dt = datetime.utcnow() - timedelta(days=1)
    init_metrics()
    init_sentry()
    asyncio.run(_process(source, since_dt, DEFAULT_LIMIT, DEFAULT_PARALLEL))


def _build_task(dag: DAG, source: str):
    return PythonOperator(
        task_id=f"ingest_{source}",
        python_callable=_run_source,
        op_kwargs={"source": source},
        dag=dag,
    )


default_args = {
    "owner": "data_injest",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

dag = DAG(
    dag_id="daily_ingest",
    default_args=default_args,
    description="Daily ingest patch notes & blogs",
    schedule_interval="0 4 * * *",  # 매일 04:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingest", "daily"],
)

with dag:
    tasks = [_build_task(dag, src) for src in SOURCES]
    # 병렬 실행이므로 의존성 없음 