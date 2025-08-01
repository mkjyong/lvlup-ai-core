"""Gemini LLM 호출 래퍼.

기존 OpenAI Responses API 의 호출 래퍼를 Google Gemini API 로 교체하였다.

변경 사항:
1. google-generativeai SDK 를 사용해 Gemini 2.5 모델 호출
2. 내부 모델명(gpt-4o-mini, o4-mini)을 Gemini 모델명에 매핑
   - gpt-4o-mini → gemini-2.5-flash-lite
   - o4-mini     → gemini-2.5-flash
3. 비동기 API 호환을 위해 `asyncio.to_thread` 로 동기 SDK 호출을 오프로드
4. API 키는 `GEMINI_API_KEY` 환경변수 또는 Settings 필드에서 로드
5. 기존 테스트 스텁 동작 유지 (API 키 미설정 시 echo 응답)
"""
from __future__ import annotations

import asyncio
import os
import threading
from collections.abc import AsyncIterator
from typing import List

import google.generativeai as genai  # type: ignore
from google.genai import types  # type: ignore

from app.config import MODEL_CATEGORY, get_settings
from app.exceptions import AIError
import app.services.token_manager as token_manager

GROUNDING_TOOL = types.Tool(google_search=types.GoogleSearch())

# ---------------------------------------------------------------------------
# 초기 설정
# ---------------------------------------------------------------------------
settings = get_settings()

# SDK 초기화 (API 키 없으면 stub 모드로 동작)
_GEMINI_API_KEY = settings.__dict__.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
if _GEMINI_API_KEY:
    genai.configure(api_key=_GEMINI_API_KEY)


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _stub_response() -> bool:
    """환경 변수 미설정 시 stub 사용 여부."""

    return _GEMINI_API_KEY == ""


def _map_model_name(internal: str) -> str:
    """내부 모델명을 Gemini 실제 모델명으로 매핑."""

    mapping = {
        "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
        "gemini-2.5-flash": "gemini-2.5-flash",
    }
    return mapping.get(internal, "gemini-2.5-flash-lite")


async def _generate_content_with_usage(model: str, prompt: str, *, enable_search: bool = True):
    """Gemini generate_content를 호출하고 (text, usage_metadata) 튜플 반환."""

    def _call():
        gen_model = genai.GenerativeModel(model)
        kw: dict = {}
        if enable_search:
            kw["tools"] = [GROUNDING_TOOL]
        resp = gen_model.generate_content(prompt, **kw)
        text = (getattr(resp, "text", None) or str(resp)).strip()
        return text, getattr(resp, "usage_metadata", None)

    return await asyncio.to_thread(_call)


# ---------------------------------------------------------------------------
# Streaming helper
# ---------------------------------------------------------------------------

from concurrent.futures import ThreadPoolExecutor

# 전역 한정 ThreadPool – 무제한 스레드 스폰 방지
_STREAM_EXECUTOR = ThreadPoolExecutor(
    max_workers=int(os.getenv("STREAM_WORKERS", "64"))
)

def _stream_content(model: str, prompt: str, *, enable_search: bool = True):
    """Google Gemini SDK 스트리밍 결과를 AsyncIterator 로 래핑.

    ThreadPoolExecutor 에 작업을 제출해 동시에 실행되는 blocking worker
    수를 제어한다. 풀 초과 시 RuntimeError 를 발생시켜 상위 레이어에서
    429/503 등을 반환하도록 유도할 수 있다.
    """

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    def _worker() -> None:
        try:
            gen_model = genai.GenerativeModel(model)
            kw: dict = {}
            if enable_search:
                kw["tools"] = [GROUNDING_TOOL]
            for chunk in gen_model.generate_content(prompt, stream=True, **kw):
                text = getattr(chunk, "text", None)
                if text:
                    loop.call_soon_threadsafe(queue.put_nowait, text)
        finally:
            # sentinel to close iterator
            loop.call_soon_threadsafe(queue.put_nowait, None)

    # 풀에 작업 제출 (풀 초과 시 RuntimeError)
    try:
        _STREAM_EXECUTOR.submit(_worker)
    except RuntimeError:
        raise AIError("Server busy, please retry later")

    async def _iterator() -> AsyncIterator[str]:  # noqa: D401
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

    return _iterator()

# ---------------------------------------------------------------------------
# Public API (OpenAI 호환 시그니처 유지)
# ---------------------------------------------------------------------------

