"""/admin 라우터 (Stub)."""
from fastapi import APIRouter, status

from sqlmodel import select, func
from pydantic import BaseModel

from app.services.prompt import PromptType
from app.models.db import get_session
from app.models.usage import LLMUsage
from app.models.payment import PaymentLog

router = APIRouter(prefix="/admin", tags=["admin"])


class StatsResponse(BaseModel):
    month: str
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost_usd: float
    total_revenue_usd: float
    paying_users: int


@router.get("/stats", response_model=StatsResponse, status_code=status.HTTP_200_OK)
async def stats():
    """월간 비용·매출·토큰 통계."""
    from datetime import datetime

    start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async with get_session() as session:
        # Usage aggregation
        usage_stmt = select(
            func.coalesce(func.sum(LLMUsage.prompt_tokens), 0),
            func.coalesce(func.sum(LLMUsage.completion_tokens), 0),
            func.coalesce(func.sum(LLMUsage.cost_usd), 0.0),
        ).where(LLMUsage.created_at >= start)
        prompt_tokens, completion_tokens, cost_usd = (await session.exec(usage_stmt)).one()

        # Revenue aggregation (assumes amount stored in raw_event)
        rev_stmt = select(
            func.coalesce(func.sum(PaymentLog.amount_usd), 0.0), func.count()
        ).where(PaymentLog.created_at >= start)
        revenue_usd, paying_users = (await session.exec(rev_stmt)).one()

    return StatsResponse(
        month=start.strftime("%Y-%m"),
        total_prompt_tokens=prompt_tokens,
        total_completion_tokens=completion_tokens,
        total_cost_usd=round(cost_usd, 4),
        total_revenue_usd=round(float(revenue_usd), 2),
        paying_users=paying_users,
    )


@router.get("/prompts", summary="시스템 프롬프트 목록", status_code=status.HTTP_200_OK)
async def list_prompts():
    return {"prompts": [p.name for p in PromptType]} 