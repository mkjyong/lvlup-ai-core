"""Retrieval-Augmented Generation orchestration layer."""
from dataclasses import dataclass
from typing import List, Optional

from app.services import prompt as prompt_service
from app.services import llm as llm_service
from app.services import chat as chat_service
from app.services import performance as perf_service
from app.services.llm_session_pool import get_chat
from app.models.chat_session import ChatSession
# NEW: schema imports
from app.schemas import coach as coach_schemas
import json
import google.generativeai as genai  # type: ignore


def select_model(game: Optional[str]) -> str:
    """게임 타입에 따라 사용할 LLM 모델 결정."""
    if game and game.lower() in {"lol", "pubg"}:
        return "gemini-2.5-flash"
    return "gemini-2.5-flash-lite"


@dataclass
class RagPipeline:
    """Main RAG orchestration pipeline."""

    # async def run(
    #     self,
    #     *,
    #     question: str,
    #     user_id: str,
    #     plan_tier: str = "free",
    #     game: Optional[str] = None,
    #     prompt_type: Optional[str] = None,
    #     include_history: bool = True,
    #     history_limit: int = 10,
    # ) -> str:
    #     """Execute full RAG flow and return answer string."""

    #     # --- 요금제별 히스토리 제한 --------------------------------
    #     if plan_tier == "free":
    #         history_limit = min(history_limit, 5)  # 최신 2쌍만 유지

    #     # 2) 게임별 Player Stats 확보 --------------------------------
    #     player_stats_block: str | None = None
    #     if game and user_id:
    #         try:
    #             from app.models.db import get_session  # local import to avoid circular

    #             async with get_session() as session:
    #                 stats = await perf_service.ensure_stats_cached(session, user_id, game)
    #             # 간단한 Key:Value 나열로 문자열 변환
    #             stats_str = "\n".join(f"- {k}: {v}" for k, v in stats.items())
    #             player_stats_block = f"[PlayerStats]\n{stats_str}"
    #         except Exception:
    #             # 캐시에 실패해도 계속 진행 (게임 계정 미등록 등)
    #             player_stats_block = None

    #     # 3) Render system prompt (게임별 템플릿)
    #     ptype = prompt_type or prompt_service.PromptType.generic.name
    #     try:
    #         prompt_enum = prompt_service.PromptType[ptype]
    #     except KeyError:
    #         prompt_enum = prompt_service.PromptType.generic

    #     # 3) Determine reusable prompt ID (Responses API) -------------------
    #     system_prompt = prompt_service.get_system_prompt(prompt_enum)

    #     # 4) Build prompt variables & message -------------------------
    #     prompt_vars: dict[str, str] = {}

    #     if player_stats_block:
    #         prompt_vars["player_stats"] = player_stats_block

    #     if include_history and user_id:
    #         history = await chat_service.list_chat_history(user_id, history_limit, game)
    #         # oldest → newest 로 정렬, 간단히 assistant answer만 이어붙임
    #         conv_snippets = "\n\n".join(h.answer for h in reversed(history))
    #         if conv_snippets:
    #             prompt_vars["conversation_snippets"] = conv_snippets

    #     # 메시지는 현재 질문만 포함
    #     messages: List[dict[str, str]] = []
    #     if system_prompt:
    #         messages.append({"role": "system", "content": system_prompt})
    #     messages.append({"role": "user", "content": question})


    #     # 6) Determine model
    #     model = select_model(game)

    #     # 7) Call Responses API 래퍼 -----------------------------------
    #     answer = await llm_service.response_completion(
    #         messages,
    #         model=model,
            
    #         user_id=user_id,
    #         plan_tier=plan_tier,
    #         prompt_vars=prompt_vars or None,
    #     )

    #     return answer 

