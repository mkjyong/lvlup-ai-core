"""In-memory LRU cache for Google Gemini ChatSession objects.

확장: 캐시 미스 시 DB 에서 최근 N 개 대화 내역을 로드해 history 에 주입한다.
"""
from __future__ import annotations

import collections
import asyncio
from typing import Dict, List

from app.services.genai_client import genai, client, types
# from google.genai import types  # type: ignore

# Pre-instantiated grounding tool for Google search (if available)
try:
    GROUNDING_TOOL = types.Tool(google_search=types.GoogleSearch())  # type: ignore[attr-defined]
    _DEFAULT_TOOLS = [GROUNDING_TOOL]
except Exception:
    # Fallback for SDK versions without GoogleSearch or during local testing
    _DEFAULT_TOOLS = []


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

    # Generation config – mapped to new SDK
    gen_conf = types.GenerationConfig(candidate_count=1, max_output_tokens=5000)
    # cache_id is supported via context caching; attach if available
    if row.context_cache_id:
        gen_conf.cache_id = row.context_cache_id  # type: ignore[attr-defined]

    # Google Search grounding tool list
    tools_list = list(_DEFAULT_TOOLS)

    from app.services.genai_client import start_chat_session

    chat = start_chat_session(
        row.model,
        system_instruction=row.system_prompt,
        generation_config=gen_conf,
        tools=tools_list,
    )
    _sessions[sid] = chat
    _evict_if_needed()
    return chat


# 최대 유지할 최근 대화 '턴'(user+model)의 수
DEFAULT_HISTORY_TURNS = 4

async def get_history_contents(
    row: ChatSessionRow,
    *,
    history_limit: int = DEFAULT_HISTORY_TURNS * 2,
) -> List[types.Content]:
    """DB 에서 최근 history 를 Google Gemini generate_content 형식으로 반환합니다.

    기존 ChatSession 객체를 만들지 않고 history 리스트만 구성해 멀티턴 generate_content
    호출에 사용할 수 있게 합니다.
    """

    sid = row.id
    # gather history from DB
    history: List[types.Content] = []
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
            # User message
            history.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=msg.question)]
                )
            )
            # Model response (if exists)
            if msg.answer:
                history.append(
                    types.Content(
                        role="model",
                        parts=[types.Part(text=msg.answer)]
                    )
                )
    except Exception:
        history = []  # fallback silently

    return history

# async def get_chat_with_history(row: ChatSessionRow, *, history_limit: int = DEFAULT_HISTORY_TURNS * 2):  # noqa: D401
#     """비동기 버전: 캐시 미스 시 DB 히스토리를 초기 history 로 주입.

#     Parameters
#     ----------
#     history_limit : int, optional
#         가져올 메시지 수. 기본값은 최근 4턴(user+model 8개 메시지) 입니다.
#     """

#     sid = row.id
#     if sid in _sessions:
#         _sessions.move_to_end(sid)
#         return _sessions[sid]

#     # gather history from DB
#     history: List[dict] = []
#     try:
#         async with get_session() as session:
#             from sqlmodel import select

#             stmt = (
#                 select(ChatMessage)
#                 .where(ChatMessage.session_id == sid)
#                 .order_by(ChatMessage.created_at.desc())
#                 .limit(history_limit)
#             )
#             rows = (await session.exec(stmt)).all()
#         for msg in reversed(rows):  # oldest → newest
#             history.append({"role": "user", "parts": [msg.question]})
#             if msg.answer:
#                 history.append({"role": "model", "parts": [msg.answer]})
#     except Exception:
#         history = []  # fallback silently

#     model = genai.GenerativeModel(row.model)
#     gen_conf = {
#         "candidate_count": 1,
#         "max_output_tokens": 5000,
#     }
#     if row.context_cache_id:
#         gen_conf["cache_id"] = row.context_cache_id

#     # Google Search grounding 툴 (SDK 버전별로 없을 수 있음)
#     tools_list = list(_DEFAULT_TOOLS)

#     chat = model.start_chat(
#         system_instruction=row.system_prompt,
#         generation_config=gen_conf,
#         tools=tools_list,
#         history=history,
#     )
#     _sessions[sid] = chat
#     _evict_if_needed()
#     return chat