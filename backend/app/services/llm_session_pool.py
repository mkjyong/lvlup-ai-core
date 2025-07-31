"""In-memory LRU cache for Google Gemini ChatSession objects."""
from __future__ import annotations

import collections
from typing import Dict

import google.generativeai as genai  # type: ignore

from app.models.chat_session import ChatSession as ChatSessionRow

MAX_LIVE = 10_000
_sessions: Dict[str, genai.types.ChatSession] = collections.OrderedDict()


def _evict_if_needed() -> None:
    while len(_sessions) > MAX_LIVE:
        _sessions.popitem(last=False)


def get_chat(row: ChatSessionRow):
    """Return cached ChatSession; create if absent."""
    sid = row.id
    if sid in _sessions:
        _sessions.move_to_end(sid)
        return _sessions[sid]

    model = genai.GenerativeModel(row.model)
    gen_conf = {"max_thought_tokens": 512}
    if row.context_cache_id:
        gen_conf["cache_id"] = row.context_cache_id

    chat = model.start_chat(
        system_instruction=row.system_prompt,
        generation_config=gen_conf,
        history=[],
    )
    _sessions[sid] = chat
    _evict_if_needed()
    return chat