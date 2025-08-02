"""Usage logging & quota helpers."""
from datetime import datetime, timedelta

from sqlmodel import select, func

# Redis helper
from app.services.cache import get_redis

from app.models.db import get_session
from app.models.usage import LLMUsage
from app.config import (
    MODEL_PRICING_PER_1K,
    MODEL_CATEGORY,
)
from app.models.plan_tier import PlanTier
from app.models.user_plan import UserPlan
from app.models.user import User


async def monthly_usage_count(user_id: str) -> int:
    """월간 사용량을 Redis 캐시 → DB 순으로 조회."""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    r = get_redis()
    key = f"usage:{user_id}:month:{month_start.strftime('%Y%m')}"

    try:
        cached = await r.get(key)
        if cached is not None:
            return int(cached)
    except Exception:
        cached = None  # Redis 장애 시 무시

    # Fallback to DB count
    async with get_session() as session:
        stmt = select(func.count()).where(
            LLMUsage.user_google_sub == user_id, LLMUsage.created_at >= month_start
        )
        result = await session.exec(stmt)
        count = result.one_or_none() or 0

    # Populate cache (TTL 32일)
    try:
        await r.set(key, count, ex=60 * 60 * 24 * 32)
    except Exception:
        pass

    return count

async def _get_active_plan(user_id: str) -> PlanTier:
    """현재 활성화된 PlanTier 반환 (없으면 free)."""
    async with get_session() as session:
        # Check UserPlan first
        stmt = (
            select(PlanTier)
            .join(UserPlan, PlanTier.id == UserPlan.plan_tier_id)
            .where(UserPlan.user_google_sub == user_id)
            .order_by(UserPlan.started_at.desc())
            .limit(1)
        )
        result = await session.exec(stmt)
        plan = result.one_or_none()
        if plan:
            return plan

        # Fallback: User.plan_tier string
        user_stmt = select(User.plan_tier).where(User.google_sub == user_id)
        r = await session.exec(user_stmt)
        tier_name = r.one_or_none() or "free"
        plan_stmt = select(PlanTier).where(PlanTier.name == tier_name)
        rp = await session.exec(plan_stmt)
        plan = rp.one_or_none()
        if plan:
            return plan

        # ultimate fallback: first free row
        pf = await session.exec(select(PlanTier).where(PlanTier.name == "free"))
        return pf.one()


async def get_active_plan(user_id: str) -> PlanTier:
    """Public wrapper to fetch active PlanTier."""
    return await _get_active_plan(user_id)

async def has_quota(user_id: str, _, model: str | None = None) -> bool:  # plan_tier param kept for compatibility
    plan = await _get_active_plan(user_id)

    monthly = await monthly_usage_count(user_id)

    if model:
        category = MODEL_CATEGORY.get(model, "general")
    else:
        category = "general"

    # monthly
    monthly_limit = (
        plan.monthly_request_limit
        if category == "general"
        else plan.special_monthly_request_limit
    )
    if monthly_limit and monthly >= monthly_limit:
        return False

    return True


async def log_usage(user_id: str, model: str, prompt_tokens: int, completion_tokens: int, cost_usd: float | None = None) -> None:
    """LLM 호출 사용량 기록 및 비용 산출."""

    if cost_usd is None:
        pricing = MODEL_PRICING_PER_1K.get(model) or {"prompt": 0.0, "completion": 0.0}
        cost_usd = (prompt_tokens / 1000) * pricing.get("prompt", 0) + (
            completion_tokens / 1000
        ) * pricing.get("completion", 0)

    usage = LLMUsage(
        user_google_sub=user_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        cost_usd=cost_usd,
    )
    async with get_session() as session:
        session.add(usage)
        await session.commit()

    # --- Redis 카운터 갱신 ----------------------------------------
    try:
        now = datetime.utcnow()
        week_key = f"usage:{user_id}:week:{(now - timedelta(days=now.weekday())).strftime('%Y%m%d')}"
        month_key = f"usage:{user_id}:month:{now.strftime('%Y%m')}"

        r = get_redis()
        async with r.pipeline(transaction=False) as pipe:
            pipe.incr(week_key)
            pipe.expire(week_key, 60 * 60 * 24 * 8)
            pipe.incr(month_key)
            pipe.expire(month_key, 60 * 60 * 24 * 32)
            await pipe.execute()
    except Exception:
        # Redis 장애 시 무시하고 DB 레코드만 유지
        pass 