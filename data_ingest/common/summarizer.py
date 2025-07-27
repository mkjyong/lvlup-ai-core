from __future__ import annotations

"""Chunk summarization utility using OpenAI ChatCompletion.

- 1-2 line concise summary in source language
- Async function with basic retry
"""

import os
from typing import List

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None  # type: ignore

from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential, retry_if_exception_type
from data_ingest.common.logger import logger


async def summarize_chunks(chunks: List[str], model: str | None = None) -> List[str]:
    """Summarize each chunk into a short sentence.

    Args:
        chunks: list of raw chunk texts
        model: openai model name
    Returns: list of summary strings (same length as chunks)
    """
    if openai is None:
        raise ImportError("openai 패키지가 필요합니다: pip install openai")

    client = openai.AsyncOpenAI()
    sys_prompt = (
        "당신은 게임 패치/전략 요약 도우미입니다. 주어진 텍스트를 1문장으로 핵심만 요약하세요."
    )

    async def _single(text: str) -> str:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(4),
            wait=wait_exponential(min=1, max=8),
            retry=retry_if_exception_type(openai.OpenAIError),
            reraise=True,
        ):
            with attempt:
                resp = await client.chat.completions.create(
                    model=model or "gpt-4.1-nano",
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": text[:3000]},
                    ],
                    max_tokens=40,
                    temperature=0.3,
                )
                return resp.choices[0].message.content.strip()
        return ""

    # sequential to avoid rate limits; could be batched
    summaries: List[str] = []
    for t in chunks:
        try:
            summaries.append(await _single(t))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Summarization failed: %s", exc)
            summaries.append("")
    return summaries


async def compress_chunks(
    chunks: List[str],
    *,
    model: str | None = "gpt-4.1-nano-2025-04-14",
    style: str = "plain",
    max_output_tokens: int = 300,
) -> List[str | None]:
    """압축(clean-up) summarization.

    각 입력 문단에서 불필요 문장을 제거하고 핵심 정보만 남겨 반환한다.
    정보가 없으면 "SKIP" 문자열을 응답하도록 프롬프트에 지시하며,
    이 경우 None 을 반환하여 downstream 단계에서 건너뛸 수 있게 한다.

    Args:
        chunks: 원본 문단 리스트
        model: 호출할 OpenAI 모델명
        style: "plain" 또는 "bullet" 등. plain 이 기본.
        max_output_tokens: 출력 토큰 최대치
    Returns: 같은 길이의 리스트. "SKIP" 또는 오류 시 None.
    """

    if openai is None:
        raise ImportError("openai 패키지를 설치하세요: pip install openai")

    client = openai.AsyncOpenAI()

    # 공통 system 프롬프트
    sys_prompt_base = (
        "당신은 게임 전문 에디터입니다. "
        "입력 문단에서 중요한 수치·스킬 효과·절차는 반드시 유지하고, "
        "불필요한 서술·형용사·중복 표현은 제거하여 간결하게 만드세요. "
        "내용이 의미가 없거나 이미 요약 수준이면 단어 'SKIP'만 출력하세요."
    )

    if style == "bullet":
        sys_prompt_base += "\n출력 형식: 각 정보마다 '• ' 기호로 시작하는 bullet list."

    async def _single(text: str) -> str | None:
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(4),
                wait=wait_exponential(min=1, max=8),
                retry=retry_if_exception_type(openai.OpenAIError),
                reraise=True,
            ):
                with attempt:
                    resp = await client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": sys_prompt_base},
                            {"role": "user", "content": text[:4000]},
                        ],
                        max_tokens=max_output_tokens,
                        temperature=0.2,
                    )
                    out = resp.choices[0].message.content.strip()
                    if out.upper() == "SKIP":
                        return None
                    return out
        except Exception as exc:  # noqa: BLE001
            logger.warning("Compression failed: %s", exc)
            return None

    out_list: List[str | None] = []
    for t in chunks:
        out_list.append(await _single(t))
    return out_list 