"""환경 변수 기반 설정 모듈.

`pydantic.BaseSettings`를 활용해 타입 안전한 설정을 제공한다.
런타임 시 단일 Settings 인스턴스를 가져오기 위해 get_settings() 헬퍼를 사용한다.
"""
from functools import lru_cache
from typing import Any

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
    # === Slack Webhooks ===
    SLACK_WEBHOOK_SUBSCRIPTION_TRACKER: str | None = None
    SLACK_WEBHOOK_UNSUBSCRIPTION_TRACKER: str | None = None
    SLACK_WEBHOOK_ALERT_BACKEND_ERR: str | None = None

    # === CORS ===
    CORS_ALLOW_ORIGINS: str = ""

    # === LLM/OpenAI ===
    OPENAI_API_KEY: str | None = None

    # --- OpenAI File Search IDs (comma-separated) ---
    OPENAI_FILE_IDS_GENERIC: str | None = ""  # e.g., "file-abc,file-def"
    OPENAI_FILE_IDS_LOL: str | None = ""
    OPENAI_FILE_IDS_PUBG: str | None = ""

    # === External Game APIs ===
    RIOT_API_KEY: str | None = None
    RIOT_RATE_LIMIT_PER_SEC: int = 18  # 공식 20req/s 에서 여유
    PUBG_API_KEY: str | None = None
    PUBG_RATE_LIMIT_PER_SEC: int = 8  # dev key 10req/s 여유

    # === JWT ===
    JWT_SECRET: str = "change-me"
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
        if not v or v in {"", "change-me", "please-change-me"}:
            raise ValueError(f"{field.name} 환경변수가 설정되지 않았거나 기본값을 사용하고 있습니다.")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """싱글턴 Settings 리턴."""

    return Settings() 

# -----------------------------
# Pricing & Plan limit tables
# -----------------------------

MODEL_PRICING_PER_1K: dict[str, float] = {
    "gpt-4o-mini": 0.00075,
    "o4-mini": 0.00550,
}

MODEL_CATEGORY: dict[str, str] = {
    "gpt-4o-mini": "general",
    "o4-mini": "special",
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