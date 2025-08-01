"""/api/coach 라우터."""
from pydantic import BaseModel
from fastapi import APIRouter, status, Depends, Response, File, Form, UploadFile
from typing import List
from enum import Enum
from datetime import datetime, timedelta
from sqlmodel import select, func

from fastapi.responses import StreamingResponse
import json

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_SIZE = 10_000_000  # 10 MB

from app.services import usage as usage_service
from app.exceptions import AIError
from app.models.chat_session import ChatSession
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
    # run_and_stream을 사용해 전체 응답을 스트림으로 받아 문자열로 결합
    pipeline = RagPipeline()
    stream_iter = await pipeline.run_and_stream(
        question=payload.question,
        user_id=user.google_sub,
        plan_tier=user.plan_tier,
        game=payload.game,
        prompt_type=payload.prompt_type,
        include_history=True,
    )
    fragments: list[str] = []
    async for item in stream_iter:
        if item["event"] == "json":
            fragments.append(item["data"])
        elif item["event"] == "token":
            fragments.append(item["data"])
    answer = "".join(fragments)
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
    session_id: str | None = Form(None),
    text: str | None = Form(None),
    game: GameEnum | None = Form(None),
    prompt_type: str | None = Form(None),
    images: List[UploadFile] | None = File(None),
    user: User = Depends(get_current_user),
):
    """SSE 스트리밍: 1) json 이벤트, 2) token 이벤트 연속.

    기존 /chat/message 와 동일한 FormData 인터페이스를 제공하며
    내부적으로 RagPipeline 을 사용해 JSON 구조 + commentary 토큰을 생성한다.
    """

    if not text and not images:
        raise AIError("text 또는 image 중 하나는 반드시 포함해야 합니다.")

    async with get_session() as db:
        # ---------------------------------------------------------
        # 세션 로드 / 생성
        # ---------------------------------------------------------
        if session_id:
            sess = await db.get(ChatSession, session_id)
            if not sess or sess.user_google_sub != user.google_sub:
                raise AIError("세션을 찾을 수 없습니다.")
        else:
            import uuid, asyncio, google.generativeai as genai  # type: ignore

            DEFAULT_PROMPT = "You are an AI coach."
            gen_model = genai.GenerativeModel("gemini-2.5-flash")
            cache_resp = await asyncio.to_thread(gen_model.cache_context, DEFAULT_PROMPT)
            sess = ChatSession(
                id=str(uuid.uuid4()),
                user_google_sub=user.google_sub,
                model="gemini-2.5-flash",
                system_prompt=DEFAULT_PROMPT,
                context_cache_id=getattr(cache_resp, "cache_id", None),
            )
            db.add(sess)
            await db.commit()

        # ---------------------------------------------------------
        # 이미지 Part 변환
        # ---------------------------------------------------------
        parts: list[dict] | None = None
        if images:
            import google.generativeai as genai  # type: ignore

            parts = []
            for file in images:
                if file.content_type not in ALLOWED_TYPES:
                    raise AIError("지원하지 않는 이미지 형식")
                contents = await file.read()
                if len(contents) > MAX_SIZE:
                    raise AIError("이미지 크기가 10MB를 초과합니다.")
                parts.append(genai.Part.from_image(contents, mime_type=file.content_type))

        # ---------------------------------------------------------
        # RagPipeline 호출 (이미지 지원)
        # ---------------------------------------------------------
        pipeline = RagPipeline()
        stream_iter = await pipeline.run_and_stream(
            question=text or "[IMAGE]",
            user_id=user.google_sub,
            plan_tier=user.plan_tier,
            game=game,
            prompt_type=prompt_type,
            image_parts=parts,  # type: ignore[arg-type]
            session_row=sess,
        )

        # ---------------------------------------------------------
        # SSE 스트림 래핑 및 DB 기록
        # ---------------------------------------------------------
        chat_log = ChatMessage(
            user_google_sub=user.google_sub,
            session_id=sess.id,
            question=text or "[IMAGE]",
            answer="",
            game=game or "generic",
        )
        db.add(chat_log)
        await db.commit()
        await db.refresh(chat_log)

        async def event_generator():
            fragments: list[str] = []
            async for item in stream_iter:  # type: ignore[async-for-over-sync]
                yield f"event: {item['event']}\n" + f"data: {json.dumps(item['data'])}\n\n"
                if item["event"] == "token":
                    fragments.append(item["data"])
                elif item["event"] == "json":
                    # structured 결과를 ChatBubble 에서 렌더할 수 있게 저장
                    try:
                        chat_log.answer = item["data"]  # JSON 전문 저장
                    except Exception:
                        pass
            # 스트림 종료 후 전체 answer 저장
            full_answer = "".join(fragments)
            if full_answer:
                chat_log.answer = full_answer
            db.add(chat_log)
            # update session meta
            sess.last_used_at = datetime.utcnow()
            if not sess.title and text:
                sess.title = text[:20]
            await db.commit()
            yield "event: done\ndata: END\n\n"

    headers = {"X-Chat-Session": sess.id}
    return StreamingResponse(event_generator(), headers=headers, media_type="text/event-stream")


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