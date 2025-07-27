"""Airflow DAG – 1시간 주기 video_transcripts 인제스트.

Prerequisites:
- AIRFLOW__CORE__LOAD_EXAMPLES=False
- Env vars: PG_CONN_STR, OPENAI_API_KEY...

명령:
```bash
# Local testing (Airflow 2.7+):
airflow dags trigger hourly_transcript_ingest
```
"""

from __future__ import annotations

from datetime import datetime, timedelta
import asyncio

from data_ingest.common.metrics import init_metrics
from data_ingest.common.sentry import init_sentry

from airflow import DAG
from airflow.operators.python import PythonOperator

from data_ingest.scripts.adhoc_run import _process  # noqa – reuse internal async logic

DEFAULT_PARALLEL = 4
DEFAULT_LIMIT = 1000
SOURCE = "video_transcripts"


def _run_ingest(**context):  # type: ignore[override]
    since_dt = datetime.utcnow() - timedelta(hours=1)

    # Export metrics & Sentry once per task instance
    init_metrics()
    init_sentry()

    asyncio.run(_process(SOURCE, since_dt, DEFAULT_LIMIT, DEFAULT_PARALLEL))


default_args = {
    "owner": "data_injest",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="hourly_transcript_ingest",
    default_args=default_args,
    description="Ingest video transcript texts hourly → pgvector",
    schedule_interval="@hourly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingest", "transcript"],
)

with dag:
    ingest_task = PythonOperator(
        task_id="ingest_transcripts",
        python_callable=_run_ingest,
        provide_context=True,
    ) 