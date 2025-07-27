"""문서 품질 점수 계산 모듈."""

from __future__ import annotations

import math
from collections import Counter
from typing import List

# Optional: datasketch MinHash 기반 유사도 계산
try:
    from datasketch import MinHash
except ImportError:  # pragma: no cover
    MinHash = None  # type: ignore

# Fallback 경고 로그용
import logging

logger = logging.getLogger(__name__)

__all__ = ["compute_score"]


def _keyword_weight(text: str, keywords: List[str]) -> float:
    if not keywords:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return hits / len(keywords)


def _minhash(text: str, num_perm: int = 128):
    """Generate MinHash object from text (whitespace tokenization)."""
    assert MinHash is not None  # type: ignore [comparison-overlap]
    m = MinHash(num_perm=num_perm)
    for token in text.split():
        m.update(token.encode())
    return m


def _novelty_weight(text: str, existing_texts: List[str] | None = None) -> float:
    """1.0(완전 새로움) ~ 0.0(완전 중복) 반환."""

    # datasketch가 없으면 과거 fallback 로직 사용
    if MinHash is None:
        if not existing_texts:
            return 1.0
        words = set(text.split())
        overlap_counts = []
        for et in existing_texts:
            if not et:
                continue
            overlap = words.intersection(et.split())
            overlap_counts.append(len(overlap) / max(1, len(words)))
        if not overlap_counts:
            return 1.0
        avg_overlap = sum(overlap_counts) / len(overlap_counts)
        return 1.0 - avg_overlap

    # MinHash 기반 Jaccard 유사도 → 1 - sim = novelty
    if not existing_texts:
        return 1.0

    target_mh = _minhash(text)

    sims = []
    for et in existing_texts:
        if not et:
            continue
        mh = _minhash(et)
        sims.append(target_mh.jaccard(mh))

    if not sims:
        return 1.0

    max_sim = max(sims)  # 가장 유사한 문서 기준
    novelty = 1.0 - max_sim
    return round(novelty, 4)


def _length_weight(text: str, min_len: int = 100, max_len: int = 1500) -> float:
    l = len(text)
    if l < min_len:
        return l / min_len  # 선형 상승
    if l > max_len:
        return max(0.0, 1 - (l - max_len) / max_len)
    return 1.0


def compute_score(
    text: str,
    *,
    keywords: List[str] | None = None,
    existing_texts: List[str] | None = None,
    llm_relevance: float | None = None,
) -> float:
    """전략 노트/자막 텍스트의 품질 점수를 반환.

    Args:
        text: 평가 대상 텍스트.
        keywords: 게임별 핵심 키워드 목록.
        existing_texts: 중복 검사용 기존 텍스트 샘플.
        llm_relevance: LLM 분류 점수(0~1). 주어지지 않으면 0.5 기본.
    """
    from data_ingest.common import config as _cfg  # local import to avoid circular

    kw_weight = _keyword_weight(text, keywords or [])
    novelty_weight = _novelty_weight(text, existing_texts)
    length_weight = _length_weight(text)
    llm_weight = llm_relevance if llm_relevance is not None else 0.5

    score = (
        _cfg.QUALITY_WEIGHT_KEYWORD * kw_weight
        + _cfg.QUALITY_WEIGHT_NOVELTY * novelty_weight
        + _cfg.QUALITY_WEIGHT_LENGTH * length_weight
        + _cfg.QUALITY_WEIGHT_LLM * llm_weight
    )
    # 소수점 4자리 반올림
    return round(score, 4) 