"""게임 자산 이미지 캐싱/조회 서비스."""

from __future__ import annotations

import asyncio
import httpx
from typing import Optional

from app.models.db import get_session
from app.models.game_asset import GameAsset
from sqlmodel import select


async def _fetch_lol_version() -> str:
    """게임 데이터 드래곤 최신 버전 문자열."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get("https://ddragon.leagueoflegends.com/api/versions.json")
        resp.raise_for_status()
        versions: list[str] = resp.json()
        return versions[0]


async def _lol_image_url(asset_type: str, key: str) -> Optional[str]:
    version = await _fetch_lol_version()
    if asset_type == "champion":
        return f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{key}.png"
    if asset_type == "item":
        return f"https://ddragon.leagueoflegends.com/cdn/{version}/img/item/{key}.png"
    return None


async def get_asset(game: str, asset_type: str, key: str) -> Optional[str]:
    """DB에서 찾거나 외부 API로 조회 후 캐시."""
    async with get_session() as session:
        stmt = select(GameAsset).where(
            (GameAsset.game == game) & (GameAsset.type == asset_type) & (GameAsset.key == key)
        )
        existing = (await session.exec(stmt)).one_or_none()
        if existing:
            return existing.image_url

    # 외부 API 조회 --------------------------------------------------
    if game == "lol":
        url = await _lol_image_url(asset_type, key)
    elif game == "pubg":
        url = await _pubg_image_url(asset_type, key)
    else:
        url = None  # TODO: PUBG 지원

    if url is None:
        return None

    # 캐시 저장 ------------------------------------------------------
    async with get_session() as session:
        ga = GameAsset(game=game, type=asset_type, key=key, image_url=url)
        session.add(ga)
        await session.commit()
    return url


# -----------------------------------------------------------------
# PUBG helpers
# -----------------------------------------------------------------


_PUBG_STATIC = "https://assets.pubg.com"


async def _pubg_image_url(asset_type: str, key: str) -> Optional[str]:
    """Return PUBG weapon/item image URL mapping. Limited to known asset types."""

    # Simple heuristic mapping; in real scenario fetch static asset manifest once and cache.
    if asset_type == "weapon":
        return f"{_PUBG_STATIC}/weapon/{key}.png"
    if asset_type == "item":
        return f"{_PUBG_STATIC}/item/{key}.png"
    if asset_type == "vehicle":
        return f"{_PUBG_STATIC}/vehicle/{key}.png"
    return None 