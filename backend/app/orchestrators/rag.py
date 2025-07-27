"""Retrieval-Augmented Generation orchestration layer."""
from dataclasses import dataclass
from typing import List, Optional

from app.services import (
    prompt as prompt_service,
    llm as llm_service,
    chat as chat_service,
    performance as perf_service,
)
from app.config import MODEL_CATEGORY
from app.services.token_manager import TRIMMED_TOKENS, message_tokens
# NEW: schema imports
from app.schemas import coach as coach_schemas
import json, jsonschema


def select_model(game: Optional[str]) -> str:
    """게임 타입에 따라 사용할 LLM 모델 결정."""
    if game and game.lower() in {"lol", "pubg"}:
        return "o4-mini"
    return "gpt-4o-mini"


@dataclass
class RagPipeline:
    """Main RAG orchestration pipeline."""

    top_k: int = 5  # RAG 문서 개수 (고정, 2025-07 변경)

    async def run(
        self,
        *,
        question: str,
        user_id: str,
        plan_tier: str = "free",
        game: Optional[str] = None,
        prompt_type: Optional[str] = None,
        include_history: bool = True,
        history_limit: int = 10,
    ) -> str:
        """Execute full RAG flow and return answer string."""
        _top_k = self.top_k

        # --- 요금제별 히스토리 제한 --------------------------------
        if plan_tier == "free":
            history_limit = min(history_limit, 5)  # 최신 2쌍만 유지
            _top_k = 3

        # Vector Store용 metadata 필터 ------------------------------
        filters = {"game": game.lower()} if game else None

        # 2) 게임별 Player Stats 확보 --------------------------------
        player_stats_block: str | None = None
        if game and user_id:
            try:
                from app.models.db import get_session  # local import to avoid circular

                async with get_session() as session:
                    stats = await perf_service.ensure_stats_cached(session, user_id, game)
                # 간단한 Key:Value 나열로 문자열 변환
                stats_str = "\n".join(f"- {k}: {v}" for k, v in stats.items())
                player_stats_block = f"[PlayerStats]\n{stats_str}"
            except Exception:
                # 캐시에 실패해도 계속 진행 (게임 계정 미등록 등)
                player_stats_block = None

        # 3) Render system prompt (게임별 템플릿)
        ptype = prompt_type or prompt_service.PromptType.generic.name
        try:
            prompt_enum = prompt_service.PromptType[ptype]
        except KeyError:
            prompt_enum = prompt_service.PromptType.generic

        # 3) Determine reusable prompt ID (Responses API) -------------------
        prompt_id = prompt_service.get_prompt_id(prompt_enum)

        if not prompt_id:
            raise RuntimeError(
                "Prompt ID for type '%s' is not configured. Set the env variable first." % prompt_enum.name
            )

        # 4) Build prompt variables & message -------------------------
        prompt_vars: dict[str, str] = {}

        if player_stats_block:
            prompt_vars["player_stats"] = player_stats_block

        if include_history and user_id:
            history = await chat_service.list_chat_history(user_id, history_limit, game)
            # oldest → newest 로 정렬, 간단히 assistant answer만 이어붙임
            conv_snippets = "\n\n".join(h.answer for h in reversed(history))
            if conv_snippets:
                prompt_vars["conversation_snippets"] = conv_snippets

        # 메시지는 현재 질문만 포함
        messages: List[dict[str, str]] = [{"role": "user", "content": question}]


        # 6) Determine model
        model = select_model(game)

        # 7) Call Responses API 래퍼 -----------------------------------
        answer = await llm_service.response_completion(
            messages,
            model=model,
            prompt_ids=[prompt_id] if prompt_id else None,
            user_id=user_id,
            plan_tier=plan_tier,
            top_k=_top_k,
            filters=filters,
            prompt_vars=prompt_vars or None,
        )

        return answer 

# -------------------------------------------------------------------
# NEW helper and stream method
# -------------------------------------------------------------------

    def _select_schema(self, game: Optional[str]):
        """게임별 JSON 스키마 선택."""
        if game:
            gl = game.lower()
            if gl == "lol":
                return coach_schemas.lol_coach_schema
            if gl == "pubg":
                return coach_schemas.pubg_coach_schema
        return coach_schemas.generic_coach_schema

    async def run_structured_and_stream(
        self,
        *,
        question: str,
        user_id: str,
        plan_tier: str = "free",
        game: Optional[str] = None,
        prompt_type: Optional[str] = None,
        include_history: bool = True,
        history_limit: int = 10,
    ):
        """1) JSON 구조 응답 → 2) 스트리밍 commentary 토큰 순으로 async generator 리턴."""

        # 메시지 공통 부분 구성 (player stats, history 등) -------------------
        _top_k = self.top_k if plan_tier != "free" else 3

        filters = {"game": game.lower()} if game else None

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

        prompt_id = prompt_service.get_prompt_id(prompt_enum)
        if not prompt_id:
            raise RuntimeError("Prompt ID for type '%s' is not configured. Set the env variable first." % prompt_enum.name)

        prompt_vars: dict[str, str] = {}
        if player_stats_block:
            prompt_vars["player_stats"] = player_stats_block

        if include_history and user_id:
            history = await chat_service.list_chat_history(user_id, history_limit, game)
            conv_snippets = "\n\n".join(h.answer for h in reversed(history))
            if conv_snippets:
                prompt_vars["conversation_snippets"] = conv_snippets

        messages: List[dict[str, str]] = [{"role": "user", "content": question}]

        model = select_model(game)

        # 1차 호출: JSON 구조 ------------------------------------------------
        schema = self._select_schema(game)
        json_text = await llm_service.response_completion(
            messages,
            model=model,
            prompt_ids=[prompt_id],
            user_id=user_id,
            plan_tier=plan_tier,
            top_k=_top_k,
            filters=filters,
            response_format={"type": "json_object", "schema": schema},
            stream=False,
            prompt_vars=prompt_vars or None,
        )

        # ------------------ JSON 검증 ---------------------------
        try:
            structured_obj = json.loads(json_text)
            jsonschema.validate(instance=structured_obj, schema=schema)
        except Exception as e:
            # Validation 실패 시 사용자에게 에러 전달
            raise ValueError("LLM returned invalid JSON structure") from e

        # 2차 호출: commentary 스트리밍 ------------------------------------
        commentary_iter = llm_service.response_completion(
            messages,
            model=model,
            prompt_ids=[prompt_id],
            user_id=user_id,
            plan_tier=plan_tier,
            top_k=_top_k,
            filters=filters,
            stream=True,
            prompt_vars=prompt_vars or None,
        )

        async def _combined_iter():
            yield {"event": "json", "data": json_text}
            async for token in commentary_iter:  # type: ignore[async-for-over-sync]
                yield {"event": "token", "data": token}

        return _combined_iter() 