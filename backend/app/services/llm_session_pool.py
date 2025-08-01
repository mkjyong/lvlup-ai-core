"""In-memory LRU cache for Google Gemini ChatSession objects.

확장: 캐시 미스 시 DB 에서 최근 N 개 대화 내역을 로드해 history 에 주입한다.
"""
from __future__ import annotations

import collections
import asyncio
from typing import Dict, List

import google.generativeai as genai  # type: ignore

from app.models.chat_session import ChatSession as ChatSessionRow
from app.models.chat import ChatMessage
from app.models.db import get_session

MAX_LIVE = 10_000
_sessions: Dict[str, genai.types.ChatSession] = collections.OrderedDict()


def _evict_if_needed() -> None:
    while len(_sessions) > MAX_LIVE:
        _sessions.popitem(last=False)



def get_chat(row: ChatSessionRow):  # kept for backward compatibility
    """Return cached ChatSession; create with empty history if absent."""

    sid = row.id
    if sid in _sessions:
        _sessions.move_to_end(sid)
        return _sessions[sid]

    model = genai.GenerativeModel(row.model)
    # Generation parameters (하드코딩 요구 사항)
    gen_conf = {
        "candidate_count": 1,
        "max_output_tokens": 5000,
    }
    # cache_id 는 Gemini context caching 용도로 그대로 유지
    if row.context_cache_id:
        gen_conf["cache_id"] = row.context_cache_id

    # Google Search 툴 활성화 (기본 설정)
    search_tool = genai.tools.GoogleSearch()

    chat = model.start_chat(
        system_instruction=row.system_prompt,
        generation_config=gen_conf,
        tools=[search_tool],
        history=[],
    )
    _sessions[sid] = chat
    _evict_if_needed()
    return chat


# 최대 유지할 최근 대화 '턴'(user+model)의 수
DEFAULT_HISTORY_TURNS = 4

async def get_chat_with_history(row: ChatSessionRow, *, history_limit: int = DEFAULT_HISTORY_TURNS * 2):  # noqa: D401
    """비동기 버전: 캐시 미스 시 DB 히스토리를 초기 history 로 주입.

    Parameters
    ----------
    history_limit : int, optional
        가져올 메시지 수. 기본값은 최근 4턴(user+model 8개 메시지) 입니다.
    """

    sid = row.id
    if sid in _sessions:
        _sessions.move_to_end(sid)
        return _sessions[sid]

    # gather history from DB
    history: List[dict] = []
    try:
        async with get_session() as session:
            from sqlmodel import select

            stmt = (
                select(ChatMessage)
                .where(ChatMessage.session_id == sid)
                .order_by(ChatMessage.created_at.desc())
                .limit(history_limit)
            )
            rows = (await session.exec(stmt)).all()
        for msg in reversed(rows):  # oldest → newest
            history.append({"role": "user", "parts": [genai.Part(text=msg.question)]})
            if msg.answer:
                history.append({"role": "model", "parts": [genai.Part(text=msg.answer)]})
    except Exception:
        history = []  # fallback silently

    model = genai.GenerativeModel(row.model)
    gen_conf = {
        "candidate_count": 1,
        "max_output_tokens": 5000,
    }
    if row.context_cache_id:
        gen_conf["cache_id"] = row.context_cache_id

    search_tool = genai.tools.GoogleSearch()

    chat = model.start_chat(
        system_instruction=row.system_prompt,
        generation_config=gen_conf,
        tools=[search_tool],
        history=history,
    )
    _sessions[sid] = chat
    _evict_if_needed()
    return chat