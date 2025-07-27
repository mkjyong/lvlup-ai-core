from __future__ import annotations

"""Riot Games API 연결.
현재는 데모용: 주어진 소환사명+region으로 최근 매치 20개를 조회하여 KPI 계산.
실제 구현 시 Riot API Key가 필요하고 RateLimit 관리 필요.
"""

import asyncio
import os
import random
from typing import Any, Dict, List

import httpx
from aiolimiter import AsyncLimiter

from app.config import get_settings

settings = get_settings()

# If no API key, use stub mode
RIOT_API_KEY = settings.RIOT_API_KEY

# rate limiter per host (shared across workers in-process only)
_limiter = AsyncLimiter(settings.RIOT_RATE_LIMIT_PER_SEC, time_period=1.0)

BASE_URL_SUMMONER = "https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{name}"
BASE_URL_MATCH_IDS = "https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=20"
BASE_URL_MATCH_DETAIL = "https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"

# region -> platform mapping for Summoner-V4
REGION_TO_PLATFORM = {
    "KR": "kr",
    "JP1": "jp1",
    "NA1": "na1",
    "EUW1": "euw1",
    "EUN1": "eun1",
    "BR1": "br1",
    "TR1": "tr1",
    "RU": "ru",
}


async def _request(url: str) -> Any:
    """Rate-limited Riot API request."""

    headers = {"X-Riot-Token": RIOT_API_KEY} if RIOT_API_KEY else {}
    async with _limiter:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()


async def _compute_kpis(matches: List[dict], puuid: str) -> Dict[str, Any]:
    wins = kills = deaths = assists = cs = kp_total = 0
    for m in matches:
        participants = m["info"]["participants"]
        p = next((x for x in participants if x["puuid"] == puuid), None)
        if not p:
            continue
        wins += 1 if p["win"] else 0
        kills += p["kills"]
        deaths += p["deaths"] or 1
        assists += p["assists"]
        cs += p["totalMinionsKilled"] + p.get("neutralMinionsKilled", 0)
        kp_total += p["killParticipation"] if "killParticipation" in p else 0

    games = len(matches) or 1
    win_rate = wins / games * 100
    kda = (kills + assists) / deaths
    cs_per_min = cs / (games * 30)  # approx 30min
    kp = kp_total / games if kp_total else 0

    return {
        "winRate": round(win_rate, 1),
        "kda": round(kda, 2),
        "csPerMin": round(cs_per_min, 2),
        "killParticipation": round(kp * 100, 1),
    }


async def fetch_latest_stats(account_id: str, region: str) -> Dict[str, Any]:  # noqa: D401
    """Fetch real stats or stub if API key missing."""

    if not RIOT_API_KEY:
        # stub
        return {
            "winRate": round(random.uniform(45, 60), 1),
            "kda": round(random.uniform(2, 5), 2),
            "csPerMin": round(random.uniform(6, 9), 2),
            "killParticipation": round(random.uniform(40, 70), 1),
        }

    platform = REGION_TO_PLATFORM.get(region.upper(), "kr")
    # 1) summoner -> puuid
    summoner_url = BASE_URL_SUMMONER.format(platform=platform, name=httpx.utils.quote(account_id))
    summoner = await _request(summoner_url)
    puuid = summoner["puuid"]

    # 2) recent match ids
    match_ids_url = BASE_URL_MATCH_IDS.format(region=region.lower(), puuid=puuid)
    match_ids = await _request(match_ids_url)

    # 3) fetch match details concurrently but with rate limit
    async def fetch_detail(mid):
        url = BASE_URL_MATCH_DETAIL.format(region=region.lower(), match_id=mid)
        return await _request(url)

    matches = await asyncio.gather(*[fetch_detail(mid) for mid in match_ids[:10]])  # limit 10

    return await _compute_kpis(matches, puuid) 