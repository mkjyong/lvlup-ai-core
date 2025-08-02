"""Chat router – session CRUD and messages list.

/ chat/message 레거시 엔드포인트는 제거되었으며, 대신 /api/coach/ask/stream 을
사용해야 한다.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from app.services.genai_client import genai, types
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
# Legacy message endpoint stub (removed)
# ---------------------------------------------------------------------------


def _legacy_chat_message_removed(*_args, **_kwargs):  # noqa: D401
    """Removed endpoint placeholder – always raises RuntimeError."""
    raise RuntimeError("/chat/message endpoint has been removed. Use /api/coach/ask/stream instead.")
