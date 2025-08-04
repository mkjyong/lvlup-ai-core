from functools import lru_cache
import ssl

import redis.asyncio as redis

from app.config import get_settings


@lru_cache(maxsize=1)
def get_redis() -> "redis.Redis":  # type: ignore[return-type]
    """전역 asyncio Redis 클라이언트 싱글턴.

    rediss:// 스킴이 감지되면 안전한 TLS 연결을 위해
    ssl_cert_reqs=ssl.CERT_REQUIRED 를 자동으로 설정한다.
    """
    settings = get_settings()
    url = settings.REDIS_URL

    kwargs = {"decode_responses": True}
    if url.startswith("rediss://"):
        # 인증서 검증이 없는 불완전 TLS 경고 방지
        kwargs["ssl_cert_reqs"] = ssl.CERT_REQUIRED

    return redis.from_url(url, **kwargs) 