from __future__ import annotations

"""LLM 기반 텍스트 중요도(1, 0.5, 0) 분류 + SQLite 캐시.

- 중요(1.0) / 보통(0.5) / 낮음(0.0)
- 캐시 파일: ~/.cache/data_ingest/llm_relevance.sqlite
- 비동기 API(OpenAI Async) 사용.
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Optional

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None  # type: ignore

try:
    import aiosqlite
except ImportError:  # pragma: no cover
    aiosqlite = None  # type: ignore

# Optional Redis cache
try:
    import redis.asyncio as aioredis  # type: ignore
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore

from data_ingest.common.logger import logger

CACHE_DIR = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "data_ingest"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_PATH = CACHE_DIR / "llm_relevance.sqlite"

DDL = """
CREATE TABLE IF NOT EXISTS relevance (
    hash TEXT PRIMARY KEY,
    score REAL NOT NULL
);
"""


async def _init_db() -> aiosqlite.Connection:  # type: ignore[valid-type]
    assert aiosqlite is not None, "aiosqlite 패키지가 필요합니다: pip install aiosqlite"
    conn = await aiosqlite.connect(CACHE_PATH.as_posix())
    await conn.execute(DDL)
    await conn.commit()
    return conn


async def get_llm_relevance(text: str, *, model: str | None = None) -> tuple[float, str]:
    """Return (importance_score, summary) using OpenAI Responses API with JSON output.

    The OpenAI call requests a JSON object in the following format::

        {"importance": "high|medium|low", "summary": "..."}

    importance → high=1.0, medium=0.5, low=0.0
    summary    → short textual summary of the input (can be empty string).
    """

    # Fallback if OpenAI not available
    if openai is None or not os.getenv("OPENAI_API_KEY"):
        logger.debug("OpenAI unavailable – default llm_relevance (0.5, '')")
        return 0.5, ""

    h = hashlib.sha256(text.encode()).hexdigest()

    # Try Redis cache first
    redis_url = os.getenv("REDIS_URL")
    if aioredis is not None and redis_url:
        try:
            redis = aioredis.from_url(redis_url, decode_responses=True)
            cached = await redis.get(f"relevance:{h}")
            if cached is not None:
                return float(cached), ""  # cached summary not stored
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis cache error: %s", exc)

    # Fallback SQLite cache
    conn = await _init_db()
    async with conn.execute("SELECT score FROM relevance WHERE hash=?", (h,)) as cursor:
        row = await cursor.fetchone()
        if row is not None:
            return float(row[0]), ""  # cached summary not stored

    client = openai.AsyncOpenAI()

    prompt = (
        "당신은 게임 전략/패치 노트/자막 분석 전문가입니다.\n"
        "다음 텍스트의 중요도를 high/medium/low 중 하나로 판단하고, 1문장 요약을 작성하세요.\n"
        "아래 JSON 예시 형식으로만, 불필요한 문자 없이 응답하세요.\n"
        '{"importance": "high", "summary": "요약 문장"}'
    )

    try:
        import json as _json

        resp = await client.chat.completions.create(
            model=model or "gpt-4.1-nano",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text[:4000]},  # max 4k chars
            ],
            max_tokens=100,
            response_format={"type": "json_object"},
        )

        content = resp.choices[0].message.content.strip()
        data = _json.loads(content)
        importance_raw = str(data.get("importance", "medium")).lower()
        summary_raw = str(data.get("summary", "")).strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM relevance classification failed: %s", exc)
        return 0.5, ""

    mapping = {
        "high": 1.0,
        "medium": 0.5,
        "low": 0.0,
    }

    score = mapping.get(importance_raw, 0.5)
    summary = summary_raw

    # Save cache
    if aioredis is not None and redis_url:
        try:
            await redis.set(f"relevance:{h}", str(score), ex=60 * 60 * 24)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis set error: %s", exc)

    await conn.execute("INSERT OR REPLACE INTO relevance(hash, score) VALUES(?, ?)", (h, score))
    await conn.commit()
    await conn.close()

    return score, summary 