from __future__ import annotations

"""PUBG API 커넥터 – 데모용 임시 구현."""

import asyncio
import os
import random
from typing import Any, Dict

import httpx
from aiolimiter import AsyncLimiter

from app.config import get_settings

settings = get_settings()

PUBG_API_KEY = settings.PUBG_API_KEY
_limiter = AsyncLimiter(settings.PUBG_RATE_LIMIT_PER_SEC, time_period=1.0)

API_BASE = "https://api.pubg.com"


async def _request(url: str) -> Any:
    headers = {
        "Authorization": f"Bearer {PUBG_API_KEY}",
        "Accept": "application/vnd.api+json",
    } if PUBG_API_KEY else {}
    async with _limiter:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()


async def fetch_latest_stats(account_id: str, platform: str = "steam") -> Dict[str, Any]:  # noqa: D401
    """Fetch latest season stats or return stub if no key."""

    if not PUBG_API_KEY:
        return {
            "winRate": round(random.uniform(5, 20), 1),
            "kda": round(random.uniform(1.0, 4.0), 2),
            "avgDamage": round(random.uniform(200, 700), 1),
            "top10Ratio": round(random.uniform(30, 60), 1),
        }

    # 1) Get current season ID
    seasons_url = f"{API_BASE}/shards/{platform}/seasons"
    seasons_data = await _request(seasons_url)
    current_season = next((s["id"] for s in seasons_data["data"] if s["attributes"]["isCurrentSeason"]), None)
    if not current_season:
        raise ValueError("Season not found")

    # 2) player season stats
    stats_url = f"{API_BASE}/shards/{platform}/players/{account_id}/seasons/{current_season}"
    stats_data = await _request(stats_url)

    solo_stats = stats_data["data"]["attributes"]["gameModeStats"].get("solo") or {}
    wins = solo_stats.get("wins", 0)
    rounds = solo_stats.get("roundsPlayed", 1)
    win_rate = wins / rounds * 100
    kda = solo_stats.get("kills", 0) / max(1, solo_stats.get("losses", 1))
    avg_damage = solo_stats.get("damageDealt", 0) / rounds
    top10_ratio = solo_stats.get("top10s", 0) / rounds * 100

    return {
        "winRate": round(win_rate, 1),
        "kda": round(kda, 2),
        "avgDamage": round(avg_damage, 1),
        "top10Ratio": round(top10_ratio, 1),
    } 