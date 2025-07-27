from __future__ import annotations

"""게임 성과(Stats) API 라우터."""

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user, get_session
from app.services.performance import get_overview, compute_percentile, get_trend

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
async def stats_overview(game: str, period: str = "weekly", user=Depends(get_current_user), session=Depends(get_session)):
    """주간/월간 KPI & 퍼센타일 요약."""

    if period not in {"weekly", "monthly"}:
        raise HTTPException(status_code=400, detail="invalid period")
    metrics = await get_overview(session, user.google_sub, game, period)
    percentile = await compute_percentile(session, game, period, metrics)
    return {"game": game, "period": period, "metrics": metrics, "percentile": percentile}


@router.get("/trend")
async def stats_trend(
    game: str,
    metric: str,
    weeks: int = 8,
    user=Depends(get_current_user),
    session=Depends(get_session),
):
    """최근 N주 weekly metric 추세."""

    if weeks <= 0 or weeks > 26:
        raise HTTPException(status_code=400, detail="weeks must be 1-26")
    trend = await get_trend(session, user.google_sub, game, metric, weeks)
    return {"game": game, "metric": metric, "trend": trend} 