"""RAG 검색 & Answer 생성 서비스."""
from typing import List, Dict, Any

from app.services import prompt as prompt_service
import os
from dataclasses import dataclass
try:
    from openai import AsyncOpenAI  # type: ignore
except ImportError:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore


# -------------------------------------------------------------
# Environment-based feature flag
# -------------------------------------------------------------

USE_OPENAI_VECTOR: bool = os.getenv("USE_OPENAI_VECTOR", "false").lower() == "true"
VECTOR_STORE_ID: str | None = os.getenv("OPENAI_VECTOR_STORE_ID")


# -------------------------------------------------------------
# Thin document wrapper so that orchestrator can treat both
# pgvector rows and OpenAI search results identically.
# -------------------------------------------------------------


@dataclass
class _SimpleDoc:  # noqa: D401
    text: str
    metadata: dict | None = None


# -------------------------------------------------------------
# Helper: OpenAI Vector search
# -------------------------------------------------------------



# -------------------------------------------------------------
# NEW: Helper – Vector Store query API (preferred)
# -------------------------------------------------------------


async def _retrieve_documents_vectorstore(
    query: str,
    top_k: int = 5,
    filters: dict | None = None,
):  # noqa: D401
    """Search OpenAI Vector Store using the *query* endpoint.

    This implementation follows the official documentation:
    https://platform.openai.com/docs/api-reference/vector-stores/retrieve

    It supports metadata filtering via the ``filters`` argument and gracefully
    falls back to an empty list on any runtime error so that the orchestrator
    can decide the next action.
    """

    if AsyncOpenAI is None or not VECTOR_STORE_ID:
        return []

    client = AsyncOpenAI()

    try:
        params: dict[str, Any] = {
            "vector_store_id": VECTOR_STORE_ID,
            "query": query,
            "top_k": top_k,
        }
        if filters:
            params["filter"] = filters

        # NOTE: Current SDK (>=1.23) exposes ``beta.vector_stores.query``.
        resp = await client.beta.vector_stores.query(**params)  # type: ignore[arg-type]

        docs: list[_SimpleDoc] = []
        for item in resp.data:  # type: ignore[attr-defined]
            # Official response spec may evolve; attempt to extract common fields.
            text: str = item.get("text") or item.get("content") or ""
            meta: dict | None = item.get("metadata")  # type: ignore[assignment]
            if text:
                docs.append(_SimpleDoc(text=text, metadata=meta))

        return docs[:top_k]
    except Exception:  # noqa: BLE001
        # Fall back silently – orchestrator will handle empty result.
        return []


async def retrieve_documents(
    query: str,
    top_k: int = 5,
    *,
    filters: Dict[str, Any] | None = None,
) -> List[_SimpleDoc]:

    # 1) Preferred: Vector Store native query API
    docs = await _retrieve_documents_vectorstore(query, top_k=top_k, filters=filters)

    return docs


async def answer_question(
    question: str,
    *,
    user_id: str | None = None,
    plan_tier: str = "free",
    game: str | None = None,
    prompt_type: str | None = None,
) -> str:
    """(Deprecated) – Use RagPipeline instead. Delegates call."""

    from app.orchestrators.rag import RagPipeline

    pipeline = RagPipeline()

    return await pipeline.run(
        question=question,
        user_id=user_id or "anonymous",
        plan_tier=plan_tier,
        game=game,
        prompt_type=prompt_type,
    ) 