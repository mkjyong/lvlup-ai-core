from __future__ import annotations

"""CLI: Run SQL migrations in data_ingest/migrations.

Usage::

    python -m data_ingest.tools.migrate

환경변수:
    PG_CONN_STR  Postgres 연결 문자열 (asyncpg 호환)

이 스크립트는 디렉터리 내 *.sql 파일을 파일명 기준 오름차순으로 실행한다.
"""

import asyncio
import os
from pathlib import Path

import asyncpg

from data_ingest.common.logger import logger

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
PG_CONN_STR = os.getenv("PG_CONN_STR", "postgresql://postgres:postgres@localhost:5432/postgres")
PG_SSL_MODE = os.getenv("PG_SSL_MODE")  # e.g. "require" for Supabase deployments


async def _apply_migration(conn: asyncpg.Connection, sql_path: Path) -> None:
    sql = sql_path.read_text()
    logger.info("Applying migration %s", sql_path.name)
    await conn.execute(sql)


async def run_migrations() -> None:
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        logger.warning("No migration files found in %s", MIGRATIONS_DIR)
        return

    logger.info("Connecting to Postgres %s", PG_CONN_STR)
    pool_kwargs = {"dsn": PG_CONN_STR}
    if PG_SSL_MODE:
        pool_kwargs["ssl"] = PG_SSL_MODE
    async with asyncpg.create_pool(**pool_kwargs) as pool:
        async with pool.acquire() as conn:
            for f in sql_files:
                await _apply_migration(conn, f)
    logger.info("Migrations complete")


def main() -> None:
    asyncio.run(run_migrations())


if __name__ == "__main__":
    main() 