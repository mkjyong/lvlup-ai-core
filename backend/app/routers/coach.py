"""/api/coach 라우터."""
from pydantic import BaseModel
from fastapi import APIRouter, status, Depends, Response
from typing import List
from enum import Enum
from datetime import datetime, timedelta
from sqlmodel import select, func

from fastapi.responses import StreamingResponse
import json

from app.services import usage as usage_service
from app.orchestrators.rag import RagPipeline
from app.services import chat as chat_service
from app.deps import get_current_user

from app.models.plan_tier import PlanTier
from app.models.db import get_session
from sqlmodel import select
from app.models.user import User
from app.models.chat import ChatMessage

router = APIRouter(prefix="/api/coach", tags=["coach"])


class GameEnum(str, Enum):
    lol = "lol"
    pubg = "pubg"


class AskRequest(BaseModel):
    question: str
    game: GameEnum | None = None
    prompt_type: str | None = None


class AskResponse(BaseModel):
    answer: str


@router.post(
    "/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "AI answer with cost and remaining quota headers",
            "headers": {
                "X-Plan-Remaining": {
                    "description": "Remaining monthly request quota after this call",
                    "schema": {"type": "integer"},
                },
            },
        }
    },
)
async def ask_endpoint(payload: AskRequest, response: Response, user: User = Depends(get_current_user)):
    answer = await RagPipeline().run(
        question=payload.question,
        user_id=user.google_sub,
        plan_tier=user.plan_tier,
        game=payload.game,
        prompt_type=payload.prompt_type,
    )
    await chat_service.save_chat(user.google_sub, payload.question, answer, game=payload.game)

    # --- 헤더: 남은 호출 한도 ---------------------------
    category = "special" if (payload.game and payload.game.lower() in {"lol", "pubg"}) else "general"

    async with get_session() as session:
        stmt = (
            select(PlanTier)
            .where(PlanTier.name == user.plan_tier)
            .limit(1)
        )
        plan = (await session.exec(stmt)).one_or_none()
    if plan is None:
        remaining = 0
    else:
        monthly_limit = plan.monthly_request_limit if category == "general" else plan.special_monthly_request_limit or 0
        current_monthly = await usage_service.monthly_usage_count(user.google_sub)
        remaining = max(0, monthly_limit - current_monthly)

    response.headers["X-Plan-Remaining"] = str(remaining)

    return AskResponse(answer=answer)

# -------------------------------------------------------------
# NEW Streaming Endpoint
# -------------------------------------------------------------


@router.post("/ask/stream", status_code=status.HTTP_200_OK)
async def ask_stream_endpoint(
    payload: AskRequest, user: User = Depends(get_current_user)
):
    """SSE 스트리밍: 1) json 이벤트, 2) token 이벤트 연속."""

    async def event_generator():
        pipeline = RagPipeline()
        stream_iter = await pipeline.run_and_stream(
            question=payload.question,
            user_id=user.google_sub,
            plan_tier=user.plan_tier,
            game=payload.game,
            prompt_type=payload.prompt_type,
        )

        async for item in stream_iter:  # type: ignore[async-for-over-sync]
            # item: {event, data}
            yield f"event: {item['event']}\n" + f"data: {json.dumps(item['data'])}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# 기록 조회


class HistoryItem(BaseModel):
    question: str
    answer: str
    created_at: str


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


@router.get("/history", response_model=HistoryResponse)
async def history_endpoint(limit: int = 20, game: GameEnum | None = None, user: User = Depends(get_current_user)):
    items = await chat_service.list_chat_history(user.google_sub, limit, game)
    return HistoryResponse(items=[HistoryItem(question=i.question, answer=i.answer, created_at=i.created_at.isoformat()) for i in items])


class StatsResponse(BaseModel):
    active: int
    improved: int


@router.get("/stats", response_model=StatsResponse)
async def stats_endpoint():
    """현재 코칭 중·최근 24시간 실력 향상 사용자 통계 반환."""
    now = datetime.utcnow()
    ten_min_ago = now - timedelta(minutes=10)
    day_ago = now - timedelta(hours=24)

    async with get_session() as session:
        # active: 최근 10분 내 채팅 기록이 있는 distinct 사용자 수
        active_stmt = select(func.count(func.distinct(ChatMessage.user_google_sub))).where(
            ChatMessage.created_at >= ten_min_ago
        )
        active_result = await session.exec(active_stmt)
        active = active_result.scalar() or 0

        # improved: 최근 24시간 내 채팅 기록이 있는 distinct 사용자 수
        improved_stmt = select(func.count(func.distinct(ChatMessage.user_google_sub))).where(
            ChatMessage.created_at >= day_ago
        )
        improved_result = await session.exec(improved_stmt)
        improved = improved_result.scalar() or 0

    return StatsResponse(active=active, improved=improved) 