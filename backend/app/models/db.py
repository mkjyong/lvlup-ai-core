"""데이터베이스 엔진 & 세션 팩토리."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings
import app.models  # noqa: F401  # Ensure models are imported before create_all

from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

_settings = get_settings()

# ---------------------------------------------------------------------------
# Asyncpg sslmode compatibility
# ---------------------------------------------------------------------------

db_url = _settings.DATABASE_URL

# asyncpg >=0.28.0 는 URL query 의 sslmode 파라미터를 지원하지 않는다.
# Supabase 등에서 복사한 DSN 에는 `?sslmode=require` 가 포함되어 오류가 발생하므로 제거한다.
if db_url.startswith("postgresql+asyncpg") and "sslmode=" in db_url:
    from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

    parsed = urlparse(db_url)
    query_params = [(k, v) for k, v in parse_qsl(parsed.query) if k not in {"sslmode", "ssl"}]
    parsed = parsed._replace(query=urlencode(query_params))
    db_url = urlunparse(parsed)

# 동기 엔진(마이그레이션 등에서 사용 가능)
sync_engine = create_engine(_settings.DATABASE_URL, echo=_settings.DEBUG, pool_pre_ping=True, future=True)

# ---------------------------------------------------------------------------
# Async 엔진 – 전역 재사용(커넥션 풀 제한 적용)
# ---------------------------------------------------------------------------

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
import ssl as _ssl

_ssl_ctx = _ssl.create_default_context()

async_engine: AsyncEngine = create_async_engine(
    db_url,
    echo=_settings.DEBUG,
    future=True,
    pool_size=_settings.DB_POOL_SIZE,
    max_overflow=0,
    connect_args={"ssl": _ssl_ctx},
)

# 세션 팩토리 전역 재사용
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:  # noqa: D401
    """애플리케이션 시작 시 호출하여 테이블 생성."""

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성용 비동기 세션 Yielder."""

    async with AsyncSessionLocal() as session:  # type: ignore[assignment]
        try:
            yield session
        finally:
            await session.close() 