async def response_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    max_tokens: int | None = None,  # Gemini API 는 자체 토큰 제한에 맞게 자르므로 참고만
    prompt_ids: list[str] | None = None,  # Gemini 에는 해당 기능이 없으므로 무시
    user_id: str | None = None,
    plan_tier: str = "free",
    # Reusable prompt variables
    prompt_vars: dict | None = None,  # prompt vars 는 템플릿 시스템에 따라 직접 문자열로 치환
    stream: bool = False,  # 스트리밍 미지원 (향후 업그레이드)
    response_format: dict | None = None,
) -> "AsyncIterator[str] | str":  # 스트림이면 async iterator, 아니면 str
    """Google Gemini API 기반 텍스트 생성 래퍼.

    기존 OpenAI Responses API 와 동일한 함수 시그니처를 유지해
    상위 레이어 코드 변경 없이 교체할 수 있도록 설계하였다.
    """

    from app.services import usage as usage_service  # local import (순환 방지)

    # -------------------------------------------------------------------
    # Stub: API 키가 없을 때는 간단히 echo 반환 (테스트 환경)
    # -------------------------------------------------------------------
    if _stub_response():
        last_user_msg = next(
            (m for m in reversed(messages) if m.get("role") == "user"),
            {"content": ""},
        )
        return f"[STUB] {last_user_msg.get('content', '')}"

    # 메시지 토큰 트리밍 (기존 로직 재사용)
    messages = token_manager.trim_messages(messages)

    # 모델 매핑 ----------------------------------------------------------
    internal_model = model or "gemini-2.5-flash-lite"
    gemini_model = _map_model_name(internal_model)

    # 요금제/사용량 체크 ---------------------------------------------------
    if user_id:
        quota_ok = await usage_service.has_quota(user_id, plan_tier, internal_model)
        if not quota_ok:
            raise AIError("요금제별 호출 횟수 한도 초과")

    # Prompt 조립 ---------------------------------------------------------
    # Gemini 는 role 구조를 별도로 지원하지 않으므로 "role: content" 형태로 단순 병합
    prompt_parts: list[str] = []
    for m in messages:
        role = m.get("role", "user")
        prompt_parts.append(f"{role}: {m.get('content', '')}")

    # prompt vars ({{ placeholder }}) 를 단순 치환 (Jinja 등 미사용)
    prompt_text = "\n".join(prompt_parts)
    if prompt_vars:
        for k, v in prompt_vars.items():
            prompt_text = prompt_text.replace(f"{{{{{k}}}}}", str(v))

    # 구조화 출력(request.response_format) 이 JSON 일 때는 system 지시어 추가
    if response_format and response_format.get("type") == "json_object":
        prompt_text = (
            "다음 JSON 스키마에 맞추어 응답하세요:\n"  # 간단 프롬프트
            + str(response_format.get("schema", {}))
            + "\n\n"
            + prompt_text
        )

    # -------------------------------------------------------------------
    # Gemini API 호출 (stream 지원 여부에 따라 분기)
    # -------------------------------------------------------------------
    if stream:
        # Gemini SDK 실시간 스트리밍 처리
        encoder = token_manager.ENCODER
        fragments: list[str] = []

        # 정확한 입력 토큰: count_tokens 활용 (실패 시 fallback)
        prompt_tokens_count = 0
        if user_id:
            try:
                prompt_tokens_count = genai.GenerativeModel(gemini_model).count_tokens(prompt_text).total_tokens  # type: ignore[attr-defined]
            except Exception:
                prompt_tokens_count = sum(token_manager.message_tokens(m) for m in messages)

        async def _iter() -> AsyncIterator[str]:  # type: ignore[override]
            async for piece in _stream_content(gemini_model, prompt_text, enable_search=True):
                fragments.append(piece)
                yield piece
            # 스트림 종료 후 사용량 로깅
            if user_id and fragments:
                completion_tokens = len(encoder.encode("".join(fragments)))
                await usage_service.log_usage(
                    user_id=user_id,
                    model=internal_model,
                    prompt_tokens=prompt_tokens_count,
                    completion_tokens=completion_tokens,
                )

        return _iter()

    # non-stream ---------------------------------------------------------
    text, usage_meta = await _generate_content_with_usage(
        gemini_model, prompt_text, enable_search=True
    )

    if user_id and usage_meta:
        # 공식 usage_metadata 활용
        prompt_tokens = getattr(usage_meta, "prompt_token_count", 0)
        completion_tokens = getattr(usage_meta, "candidates_token_count", 0)
        await usage_service.log_usage(
            user_id=user_id,
            model=internal_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    elif user_id:
        # fallback: 추정 방식
        encoder = token_manager.ENCODER
        prompt_tokens = sum(token_manager.message_tokens(m) for m in messages)
        completion_tokens = len(encoder.encode(text))
        await usage_service.log_usage(
            user_id=user_id,
            model=internal_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    result_text = text

    return result_text