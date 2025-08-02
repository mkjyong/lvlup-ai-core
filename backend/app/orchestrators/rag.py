"""Retrieval-Augmented Generation (RAG) – minimal Gemini streaming orchestrator.

이 모듈은 Google Gemini ChatSession 기반으로 사용자의 질문을 스트리밍으로
응답하기 위한 가장 작은 단위를 제공합니다. 복잡한 JSON 2-phase, 플레이어
통계, 레거시 OpenAI 호환 로직을 모두 제거하고 다음 책임만 수행합니다.

1. ChatSession 로드/생성   (select_model + system prompt 결정 포함)
2. llm_session_pool.get_chat() 으로 Gemini Chat 객체 획득
3. chat.send_message_stream(parts) 호출 후 (ChatSession, AsyncIterator[str]) 반환

이렇게 단순화함으로써 비즈니스 로직을 RagPipeline.run_stream() 하나로
집약하고, 라우터/서비스 계층은 토큰 스트림을 전달/저장하는 일에만 집중할
수 있습니다.
"""
from __future__ import annotations

import asyncio
import uuid
import os
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional, Tuple
from app.services.genai_client import genai, client as genai_client, types

# Ensure API key configured early

from app.models.chat_session import ChatSession
from app.models.db import get_session
from app.services import prompt as prompt_service
from app.services.llm_session_pool import get_chat
from concurrent.futures import ThreadPoolExecutor

# 전역 한정 ThreadPool – 무제한 스레드 스폰 방지
_STREAM_EXECUTOR = ThreadPoolExecutor(
    max_workers=int(os.getenv("STREAM_WORKERS", "64"))
)
# ---------------------------------------------------------------------------
# Helper – 모델 선택
# ---------------------------------------------------------------------------

def select_model(game: Optional[str]) -> str:  # noqa: D401
    """게임 종류에 따라 LLM 모델명을 선택한다."""

    if game and game.lower() in {"lol", "pubg"}:
        return "gemini-2.5-flash"
    return "gemini-2.5-flash-lite"


# ---------------------------------------------------------------------------
# Helper – flatten contents for token calc / debug
# ---------------------------------------------------------------------------
from typing import List, Dict, Any

def _flatten_contents(contents: List[Dict[str, Any]]) -> str:  # noqa: D401
    """parts 안의 plain text 를 모두 이어붙여 디버그/토큰계산용 문자열 반환"""
    buf: List[str] = []
    for c in contents:
        for p in c.get("parts", []):
            if isinstance(p, str):
                buf.append(p)
            elif isinstance(p, dict) and "text" in p:
                buf.append(str(p["text"]))
    return "\n".join(buf)

# ---------------------------------------------------------------------------
# Main Pipeline – minimal streaming
# ---------------------------------------------------------------------------

@dataclass
class RagPipeline:  # noqa: D101 – simple wrapper
    """Gemini 기반 RAG 파이프라인 (스트리밍 전용)."""

    async def run_stream(
        self,
        *,
        question: str,
        user_id: str,
        plan_tier: str = "free",  # plan_tier 는 quota 체크용 – 현재 로직에선 미사용
        game: str | None = None,
        prompt_type: str | None = None,
        images: List[types.Part] | None = None,
        session_id: str | None = None,
    ) -> Tuple[ChatSession, AsyncIterator[str]]:
        """스트리밍 응답을 위한 단일 엔트리 포인트.

        Parameters
        ----------
        question : str
            사용자의 현재 질문 문자열.
        user_id : str
            Google sub (unique user id).
        plan_tier : str, optional
            요금제 정보(사용량 체크 용도) – 현재 함수 내부에서는 사용하지 않음.
        game : str | None, optional
            게임 타입(lol | pubg 등). 모델 선택에 활용.
        prompt_type : str | None, optional
            시스템 프롬프트 종류(generic | lol | pubg …).
        images : list[types.Part] | None, optional
            이미지 Part 리스트 (multimodal 입력). None 이면 텍스트 전용.
        session_id : str | None, optional
            기존 세션 ID. 없으면 새로 생성.

        Returns
        -------
        tuple(ChatSession, AsyncIterator[str])
            DB 세션 행과 Gemini token 스트림.
        """

        # -------------------------------------------------------------------
        # 1) ChatSession 로드/생성
        # -------------------------------------------------------------------
        async with get_session() as db:
            sess: ChatSession | None = None
            if session_id:
                sess = await db.get(ChatSession, session_id)
            if not sess:
                # 모델 & 시스템 프롬프트 결정
                model = select_model(game)
                try:
                    p_enum = (
                        prompt_service.PromptType(prompt_type)  # type: ignore[arg-type]
                        if prompt_type
                        else prompt_service.PromptType.generic
                    )
                except ValueError:
                    p_enum = prompt_service.PromptType.generic

                sys_prompt = prompt_service.get_system_prompt(p_enum)

                # Gemini SDK v1 – client 기반으로 변경했으므로 미리 모델 인스턴스를 만들 필요 없음.
                # 📌 context caching은 당장 사용하지 않음
                cache_id: str | None = None

                sess = ChatSession(
                    id=str(uuid.uuid4()),
                    user_google_sub=user_id,
                    model=model,
                    system_prompt=sys_prompt,
                    context_cache_id=cache_id,
                )
                db.add(sess)
                await db.commit()

        # -------------------------------------------------------------------
        # 2) 이전 대화 history 로드 (generate_content 용)
        # -------------------------------------------------------------------
        from app.services.llm_session_pool import get_history_contents, _DEFAULT_TOOLS

        history_contents = await get_history_contents(sess)

        # -------------------------------------------------------------------
        # 3) 사용자 입력 파트 구성 (multimodal)
        # -------------------------------------------------------------------
        user_parts: list = list(images) if images else []
        user_parts.append(question)
        history_contents.append({"role": "user", "parts": user_parts})

        # -------------------------------------------------------------------
        # 4) Gemini generate_content(스트리밍) 호출
        # -------------------------------------------------------------------
        # Google GenAI SDK v1 사용 – Client 기반 호출로 변경
        client = genai_client
        gen_conf = {
            "candidate_count": 1,
            "max_output_tokens": 5000,
        }

        # --- Blocking -> Async 변환 -----------------------------------------
        import asyncio
        import structlog
        logger = structlog.get_logger(__name__)

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        logger.info("gemini_request_init", history_len=len(history_contents), prompt_preview=_flatten_contents(history_contents)[:200])

        def _worker() -> None:
            try:
                for chunk in client.models.generate_content(
                    model=sess.model,
                    contents=history_contents,
                    stream=True,
                    tools=_DEFAULT_TOOLS,
                    generation_config=types.GenerationConfig(**gen_conf),
                ):
                    text = getattr(chunk, "text", None)
                    if text:
                        logger.debug("gemini_chunk", text=text)
                        loop.call_soon_threadsafe(queue.put_nowait, text)
            except Exception as e:
                logger.error("gemini_stream_error", err=str(e), exc_info=True)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        # 전역 executor 재활용 (llm 모듈과 동일 로직)
        _STREAM_EXECUTOR.submit(_worker)

        async def _iter() -> AsyncIterator[str]:  # noqa: D401
            while True:
                item = await queue.get()
                if item is None:
                    break
                logger.debug("send_token_to_client", token=item)
                yield item

        return sess, _iter()