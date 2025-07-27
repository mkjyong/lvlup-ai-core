from __future__ import annotations

"""GeoIP 기반으로 클라이언트 국가/서버 정보를 추정하는 미들웨어.

- `request.state.geo_country`: ISO 3166-1 alpha-2 국가 코드 (예: "KR")
- `request.state.suggested_lol_region`: LoL 플랫폼 라우팅 코드(예: "KR", "JP1", "NA1")

기본 구현은 HTTP `X-Forwarded-For` 헤더의 IP → https://ipapi.co/json 호출.
프로덕션에서는 자체 GeoIP DB(MaxMind 등)로 교체 가능.
"""

import asyncio
import ipaddress
from typing import Callable, Awaitable, Optional

import httpx
from fastapi import Request, Response

# 최소 매핑 테이블 (필요 시 확장)
COUNTRY_TO_LOL_REGION: dict[str, str] = {
    "KR": "KR",
    "JP": "JP1",
    "US": "NA1",
    "CA": "NA1",
    "BR": "BR1",
    "TR": "TR1",
    "RU": "RU",
    "EU": "EUN1",  # generic fallbacks
    "GB": "EUW1",
    "DE": "EUW1",
    "FR": "EUW1",
}

# 공용 Geo IP API – 무응답 시 타임아웃 500ms
_GEOIP_ENDPOINT = "https://ipapi.co/{ip}/json/"


class GeoIPMiddleware:
    """GeoIP 국가 코드를 추정하여 request.state 에 저장한다."""

    def __init__(self, app, *, timeout: float = 0.5):
        self.app = app
        self.timeout = timeout

    async def __call__(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):  # type: ignore[override]
        client_ip = _get_client_ip(request)
        country_code: Optional[str] = None

        if client_ip:
            # 비동기 GeoIP 조회 – 타임아웃으로 실패 시 None 유지
            try:
                country_code = await _lookup_country(client_ip, self.timeout)
            except Exception:
                country_code = None

        if country_code:
            request.state.geo_country = country_code  # ISO Alpha-2
            request.state.suggested_lol_region = COUNTRY_TO_LOL_REGION.get(country_code, "NA1")
        return await call_next(request)


def _get_client_ip(request: Request) -> Optional[str]:
    """X-Forwarded-For 헤더 또는 client.host 값 반환."""

    xff = request.headers.get("X-Forwarded-For")
    if xff:
        # 여러 IP가 있을 경우 첫 번째가 클라이언트 IP
        ip = xff.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None
    try:
        if ip and ipaddress.ip_address(ip):
            return ip
    except ValueError:
        pass
    return None


async def _lookup_country(ip: str, timeout: float) -> Optional[str]:
    """ipapi.co 를 호출해 국가 코드(예: 'KR') 반환."""

    url = _GEOIP_ENDPOINT.format(ip=ip)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("country_code")
        except httpx.HTTPError:
            return None
    return None 