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
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional, Tuple

import google.generativeai as genai  # type: ignore

from app.models.chat_session import ChatSession
from app.models.db import get_session
from app.services import prompt as prompt_service
from app.services.llm_session_pool import get_chat

# ---------------------------------------------------------------------------
# Helper – 모델 선택
# ---------------------------------------------------------------------------

def select_model(game: Optional[str]) -> str:  # noqa: D401
    """게임 종류에 따라 LLM 모델명을 선택한다."""

    if game and game.lower() in {"lol", "pubg"}:
        return "gemini-2.5-flash"
    return "gemini-2.5-flash-lite"


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
        images: List[genai.Part] | None = None,
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
        images : list[genai.Part] | None, optional
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

                gen_model = genai.GenerativeModel(model)
                cache_resp = await asyncio.to_thread(gen_model.cache_context, sys_prompt)
                cache_id = getattr(cache_resp, "cache_id", None)

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
        # 2) Gemini Chat 객체 준비
        # -------------------------------------------------------------------
        from app.services.llm_session_pool import get_chat_with_history
        chat = await get_chat_with_history(sess)  # LRU cache + DB history

        # 사용자 입력 파트 구성 (multimodal)
        parts: List[genai.Part] = list(images) if images else []
        parts.append(genai.Part(text=question))

        # -------------------------------------------------------------------
        # 3) Streaming 호출 및 반환
        # -------------------------------------------------------------------
        stream_iter = chat.send_message_stream(parts)

        return sess, stream_iter