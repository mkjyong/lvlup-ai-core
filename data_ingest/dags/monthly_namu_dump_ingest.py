from __future__ import annotations

"""Airflow DAG – 월 1회 나무위키 덤프 파싱.

변수/연동:
    • AIRFLOW Variable `NAMU_DUMP_PATH` – 최신 덤프(.json 또는 .json.gz) 경로.
    • 덤프는 초기 수집과 동일하게 처리하므로 매월 전체 ingest.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator

# ----------------------------------------------

NAMU_DUMP_PATH = Variable.get("NAMU_DUMP_PATH", default_var="/data/namu/latest.json.gz")

default_args = {
    "owner": "data_ingest",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=30),
}

dag = DAG(
    dag_id="monthly_namu_dump_ingest",
    default_args=default_args,
    description="Monthly Namuwiki dump ingest",
    schedule_interval="0 3 1 * *",  # 매달 1일 03:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingest", "namuwiki"],
)

with dag:
    BashOperator(
        task_id="ingest_namu_dump",
        bash_command=f"python -m data_ingest.sources.namu_dump {NAMU_DUMP_PATH}",
    ) 