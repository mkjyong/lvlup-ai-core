"""System prompt 관리 서비스 (Google Gemini).

Google Gemini API 는 OpenAI 의 reusable prompt ID 기능을 지원하지 않으므로
시스템 프롬프트를 코드 내부 상수로 관리한다. 버저닝은 아직 필요 없으며,
현재는 목업 텍스트를 사용한다.
"""

from enum import Enum
from typing import Any, Dict


class PromptType(str, Enum):
    lol = "lol"
    pubg = "pubg"
    generic = "generic"


# ---------------------------------------------------------------------------
# System Prompt 텍스트
# ---------------------------------------------------------------------------

_PROMPT_TEXTS: Dict[PromptType, str] = {
    PromptType.generic: "You are a professional esports coach. (mock system prompt)",
    PromptType.lol: "You are a professional League of Legends coach. (mock system prompt)",
    PromptType.pubg: "You are a professional PUBG coach. (mock system prompt)",
}


def get_system_prompt(ptype: "PromptType") -> str:  # noqa: D401
    """Return the system prompt text for the given prompt type."""
    return _PROMPT_TEXTS.get(ptype, _PROMPT_TEXTS[PromptType.generic])


# ---------------------------------------------------------------------------
# Legacy stubs (backward compatibility)
# ---------------------------------------------------------------------------

def get_prompt_id(ptype: "PromptType"):
    """Deprecated – kept for backward compatibility."""
    return None


def render(*_args: Any, **_kwargs: Any):  # type: ignore[return-value]
    """Deprecated stub – Prompt rendering via Jinja2 is removed."""
    raise RuntimeError("render() is deprecated. Use system prompt text instead.")


def token_guard(prompt: str, *_args: Any, **_kwargs: Any) -> str:  # noqa: D401
    """No-op token guard maintained for backward compatibility."""
    return prompt
