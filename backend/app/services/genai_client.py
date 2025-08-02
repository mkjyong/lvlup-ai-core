"""Centralized Google GenAI SDK client wrapper.

This module upgrades the code base from the deprecated `google-generativeai`
SDK to the new `google-genai` SDK introduced July 2025
(https://github.com/googleapis/python-genai).

Key design goals
----------------
1. **Singleton client** – avoid re-creating TCP connections / auth overhead.
2. **Thin wrapper** – expose only helper utilities required by the rest of
   the codebase while **NOT** re-implementing the old API surface. All call
   sites must migrate to the new official method names.
3. **Explicit model selection** – every public helper takes `model_name: str`
   so that plan-tier ↔ model mapping logic lives at the call-site, keeping
   this layer stateless.

The wrapper intentionally keeps a minimal surface so that future SDK changes
are localised here, _without hiding_ the official SDK objects.  When a caller
needs advanced features (RAG, tool-calling, etc.) they should import the
native `google.genai` symbols directly after obtaining the shared `client`.

Example
~~~~~~~
>>> from app.services.genai_client import client, genai, types, generate_text
>>> text = generate_text("gemini-2.5-flash", "Hello world!")
>>> print(text)
"Hello! How can I assist you today?"
"""
from __future__ import annotations

import os
import functools
from typing import Any, Iterable, List

from google import genai  # type: ignore
from google.genai import types  # type: ignore

# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def _make_client() -> genai.Client:  # pragma: no cover – trivial
    """Initialise and cache a single `genai.Client` instance.

    The function is wrapped with ``lru_cache`` so every import in the process
    tree receives the same instance, mirroring how the old SDK used a global
    configuration object.
    """

    # 1) OS env var takes highest precedence (k8s secret, CI job, etc.)
    api_key: str | None = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    # 2) Fallback to application settings (.env) so local dev works without `export`.
    if not api_key:
        try:
            from app.config import get_settings

            api_key = get_settings().GEMINI_API_KEY
        except Exception:  # pragma: no cover – config import should always succeed
            api_key = None

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable is not set; "
            "define it in your shell or .env file"
        )

    # The GenAI SDK auto-detects backend (Gemini API vs Vertex AI) based on the
    # presence of GOOGLE_GENAI_USE_VERTEXAI.  We stick to defaults unless the
    # operator explicitly opts-in to Vertex.
    return genai.Client(api_key=api_key)


client: genai.Client = _make_client()

# re-export frequently used symbols for convenience
__all__ = [
    "client",
    "genai",
    "types",
    "generate_text",
    "generate_text_stream",
    "count_tokens",
    "start_chat_session",
]

# ---------------------------------------------------------------------------
# High-level helper utilities (text-only – most common path)
# ---------------------------------------------------------------------------

def _normalize_contents(prompt: str | Iterable[str]) -> List[types.Content]:
    """Convert str or iterable[str] into SDK `Content` list with role=user."""
    if isinstance(prompt, str):
        prompt = [prompt]
    return [types.Content(role="user", parts=[types.Part.from_text(p)]) for p in prompt]


def generate_text(model_name: str, prompt: str | Iterable[str], **kwargs: Any) -> str:
    """Synchronous text generation – returns the first candidate's text."""
    contents = _normalize_contents(prompt)
    resp = client.models.generate_content(
        model=model_name,
        contents=contents,
        **kwargs,
    )
    return resp.text  # type: ignore[attr-defined]


def generate_text_stream(
    model_name: str,
    prompt: str | Iterable[str],
    **kwargs: Any,
):
    """Streaming generator yielding text fragments."""
    contents = _normalize_contents(prompt)
    for chunk in client.models.generate_content(
        model=model_name,
        contents=contents,
        stream=True,
        **kwargs,
    ):
        text = getattr(chunk, "text", None)
        if text:
            yield text


def count_tokens(model_name: str, prompt: str) -> int:
    """Return token count for *prompt* using official tokenizer."""
    contents = _normalize_contents(prompt)
    resp = client.models.count_tokens(model=model_name, contents=contents)
    return resp.total_tokens

# ---------------------------------------------------------------------------
# Chat helper (multi-turn)
# ---------------------------------------------------------------------------

def start_chat_session(
    model_name: str,
    *,
    system_instruction: str | None = None,
    generation_config: types.GenerationConfig | None = None,
    tools: list[types.Tool] | None = None,
):
    """Return a `genai.Chat` object ready for multi-turn conversation."""
    return client.chats.create(
        model=model_name,
        config=generation_config,
        history=None,
        system_instruction=system_instruction,
    )
