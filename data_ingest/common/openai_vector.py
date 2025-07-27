"""OpenAI Vector Store helper functions.

This thin wrapper centralises interaction with the OpenAI Vector Store API so
that the rest of the ingestion pipeline can remain vendor-agnostic.

Key responsibilities
-------------------
1. Ensure a target Vector Store exists (create lazily if missing).
2. Provide a simple ``upsert_text`` helper that uploads raw text as a file and
   waits until the batch is indexed.
3. Expose a singleton OpenAI client to avoid re-creating HTTP sessions.

Environment variables
---------------------
OPENAI_API_KEY           – API key
OPENAI_VECTOR_STORE_ID   – Target store identifier. If the store does not
                           exist it will be created automatically.
EMBEDDING_MODEL          – Embedding model name (default: text-embedding-3-small)
"""

from __future__ import annotations

import os
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from openai import OpenAI, BadRequestError  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "openai 패키지가 설치되지 않았습니다. backend/requirements.txt 를 확인하세요.") from exc

__all__ = ["ensure_store", "upsert_text", "client", "VECTOR_STORE_ID"]

# ---------------------------------------------------------------------------
# Global client & config
# ---------------------------------------------------------------------------

client = OpenAI()

# 환경 변수 ------------------------------------------------------------
VECTOR_STORE_ID: str | None = os.getenv("OPENAI_VECTOR_STORE_ID")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

if not VECTOR_STORE_ID:
    raise EnvironmentError("OPENAI_VECTOR_STORE_ID 환경변수가 설정되어 있지 않습니다.")

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _fmt_title(store_id: str) -> str:
    """Generate a human-readable title for the vector store (once)."""
    return f"lvlup-core:{store_id}"


def ensure_store() -> str:  # noqa: D401
    """Return a ready-to-use vector store id – create the store on first call."""
    global VECTOR_STORE_ID  # pylint: disable=global-statement

    # Already ensured
    if VECTOR_STORE_ID:
        return VECTOR_STORE_ID

    store_id_env = os.getenv("OPENAI_VECTOR_STORE_ID")
    if store_id_env:
        VECTOR_STORE_ID = store_id_env
        return VECTOR_STORE_ID

    # Auto-create a store with generated id
    from uuid import uuid4

    VECTOR_STORE_ID = uuid4().hex[:12]
    client.beta.vector_stores.create(
        id=VECTOR_STORE_ID,
        name=_fmt_title(VECTOR_STORE_ID),
        embedding_config={"model": EMBEDDING_MODEL},
    )
    return VECTOR_STORE_ID


async def upsert_text(doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Upload *text* to the vector store and return created ``file_id``.

    Internally we write the provided text to a temporary UTF-8 file. The file is
    uploaded through the *file_batches* endpoint which blocks until ingestion
    is complete (``create_and_poll`` helper).
    """

    vs_id = ensure_store()

    # Make sure the text is not empty / too long
    text = text.strip()
    if not text:
        raise ValueError("빈 텍스트는 업로드할 수 없습니다.")

    # Safety guard – OpenAI 파일 업로드 제한 100 MB
    if len(text.encode("utf-8")) > 100 * 1024 * 1024:
        raise ValueError("텍스트가 100MB를 초과합니다. 분할 업로드를 고려하세요.")

    # Dedent to avoid incidental indentation from triple-quoted strings
    text = textwrap.dedent(text)

    # Write to temporary file
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)

    # Build metadata – always include doc_id for traceability
    meta: Dict[str, Any] = metadata.copy() if metadata else {}
    meta.setdefault("doc_id", doc_id)

    # Upload and block until ready
    try:
        batch = client.beta.vector_stores.file_batches.create_and_poll(  # type: ignore[attr-defined]
            vector_store_id=vs_id,
            # API 현재 버전은 *file_paths* or *files* 둘 중 하나만 사용
            file_paths=[str(tmp_path)],
            metadata=meta,
        )
    except BadRequestError as exc:
        # 예: 중복 파일, rate-limit 등
        raise RuntimeError(f"Vector Store 업로드 실패: {exc}") from exc
    finally:
        # Clean up temp file – ingestion 완료 후 safe to delete
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass

    # 성공한 경우 first file id 반환
    return batch.file_ids[0] if hasattr(batch, "file_ids") and batch.file_ids else "" 