# -------------------------------------------------------------------
# NEW helper and stream method
# -------------------------------------------------------------------

    async def run_stream(
        self,
        *,
        question: str,
        user_id: str,
        plan_tier: str = "free",
        game: Optional[str] = None,
        prompt_type: Optional[str] = None,
        image_parts: list | None = None,
        session_row: "ChatSession" | None = None,
    ):
        """1) JSON 구조 응답 → 2) 스트리밍 commentary 토큰 순으로 async generator 리턴."""

        player_stats_block: str | None = None
        if game and user_id:
            try:
                from app.models.db import get_session

                async with get_session() as session:
                    stats = await perf_service.ensure_stats_cached(session, user_id, game)
                stats_str = "\n".join(f"- {k}: {v}" for k, v in stats.items())
                player_stats_block = f"[PlayerStats]\n{stats_str}"
            except Exception:  # pragma: no cover
                player_stats_block = None

        ptype = prompt_type or prompt_service.PromptType.generic.name
        try:
            prompt_enum = prompt_service.PromptType[ptype]
        except KeyError:
            prompt_enum = prompt_service.PromptType.generic

        system_prompt = prompt_service.get_system_prompt(prompt_enum)



        prompt_vars: dict[str, str] = {}
        if player_stats_block:
            prompt_vars["player_stats"] = player_stats_block


        messages: List[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": question})

        model = select_model(game)

        # -------------------------------------------------------------------
        # ChatSession 로드/생성 ------------------------------------------------
        # -------------------------------------------------------------------
        if session_row is None:
            from app.models.db import get_session  # local import
            import asyncio, uuid
            async with get_session() as db:
                if session_row is None:
                    # 새 세션 생성
                    ptype = prompt_type or prompt_service.PromptType.generic.name
                    try:
                        prompt_enum = prompt_service.PromptType[ptype]
                    except KeyError:
                        prompt_enum = prompt_service.PromptType.generic
                    system_prompt = prompt_service.get_system_prompt(prompt_enum)
                    gen_model = genai.GenerativeModel(model)
                    cache_resp = await asyncio.to_thread(gen_model.cache_context, system_prompt)
                    session_row = ChatSession(
                        id=str(uuid.uuid4()),
                        user_google_sub=user_id,
                        model=model,
                        system_prompt=system_prompt,
                        context_cache_id=getattr(cache_resp, "cache_id", None),
                    )
                    db.add(session_row)
                    await db.commit()

        # -------------------------------------------------------------------
        # ChatSession 기반 호출 (토큰 스트리밍 only)
        # -------------------------------------------------------------------
        if session_row is not None:
            # ChatSession 기반 (이미지 포함 가능)
            chat_obj = get_chat(session_row)

            # 사용자 파트 구성
            parts: list[genai.Part] = []
            if image_parts:
                parts.extend(image_parts)  # type: ignore[arg-type]
            parts.append(genai.Part(text=question))

            commentary_iter = chat_obj.send_message_stream(parts)
        else:
            # 레거시 텍스트 파이프라인 (이미지 미지원)
            # 1차 호출: JSON 구조 ------------------------------------
            json_text = await llm_service.response_completion(
                messages,
                model=model,
                
                user_id=user_id,
                plan_tier=plan_tier,
                stream=False,
                prompt_vars=prompt_vars or None,
            )

            # ------------------ JSON 검증 ---------------------------
            try:
                structured_obj = json.loads(json_text)
                # jsonschema.validate(instance=structured_obj, schema=schema)  # TODO: validate schema properly
            except Exception as e:
                # Validation 실패 시 사용자에게 에러 전달
                raise ValueError("LLM returned invalid JSON structure") from e

            # 2차 호출: commentary 스트리밍 ------------------------------
            commentary_iter = llm_service.response_completion(
                messages,
                model=model,
                
                user_id=user_id,
                plan_tier=plan_tier,
                stream=True,
                prompt_vars=prompt_vars or None,
            )

        return session_row, commentary_iter  # returning tuple
            yield {"event": "json", "data": json_text}
            async for token in commentary_iter:  # type: ignore[async-for-over-sync]
                yield {"event": "token", "data": token}

        return _combined_iter() 