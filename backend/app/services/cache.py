from functools import lru_cache

import redis.asyncio as redis

from app.config import get_settings


@lru_cache(maxsize=1)
def get_redis() -> "redis.Redis":  # type: ignore[return-type]
    """전역 asyncio Redis 클라이언트 싱글턴을 반환한다."""

    settings = get_settings()
    return redis.from_url(settings.REDIS_URL, decode_responses=True) 