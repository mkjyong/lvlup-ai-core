"""구조화 로깅 설정.

`structlog`를 사용해 JSON 형태 로깅을 제공한다.
"""
import logging
import sys

import structlog

from app.config import get_settings
from app.services.security import mask_pii_processor


def _get_log_level() -> int:
    settings = get_settings()
    return getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)


def init_logging(force: bool = False) -> None:  # noqa: D401
    """structlog 설정 & 글로벌 로거 초기화.

    FastAPI 앱 팩토리에서 가장 먼저 호출되어야 한다.
    """

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors = [
        timestamper,
        structlog.contextvars.merge_contextvars,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        mask_pii_processor,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(_get_log_level()),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # 표준 로깅은 structlog가 이미 JSON 문자열을 출력하므로 그대로 전달
    logging.basicConfig(level=_get_log_level(), format="%(message)s", stream=sys.stdout)

    # -----------------------------------------
    # Noise suppression – show only access INFO
    # -----------------------------------------
    # httpx / httpcore 디버그 트레이스, uvicorn.error 등을 WARNING 이상으로 올려
    # 접근 로그(uvicorn.access)만 INFO 레벨로 남긴다.
    noisy_libs = (
        "httpx",
        "httpcore",
        "uvicorn.error",
        "python_multipart.multipart",
        "google.genai",
    )
    for name in noisy_libs:
        logging.getLogger(name).setLevel(logging.WARNING)

    # uvicorn.access 는 INFO 그대로 유지
    logging.getLogger("uvicorn.access").setLevel(logging.INFO) 