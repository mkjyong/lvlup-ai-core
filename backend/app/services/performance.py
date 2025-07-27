from __future__ import annotations

"""게임 성과 집계 및 캐싱 서비스."""

from datetime import datetime, timedelta, date
from typing import Dict, Any

from sqlalchemy import select
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.match_cache import MatchCache
from app.models.performance_stats import PerformanceStats
from app.models.game_account import GameAccount
from app.services.external import lol as lol_api, pubg as pubg_api

CACHE_TTL_HOURS = 6


async def ensure_stats_cached(session: AsyncSession, user_sub: str, game: str) -> Dict[str, Any]:
    """TTL 내 캐시가 있으면 반환, 없으면 외부 API fetch 후 저장."""

    now = datetime.utcnow()
    ttl_cutoff = now - timedelta(hours=CACHE_TTL_HOURS)

    result = await session.exec(
        select(MatchCache).where(
            MatchCache.user_google_sub == user_sub, MatchCache.game == game, MatchCache.fetched_at >= ttl_cutoff
        )
    )
    cache = result.first()
    if cache:
        return cache.raw

    # fetch via connector
    account = await session.exec(
        select(GameAccount).where(GameAccount.user_google_sub == user_sub, GameAccount.game == game)
    )
    account_row = account.first()
    if not account_row:
        raise ValueError("Game account not registered")

    if game == "lol":
        raw_stats = await lol_api.fetch_latest_stats(account_row.account_id, account_row.region or "KR")
    elif game == "pubg":
        raw_stats = await pubg_api.fetch_latest_stats(account_row.account_id)
    else:
        raise ValueError("Unsupported game")

    cache = MatchCache(user_google_sub=user_sub, game=game, raw=raw_stats, fetched_at=now, ttl=now + timedelta(hours=CACHE_TTL_HOURS))
    session.add(cache)
    await session.commit()
    return raw_stats


async def aggregate_stats(session: AsyncSession, user_sub: str, game: str, raw_stats: Dict[str, Any]) -> None:
    """간단히 raw_stats를 저장하여 weekly/monthly 엔트리에 upsert한다."""

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    first_day_month = today.replace(day=1)

    for period, start_date in (("weekly", monday), ("monthly", first_day_month)):
        end_date = start_date + (timedelta(days=7) if period == "weekly" else timedelta(days=31))
        result = await session.exec(
            select(PerformanceStats).where(
                PerformanceStats.user_google_sub == user_sub,
                PerformanceStats.game == game,
                PerformanceStats.period == period,
                PerformanceStats.period_start == start_date,
            )
        )
        row = result.first()
        if row:
            row.metrics = raw_stats
            row.period_end = end_date
        else:
            row = PerformanceStats(
                user_google_sub=user_sub,
                game=game,
                period=period,
                period_start=start_date,
                period_end=end_date,
                metrics=raw_stats,
            )
            session.add(row)
    await session.commit()


async def get_overview(session: AsyncSession, user_sub: str, game: str, period: str) -> Dict[str, Any]:
    """PerformanceStats 조회 후 반환."""

    result = await session.exec(
        select(PerformanceStats)
        .where(
            PerformanceStats.user_google_sub == user_sub,
            PerformanceStats.game == game,
            PerformanceStats.period == period,
        )
        .order_by(PerformanceStats.period_start.desc())
    )
    row = result.first()
    if row:
        return row.metrics
    # fallback: ensure cache and aggregate
    raw_stats = await ensure_stats_cached(session, user_sub, game)
    await aggregate_stats(session, user_sub, game, raw_stats)
    return raw_stats 

# -----------------------------
# Percentile & Trend Utilities
# -----------------------------


async def compute_percentile(
    session: AsyncSession, game: str, period: str, user_metrics: Dict[str, Any]
) -> Dict[str, float]:
    """주어진 metrics 에 대해 전체 분포 대비 퍼센타일(0-100) 계산.

    매우 간단한 구현: PerformanceStats 테이블에서 동일 게임/기간의 값들과 비교.
    """

    percentiles: Dict[str, float] = {}
    if not user_metrics:
        return percentiles

    result = await session.exec(
        select(PerformanceStats.metrics).where(
            PerformanceStats.game == game,
            PerformanceStats.period == period,
        )
    )
    rows = result.all()
    if not rows:
        return {k: 0.0 for k in user_metrics}

    # build lists per metric
    metrics_dict: Dict[str, list[float]] = {k: [] for k in user_metrics}
    for (metrics_json,) in rows:  # metrics column only
        for k in metrics_dict:
            v = metrics_json.get(k)
            if isinstance(v, (int, float)):
                metrics_dict[k].append(float(v))

    for k, vals in metrics_dict.items():
        if not vals:
            percentiles[k] = 0.0
            continue
        vals.sort()
        user_val = float(user_metrics.get(k, 0))
        # number of values <= user
        le_count = len([v for v in vals if v <= user_val])
        percentiles[k] = round(le_count / len(vals) * 100, 1)

    return percentiles


async def get_trend(
    session: AsyncSession, user_sub: str, game: str, metric: str, weeks: int = 8
) -> list[tuple[str, float]]:
    """최근 N주 weekly performance metric 추세 (ISO date string, value) 리스트."""

    result = await session.exec(
        select(PerformanceStats)
        .where(
            PerformanceStats.user_google_sub == user_sub,
            PerformanceStats.game == game,
            PerformanceStats.period == "weekly",
        )
        .order_by(PerformanceStats.period_start.desc())
        .limit(weeks)
    )
    rows = result.all()
    trend = []
    for r in reversed(rows):  # oldest first
        val = r.metrics.get(metric) if isinstance(r.metrics, dict) else None
        if isinstance(val, (int, float)):
            trend.append((r.period_start.isoformat(), float(val)))
    return trend 