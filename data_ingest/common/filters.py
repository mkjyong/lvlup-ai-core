from __future__ import annotations
"""Pre-filter utilities to quickly discard low-value texts.

- 빠른 키워드 매칭으로 LLM 호출 비용 절감
- 키워드 목록은 환경변수 `KEYWORD_FILE`(YAML) 로부터 로드하며, 없으면 빈 목록
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import List

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from data_ingest.common.logger import logger

_KEYWORD_FILE = os.getenv("KEYWORD_FILE")  # ex: /etc/keywords.yaml


@lru_cache(maxsize=1)
def _load_mapping() -> dict[str, List[str]]:
    if _KEYWORD_FILE is None or yaml is None:
        return {}
    path = Path(_KEYWORD_FILE)
    if not path.exists():
        logger.warning("KEYWORD_FILE %s not found", path)
        return {}
    try:
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            raise ValueError("Keyword YAML must be a mapping")
        return {k: [str(x).lower() for x in v] for k, v in data.items() if isinstance(v, list)}
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load keyword file: %s", exc)
        return {}


def get_keywords(source: str) -> List[str]:
    """Return keyword list for the given source."""
    return _load_mapping().get(source, [])


def fast_keyword_pass(text: str, keywords: List[str]) -> bool:
    """Return True if any keyword appears in text (case-insensitive).
    If keyword list empty → always True.
    """
    if not keywords:
        return True
    lower_text = text.lower()
    return any(kw.lower() in lower_text for kw in keywords) 