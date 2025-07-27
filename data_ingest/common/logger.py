"""공용 로거 설정 (structlog → 표준 logging fallback)."""

from __future__ import annotations

import logging
import os
import sys
from .slack import send_slack_message

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("data_ingest")

# -------------------------------
# Slack Error Handler (ERROR 이상)
# -------------------------------

if os.getenv("SLACK_WEBHOOK_ALERT_DATA_INGESTOR_ERR"):
    class _SlackErrHandler(logging.Handler):
        def emit(self, record):  # noqa: D401
            if record.levelno >= logging.ERROR:
                send_slack_message(f":rotating_light: *Ingestor Error* {record.getMessage()}")

    logger.addHandler(_SlackErrHandler()) 