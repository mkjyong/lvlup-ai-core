from __future__ import annotations

"""Sentry SDK 초기화.

환경변수
----------
SENTRY_DSN: DSN 이 주어지면 자동 초기화한다.
ENVIRONMENT: (optional) production / staging / local 등
"""

import os

try:
    import sentry_sdk
except ImportError:  # pragma: no cover
    sentry_sdk = None  # type: ignore


def init_sentry() -> None:
    """Init Sentry SDK if DSN provided."""
    if sentry_sdk is None:
        return
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    env = os.getenv("ENVIRONMENT", "local")
    sentry_sdk.init(dsn=dsn, environment=env, traces_sample_rate=0.0) 