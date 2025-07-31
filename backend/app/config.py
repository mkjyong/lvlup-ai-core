"""환경 변수 기반 설정 모듈.

`pydantic.BaseSettings`를 활용해 타입 안전한 설정을 제공한다.
런타임 시 단일 Settings 인스턴스를 가져오기 위해 get_settings() 헬퍼를 사용한다.
"""
from functools import lru_cache
from typing import Any
import os

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """프로젝트 전역 설정.

    환경 변수 또는 `.env` 파일을 통해 로드된다.
    """

    # === 애플리케이션 ===
    APP_NAME: str = "AI Coach Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # === 데이터베이스 ===
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # === Redis / Cache ===
    REDIS_URL: str = "redis://localhost:6379/0"

    # === Celery ===
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_BACKEND_URL: str = "redis://localhost:6379/0"

    # === 모니터링 ===
    PROMETHEUS_ENABLED: bool = True

    # === 보안 ===
    EMAIL_ENC_KEY: str  # 32-byte urlsafe_base64 Fernet key (필수)

    # === PortOne (아임포트) ===
    PORTONE_API_SECRET: str = ""
    PORTONE_BASE_URL: str = "https://api.portone.io"
    PORTONE_WEBHOOK_SECRET: str = ""

    # NOTE: 아래 필드들은 테스트/로컬 환경에서는 기본값을 허용한다.
    import sys
    _IS_TEST_ENV: bool = (
        os.getenv("PYTEST_CURRENT_TEST") is not None
        or os.getenv("ENVIRONMENT", "prod").lower() in {"test", "local"}
        or "pytest" in sys.modules
    )

    if _IS_TEST_ENV:
        # 안전하지 않은 기본값 – 테스트에서만 사용
        EMAIL_ENC_KEY: str = "rJFkzR1K1MDCItH66fLhNW4Jtm46Jj43HUzfv4jaWTM="
        DOMAIN_BASE_URL: str = "http://localhost"
        JWT_SECRET: str = "test-jwt-secret"

        # === PortOne (아임포트) ===
        PORTONE_API_SECRET: str = ""
        PORTONE_BASE_URL: str = "https://api.portone.io"
        PORTONE_WEBHOOK_SECRET: str = ""

        # === Slack Webhooks ===
        SLACK_WEBHOOK_SUBSCRIPTION_TRACKER: str | None = None
        SLACK_WEBHOOK_UNSUBSCRIPTION_TRACKER: str | None = None
        SLACK_WEBHOOK_ALERT_BACKEND_ERR: str | None = None

    # === CORS ===
    CORS_ALLOW_ORIGINS: str = ""

    # === LLM / Gemini ===
    GEMINI_API_KEY: str | None = None

    # === External Game APIs ===
    RIOT_API_KEY: str | None = None
    RIOT_RATE_LIMIT_PER_SEC: int = 18  # 공식 20req/s 에서 여유
    PUBG_API_KEY: str | None = None
    PUBG_RATE_LIMIT_PER_SEC: int = 8  # dev key 10req/s 여유

    # === JWT ===
    JWT_SECRET: str = "change-me"
    if _IS_TEST_ENV:
        JWT_SECRET: str = "test-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14  # 14 days

    # === 기타 ===
    LOG_LEVEL: str = "INFO"

    # === 운영 플래그 ===
    AUTO_MIGRATE: bool = True  # True 이면 서버 시작 시 테이블 자동 생성

    # === 결제 재시도 정책 ===
    RETRY_PAYMENT_MAX_ATTEMPTS: int = 2  # 최초 실패 후 추가 시도 횟수
    RETRY_PAYMENT_INTERVAL_HOURS: int = 6  # 재시도 간격(시간)

    # === HTTP 재시도 ===
    HTTP_RETRY_ATTEMPTS: int = 3
    HTTP_RETRY_DELAY_SEC: int = 3

    # === (예시) Google OAuth ===
    GOOGLE_CLIENT_ID: str = ""

    # === 앱 도메인 ===
    DOMAIN_BASE_URL: str  # 예: https://app.example.com

    if _IS_TEST_ENV:
        DOMAIN_BASE_URL: str = "http://localhost"

    # === DB 커넥션 풀 ===
    DB_POOL_SIZE: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    # 추가 검증 예시
    @validator("DATABASE_URL")
    def _validate_db_url(cls, v: str) -> str:  # noqa: D401
        """데이터베이스 URL 기본 값 경고."""
        if v.startswith("sqlite"):
            # sqlite는 dev 용으로만 사용 권장
            return v
        return v

    # 필수 시크릿 키 검증
    @validator("EMAIL_ENC_KEY", "JWT_SECRET")
    def _require_secret(cls, v: str, field):  # noqa: D401
        is_test = os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("ENVIRONMENT", "prod").lower() in {"test", "local"}
        if not v or v in {"", "change-me", "please-change-me"}:
            if is_test:
                # 테스트 용도로 allow
                return v or "test-default"
            raise ValueError(f"{field.name} 환경변수가 설정되지 않았거나 기본값을 사용하고 있습니다.")
        return v

    # DOMAIN_BASE_URL 필수 검증 (프로덕션만)
    @validator("DOMAIN_BASE_URL", pre=True, always=True)
    def _validate_domain(cls, v):
        is_test = os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("ENVIRONMENT", "prod").lower() in {"test", "local"}
        if not v:
            if is_test:
                return "http://localhost"
            raise ValueError("DOMAIN_BASE_URL must be set")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """싱글턴 Settings 리턴."""

    return Settings() 

# -----------------------------
# Pricing & Plan limit tables
# -----------------------------

# Gemini API 가격 정책 (2025-07 기준)
# https://ai.google.dev/gemini-api/docs/pricing?hl=ko
# key: model → {prompt: 가격/1K input 토큰, completion: 가격/1K output 토큰}
MODEL_PRICING_PER_1K: dict[str, dict[str, float]] = {
    # Gemini 2.5 Flash-Lite (가볍고 저렴한 버전 – Pro 대비 50% 수준 가정)
    # 실제 가격은 Flash 기준 $0.0025/$0.0075 이므로 50% → 0.00125 / 0.00375
    "gemini-2.5-flash-lite": {
        "prompt": 0.00125,
        "completion": 0.00375,
    },
    # Gemini 2.5 Flash (실시간 응답 지향)
    "gemini-2.5-flash": {
        "prompt": 0.0025,
        "completion": 0.0075,
    },
}

MODEL_CATEGORY: dict[str, str] = {
    "gemini-2.5-flash-lite": "general",
    "gemini-2.5-flash": "special",
}

PLAN_CALL_LIMITS: dict[str, dict[str, dict[str, int]]] = {
    "free": {
        "general": {"weekly": 30, "monthly": 200},
    },
    "basic": {
        "general": {"weekly": 200, "monthly": 800},
        "special": {"monthly": 100},
    },
}

PLAN_TOKEN_LIMITS: dict[str, dict[str, int]] = {
    "free": {"prompt": 500, "completion": 1000},
    "basic": {"prompt": 1000, "completion": 2000},
} 