from __future__ import annotations

"""Airflow DAG – 12시간마다 Fandom·Liquipedia·StrategyWiki 증분 수집."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# 설정 -------------------------------------------------

DEFAULT_WIKI_TASKS = [
    # (module, args)
    ("data_ingest.sources.fandom", "--wiki leagueoflegends"),
    ("data_ingest.sources.liquipedia", "--game leagueoflegends"),
    ("data_ingest.sources.strategywiki", ""),
]

def _task_id(mod, arg):
    return mod.split(".")[-1] + ("_" + arg.split()[1] if arg else "")

# DAG -------------------------------------------------

default_args = {
    "owner": "data_ingest",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

dag = DAG(
    dag_id="wiki_incremental_ingest",
    default_args=default_args,
    description="Incremental ingest for game wikis",
    schedule_interval="0 4 * * *",  # 하루 한 번 (04:00 UTC)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingest", "wiki"],
)

with dag:
    for mod, arg in DEFAULT_WIKI_TASKS:
        cmd = f"python -m {mod} {arg} --mode incremental"
        BashOperator(
            task_id=_task_id(mod, arg),
            bash_command=cmd,
        ) 