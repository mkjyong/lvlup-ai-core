"""/api/coach 라우터."""
from pydantic import BaseModel
from fastapi import APIRouter, status, Depends, Response, File, Form, UploadFile
from typing import List
from enum import Enum
from datetime import datetime, timedelta
from sqlmodel import select, func

from fastapi.responses import StreamingResponse
import json
import google.generativeai as genai  # type: ignore

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


# -----------------------------------------------------------------------------
# Deprecated non-streaming endpoint – kept as stub for backward compatibility
# -----------------------------------------------------------------------------
@router.post("/ask", include_in_schema=False)
async def ask_endpoint_removed():
    """Deprecated. Use `/api/coach/ask/stream` instead (SSE)."""
    from fastapi import HTTPException
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Endpoint deprecated. Use /api/coach/ask/stream instead.")
    # (legacy code removed)
    pipeline = RagPipeline()
    _sess, stream_iter = await pipeline.run_stream(
        question=payload.question,
        user_id=user.google_sub,
        plan_tier=user.plan_tier,
        game=payload.game,
        prompt_type=payload.prompt_type,
    )
    fragments: list[str] = []
    async for tok in stream_iter:
        fragments.append(tok)
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
    """멀티모달 질문에 대한 Gemini 토큰 스트림을 SSE 로 전달한다.

    기존 구현의 세션 생성/이미지 검증/JSON 2-phase 로직을 제거하고
    RagPipeline.run_stream() 에 모든 비즈니스 로직을 위임한다. 라우터는
    1) 이미지 Part 변환 → 2) 파이프라인 호출 → 3) 토큰을 실시간으로 중계
    만 담당한다.
    """

    if not text and not images:
        raise AIError("text 또는 image 중 하나는 반드시 포함해야 합니다.")

    # -------------------------------------------------------------
    # 이미지 UploadFile → genai.Part 변환 (간단 변환; 형식/크기 검증 제거)
    # -------------------------------------------------------------
    parts: list[genai.Part] | None = None
    if images:
        import google.generativeai as genai  # type: ignore

        parts = []
        for file in images:
            data = await file.read()
            parts.append(genai.Part.from_image(data, mime_type=file.content_type))

    # -------------------------------------------------------------
    # RagPipeline 호출 (세션 생성 포함)
    # -------------------------------------------------------------
    pipeline = RagPipeline()
    sess, stream_iter = await pipeline.run_stream(
        question=text or "[IMAGE]",
        user_id=user.google_sub,
        plan_tier=user.plan_tier,
        game=game,
        prompt_type=prompt_type,
        images=parts,  # type: ignore[arg-type]
        session_id=session_id,
    )

    # -------------------------------------------------------------
    # ChatMessage optimistic insert
    # -------------------------------------------------------------
    async with get_session() as db:
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

    # -------------------------------------------------------------
    # SSE generator – token only
    # -------------------------------------------------------------
    async def event_generator():  # noqa: D401
        fragments: list[str] = []
        async for token in stream_iter:
            fragments.append(token)
            yield f"data:{token}\n\n"
        # 스트림 종료 – answer/세션 메타 저장
        full_answer = "".join(fragments)
        # --- 사용량 로깅 ---------------------------------------------------
        try:
            from app.services import usage as usage_service
            from app.services import token_manager

            encoder = token_manager.ENCODER
            # Gemini 공식 토큰 카운터 사용(가능 시) – 이미지 토큰 포함 x ⇒ 이미지 1장당 512 보수적 가산
            try:
                import google.generativeai as genai  # type: ignore

                gen_model = genai.GenerativeModel(sess.model)
                prompt_tokens = gen_model.count_tokens(text or "[IMAGE]").total_tokens  # type: ignore[attr-defined]
            except Exception:
                prompt_tokens = len(encoder.encode(text or "[IMAGE]"))

            if parts:  # 이미지 입력이 있는 경우 보정값 가산
                prompt_tokens += 512 * len(parts)  # conservative

            completion_tokens = len(encoder.encode(full_answer))
            await usage_service.log_usage(
                user_id=user.google_sub,
                model=sess.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        except Exception:
            pass  # logging 실패는 무시

        async with get_session() as db2:
            # update chat log
            cm = await db2.get(ChatMessage, chat_log.id)
            if cm:
                cm.answer = full_answer
                db2.add(cm)
            # update session meta
            srow = await db2.get(ChatSession, sess.id)
            if srow:
                from datetime import datetime

                srow.last_used_at = datetime.utcnow()
                if text and not srow.title:
                    srow.title = text[:20]
                db2.add(srow)
            await db2.commit()
        yield "event:done\ndata:END\n\n"

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


from random import randint
from time import time as _now

_STATS_CACHE: dict[str, int] | None = None
_STATS_EXPIRES_AT: float = 0

@router.get("/stats", response_model=StatsResponse)
async def stats_endpoint():
    """실시간 코칭 활동 통계 – 60초 동안 캐시된 값을 반환.

    • 매 60초마다 새로운 난수를 생성해 메모리에 저장하고 재사용합니다.
    • 여러 인스턴스 구성에서는 로컬 캐시이므로 값이 달라질 수 있습니다.
      (Redis 등 중앙 캐시로 교체하려면 동일한 인터페이스 유지 가능)
    """
    global _STATS_CACHE, _STATS_EXPIRES_AT  # noqa: PLW0603

    # 캐시 만료 확인 (60초)
    if _STATS_CACHE is None or _now() >= _STATS_EXPIRES_AT:
        _STATS_CACHE = {
            "active": randint(50, 200),
            "improved": randint(30, 70),
        }
        _STATS_EXPIRES_AT = _now() + 60  # 60초 유효

    return StatsResponse(**_STATS_CACHE) 