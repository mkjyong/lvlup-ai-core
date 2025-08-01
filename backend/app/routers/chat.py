"""Chat router – session CRUD, multimodal messaging, SSE stream."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

import google.generativeai as genai  # type: ignore
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlmodel import select

from app.deps import get_current_user
from app.exceptions import AIError
from app.models.chat import ChatMessage
from app.models.chat_session import ChatSession
from app.models.db import get_session
from app.models.user import User
from app.services.llm_session_pool import get_chat

router = APIRouter(prefix="/chat", tags=["chat"])
DEFAULT_PROMPT = "You are an AI coach."
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_SIZE = 10_000_000  # 10 MB

# ---------------------------------------------------------------------------
# Session list
# ---------------------------------------------------------------------------


@router.get("/sessions")
async def list_sessions(user: User = Depends(get_current_user)):
    async with get_session() as s:
        stmt = (
            select(ChatSession.id, ChatSession.title, ChatSession.started_at, ChatSession.last_used_at)
            .where(ChatSession.user_google_sub == user.google_sub)
            .order_by(ChatSession.last_used_at.desc())
        )
        rows = (await s.exec(stmt)).all()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Messages list
# ---------------------------------------------------------------------------


@router.get("/messages")
async def list_messages(
    session_id: str,
    limit: int = 100,
    user: User = Depends(get_current_user),
):
    async with get_session() as s:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id, ChatMessage.user_google_sub == user.google_sub)
            .order_by(ChatMessage.created_at)
            .limit(limit)
        )
        rows = (await s.exec(stmt)).all()
        result = []
        for row in rows:
            result.append({"role": "user", "text": row.question, "created_at": row.created_at})
            if row.answer:
                result.append({"role": "assistant", "text": row.answer, "created_at": row.created_at})
        return result


# ---------------------------------------------------------------------------
# Send message (multimodal) + SSE
# ---------------------------------------------------------------------------


# @router.post("/message", status_code=status.HTTP_200_OK)
# Legacy endpoint disabled. Calls should use /api/coach/ask/stream
async def post_message(
    session_id: str | None = Form(None),
    text: str | None = Form(None),
    images: List[UploadFile] | None = File(None),
    user: User = Depends(get_current_user),
):
    if not text and not images:
        raise AIError("text 또는 image 중 하나는 반드시 포함해야 합니다.")

    async with get_session() as db:
        # session load / create ------------------------------------------------
        if session_id:
            sess = await db.get(ChatSession, session_id)
            if not sess or sess.user_google_sub != user.google_sub:
                raise AIError("세션을 찾을 수 없습니다.")
        else:
            import asyncio
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

        chat_obj = get_chat(sess)

        # build parts ---------------------------------------------------------
        parts: list[genai.Part] = []
        if images:
            for file in images:
                if file.content_type not in ALLOWED_TYPES:
                    raise AIError("지원하지 않는 이미지 형식")
                contents = await file.read()
                if len(contents) > MAX_SIZE:
                    raise AIError("이미지 크기가 10MB를 초과합니다.")
                parts.append(genai.Part.from_image(contents, mime_type=file.content_type))
        if text:
            parts.append(genai.Part(text=text))

        # optimistic log ------------------------------------------------------
        chat_log = ChatMessage(
            user_google_sub=user.google_sub,
            session_id=sess.id,
            question=text or "[IMAGE]",
            answer="",
        )
        db.add(chat_log)
        await db.commit()
        await db.refresh(chat_log)

        async def sse_generator():
            fragments: list[str] = []
            async for chunk in chat_obj.send_message_stream(parts):
                token = chunk.text
                fragments.append(token)
                yield f"event: token\ndata: {token}\n\n"
            # stream end
            full_answer = "".join(fragments)
            chat_log.answer = full_answer
            db.add(chat_log)
            # update session meta
            sess.last_used_at = datetime.utcnow()
            if not sess.title and text:
                sess.title = text[:20]
            await db.commit()
            yield "event: done\ndata: END\n\n"

        headers = {"X-Chat-Session": sess.id}
        return StreamingResponse(sse_generator(), headers=headers, media_type="text/event-stream")