"""Data-ingest daemon – continuously ingest raw_data rows in the background.

Usage:
    python -m data_ingest               # via __main__.py
    python -m data_ingest.daemon        # explicit module path

Configuration via environment variables (optional):
    INGEST_SOURCES        comma-separated list of raw_data.source values to process
                          default: "lol_patch,pubg_patch,namu_wiki"
    INGEST_LOOP_INTERVAL  seconds between sweep iterations (default: 300)
    INGEST_LIMIT          maximum rows to process per source per sweep (default: 1000)
    INGEST_PARALLEL       parallel embedding workers per source (default: 4)
    INGEST_BATCH_SIZE     batch size for DB fetch in _process (default: 100)
    MIN_QUALITY_SCORE     quality threshold override (falls back to config)

The daemon reuses the internal `_process` coroutine from
`data_ingest.scripts.adhoc_run` to avoid duplicating ingest logic.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta

from data_ingest.common import (
    logger,  # shared structured logger
    init_metrics,
)
from data_ingest.common import config as _cfg
from data_ingest.common.sentry import init_sentry
from data_ingest.scripts.adhoc_run import _process

# ---------------------------------------------------------------------------
# Resolve runtime configuration from environment variables once at startup.
# ---------------------------------------------------------------------------

SOURCES: list[str] = [
    src.strip()
    for src in os.getenv("INGEST_SOURCES", "lol_patch,pubg_patch,namu_wiki").split(",")
    if src.strip()
]
LOOP_INTERVAL: int = int(os.getenv("INGEST_LOOP_INTERVAL", "300"))
LIMIT: int = int(os.getenv("INGEST_LIMIT", "1000"))
PARALLEL: int = int(os.getenv("INGEST_PARALLEL", "4"))
BATCH_SIZE: int = int(os.getenv("INGEST_BATCH_SIZE", "100"))
MIN_SCORE: float = float(os.getenv("MIN_QUALITY_SCORE", str(_cfg.MIN_QUALITY_SCORE)))
DRY_RUN: bool = os.getenv("INGEST_DRY_RUN", "false").lower() in ("1", "true", "yes")


async def _sweep_once(since_dt: datetime) -> None:
    """Run one ingest sweep across all configured sources."""

    for src in SOURCES:
        try:
            logger.info("Ingest sweep start", extra={"source": src})
            await _process(
                src,
                since_dt=since_dt,
                limit=LIMIT,
                parallel=PARALLEL,
                batch_size=BATCH_SIZE,
                min_score=MIN_SCORE,
                dry_run=DRY_RUN,
            )
        except Exception as exc:  # noqa: BLE001
            # swallow exception to continue other sources and next iterations
            logger.exception("Ingest sweep failed", extra={"source": src, "error": str(exc)})


async def _run_loop() -> None:
    """Main daemon loop – initialise once then run forever."""

    # One-time initialisation
    init_metrics()
    init_sentry()

    logger.info(
        "Ingest daemon started",
        extra={
            "sources": SOURCES,
            "loop_interval": LOOP_INTERVAL,
            "limit": LIMIT,
            "parallel": PARALLEL,
            "batch_size": BATCH_SIZE,
            "min_score": MIN_SCORE,
            "dry_run": DRY_RUN,
        },
    )

    # On first boot, attempt to backfill up to 7 days of unprocessed rows
    since_dt = datetime.utcnow() - timedelta(days=7)

    while True:
        await _sweep_once(since_dt)
        # After the first loop, only consider rows created in the last 5 minutes.
        since_dt = datetime.utcnow() - timedelta(minutes=5)
        await asyncio.sleep(LOOP_INTERVAL)


def main() -> None:  # noqa: D401
    """Blocking entrypoint that can be used by `python -m data_ingest`."""

    try:
        asyncio.run(_run_loop())
    except KeyboardInterrupt:
        logger.info("Ingest daemon interrupted – shutting down") 