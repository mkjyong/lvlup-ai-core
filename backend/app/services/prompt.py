"""Reusable Prompt ID 관리 서비스.

이 프로젝트는 이제 시스템 프롬프트를 OpenAI Responses API에 등록하고
`prompt_id` 로만 참조합니다. 기존 Jinja2 템플릿 로직은 삭제되었습니다.
"""

from typing import Any, Optional
from enum import Enum
import os


class PromptType(str, Enum):
    """Supported prompt categories → env var mapping keys."""

    lol = "lol"
    pubg = "pubg"
    generic = "generic"


# ---------------------------------------------------------------------------
# Reusable Prompt ID helpers
# ---------------------------------------------------------------------------

_PROMPT_ENV_MAP = {
    PromptType.generic: "PROMPT_ID_GENERIC",
    PromptType.lol: "PROMPT_ID_LOL",
    PromptType.pubg: "PROMPT_ID_PUBG",
}


def get_prompt_id(ptype: "PromptType") -> Optional[str]:  # noqa: D401
    """Return reusable prompt_id for given prompt type.

    If the corresponding env variable is unset, returns ``None`` so that the
    caller can decide whether to raise or handle the error.
    """

    env_key = _PROMPT_ENV_MAP.get(ptype)
    return os.getenv(env_key) if env_key else None


# ---------------------------------------------------------------------------
# Legacy API stubs (safety)
# ---------------------------------------------------------------------------


def render(*_args: Any, **_kwargs: Any):  # type: ignore[return-value]
    """Deprecated stub – Prompt rendering via Jinja2 is removed."""

    raise RuntimeError("render() is deprecated. Use reusable prompt_id instead.")


def token_guard(prompt: str, *_args: Any, **_kwargs: Any) -> str:  # noqa: D401
    """No-op token guard maintained for backward compatibility."""

    return prompt 