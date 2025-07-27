"""OpenAI LLM 호출 래퍼 (Stub)."""
import asyncio
from typing import Any, List

import openai

from app.config import get_settings
from app.exceptions import AIError

import app.services.token_manager as token_manager
from app.config import MODEL_CATEGORY

import os

from collections.abc import AsyncIterator

# Load global settings once --------------------------------------------

settings = get_settings()

# Configure OpenAI client globally (HTTP2 enabled by default)
openai.api_key = settings.OPENAI_API_KEY or ""  # 빈 키 허용


# Stub helper (unit tests / no API key) --------------------------------


def _stub_response() -> bool:
    """환경 변수 미설정 시 stub 사용 여부."""

    return not settings.OPENAI_API_KEY

# ---------------------------------------------------
# Vector Store Retrieval helper (none needed)
# ---------------------------------------------------


async def response_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    prompt_ids: list[str] | None = None,
    user_id: str | None = None,
    plan_tier: str = "free",
    # Vector Store options
    use_vector_store: bool = True,
    top_k: int | None = None,
    filters: dict | None = None,
    # Reusable prompt variables
    prompt_vars: dict | None = None,
    stream: bool = False,
    response_format: dict | None = None,
) -> "AsyncIterator[str] | str":  # 스트림이면 async iterator 반환, 아니면 str
    """OpenAI **Responses API** 호출 래퍼.

    File-search tool을 통해 RAG 문서를 자동 검색하며 기존 `chat_completion`과 동일한
    사용량 로깅, 백오프 로직을 유지한다.
    """

    from app.services import usage as usage_service  # local import

    # 토큰 한도 로직은 기존 chat_completion 재사용 ----------------------
    if user_id:
        plan = await usage_service._get_active_plan(user_id)
        prompt_limit = plan.prompt_limit or 0
        completion_limit = plan.completion_limit or 0
    else:
        prompt_limit = completion_limit = 0

    limits = {"prompt": prompt_limit, "completion": completion_limit}

    # 메시지 토큰 트리밍 ------------------------------------------------
    messages = token_manager.trim_messages(messages)

    # -------------------------------------------------------------
    # Stub: API 키가 없을 때는 임의 응답 리턴 (테스트 환경)
    # -------------------------------------------------------------
    if _stub_response():
        # 가장 최근 user 메시지에 간단히 에코
        last_user_msg = next((m for m in reversed(messages) if m.get("role") == "user"), {"content": ""})
        return f"[STUB] {last_user_msg.get('content', '')}"

    # 한도 검사 ---------------------------------------------------------
    if limits["prompt"]:
        prompt_tokens_est = sum(
            token_manager.message_tokens(m) for m in messages if m.get("role") == "user"
        )
        if prompt_tokens_est > limits["prompt"]:
            raise AIError("프롬프트 토큰 한도 초과")

    model_to_use = model or (
        "o4-mini" if MODEL_CATEGORY.get(model or "gpt-4o-mini", "general") == "special" else "gpt-4o-mini"
    )

    # 응답 토큰 한도 ----------------------------------------------------
    completion_limit = limits["completion"]
    if completion_limit and max_tokens is not None:
        final_max_tokens = min(max_tokens, completion_limit)
    elif completion_limit:
        final_max_tokens = completion_limit
    else:
        final_max_tokens = max_tokens

    # ----- Vector Store Retrieval tool -------------------------------
    tools: list[dict[str, object]] = []

    if use_vector_store and os.getenv("OPENAI_VECTOR_STORE_ID"):
        vs_id = os.getenv("OPENAI_VECTOR_STORE_ID")
        tool_payload: dict[str, object] = {
            "type": "file_search",
            "vector_store_ids": [vs_id],
        }
        if top_k is not None:
            tool_payload["max_results"] = top_k
        if filters:
            tool_payload["filters"] = filters

        tools.append(tool_payload)

    request: dict[str, object] = {
        "model": model_to_use,
        "messages": messages,
        "max_tokens": final_max_tokens,
        "store": False,
    }

    # ---------------- Prompt Variables -----------------------------
    if prompt_vars:
        # OpenAI Responses API uses `prompt_vars` (dict[str,str]) to replace
        # placeholders (e.g. {{player_stats}}) in reusable prompts.
        request["prompt_vars"] = prompt_vars  # type: ignore[typeddict-item]

    # 추가 옵션 -------------------------------------------------------
    if stream:
        request["stream"] = True
    if response_format is not None:
        request["response_format"] = response_format  # type: ignore[typeddict-item]

    if tools:
        request["tools"] = tools  # type: ignore[typeddict-item]
    if prompt_ids:
        request["prompt_ids"] = prompt_ids  # Reusable system prompt

    # ------------------------- 호출 & 로깅 ---------------------------
    max_retries, delay = 3, 1
    for attempt in range(max_retries):
        try:
            if user_id:
                quota_ok = await usage_service.has_quota(user_id, plan_tier, model_to_use)
                if not quota_ok:
                    raise AIError("요금제별 호출 횟수 한도 초과")

            # 스트림 / 논스트림 분기 ---------------------------------
            if stream:
                # 스트림 응답은 AsyncIterator 반환
                resp_stream = await openai.responses.create(**request)  # type: ignore[arg-type]

                # --- 토큰 집계용 버퍼 -------------------------------
                fragments: list[str] = []  # delta 문자열 모음
                encoder = token_manager.ENCODER
                prompt_tokens_est = sum(token_manager.message_tokens(m) for m in messages)

                async def _token_iterator():
                    nonlocal fragments  # noqa: PLW0603
                    try:
                        async for chunk in resp_stream:  # type: ignore[async-iteration-over-sync]
                            if hasattr(chunk, "choices") and chunk.choices:
                                delta = chunk.choices[0].delta  # type: ignore[attr-defined]
                                content = getattr(delta, "content", None)
                                if content:
                                    fragments.append(content)
                                    yield content
                    finally:
                        # 응답 스트림 종료 및 리소스 정리
                        await getattr(resp_stream, "aiter_close", lambda: None)()

                        # ------ 사용량 로깅 -------------------------
                        if user_id and fragments:
                            try:
                                full_text = "".join(fragments)
                                completion_tokens_acc = len(encoder.encode(full_text))
                                await usage_service.log_usage(
                                    user_id=user_id,
                                    model=request["model"],
                                    prompt_tokens=prompt_tokens_est,
                                    completion_tokens=completion_tokens_acc,
                                )
                            except Exception:  # pragma: no cover
                                pass

                return _token_iterator()

            # ---------------- Non-stream -----------------------------
            resp = await openai.responses.create(**request)  # type: ignore[arg-type]

            # usage logging ------------------------------------------
            if user_id and getattr(resp, "usage", None):
                try:
                    u = resp.usage  # type: ignore[attr-defined]
                    await usage_service.log_usage(
                        user_id=user_id,
                        model=request["model"],
                        prompt_tokens=u.prompt_tokens,  # type: ignore[attr-defined]
                        completion_tokens=u.completion_tokens,  # type: ignore[attr-defined]
                    )
                except Exception:  # pragma: no cover
                    pass

            # Responses API – SDK 예상 (choices[0].message or response.text)
            if hasattr(resp, "choices"):
                return resp.choices[0].message.content.strip()
            if hasattr(resp, "response"):
                return resp.response  # type: ignore[return-value]
            return str(resp)
        except Exception as exc:  # pragma: no cover
            if attempt == max_retries - 1:
                raise AIError("LLM 호출 실패") from exc
            await asyncio.sleep(delay)
            delay *= 2


async def embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """텍스트 임베딩을 OpenAI로부터 가져온다."""

    if _stub_response():
        # random small vector stub
        return [0.0] * 5

    max_retries = 3
    delay = 1
    for attempt in range(max_retries):
        try:
            resp = await openai.embeddings.create(input=[text], model=model)  # type: ignore[arg-type]
            return resp.data[0].embedding  # type: ignore[return-value]
        except Exception as exc:  # pragma: no cover
            if attempt == max_retries - 1:
                raise AIError("임베딩 생성 실패") from exc
            await asyncio.sleep(delay)
            delay *= 2 