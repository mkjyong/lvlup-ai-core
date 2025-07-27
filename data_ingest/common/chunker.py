"""텍스트를 슬라이딩 윈도우로 분할.

두 가지 방식 지원
1. 문자 수 기반(`sliding_window_chunks`)
2. 토큰 수 기반(`token_window_chunks`) – tiktoken 설치 시 사용
"""

from __future__ import annotations

from typing import List

from data_ingest.common import config as _cfg

# Optional tiktoken for token counting
try:
    import tiktoken
except ImportError:  # pragma: no cover
    tiktoken = None  # type: ignore

__all__ = [
    "sliding_window_chunks",
    "token_window_chunks",
    "paragraph_chunks",  # NEW
]


def sliding_window_chunks(
    text: str,
    size: int = _cfg.CHUNK_SIZE,
    overlap_ratio: float = _cfg.CHUNK_OVERLAP_RATIO,
) -> List[str]:
    """문자 길이 기반 분할.

    Args:
        text: 원본 텍스트.
        size: 각 청크 최대 문자수.
        overlap_ratio: 0~1 사이 값. 0.5 → 절반 겹침.
    Returns:
        청크 문자열 리스트.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    if not 0 <= overlap_ratio < 1:
        raise ValueError("overlap_ratio must be 0<=x<1")

    step = int(size * (1 - overlap_ratio)) or 1
    chunks: List[str] = []

    for start in range(0, len(text), step):
        chunk = text[start : start + size]
        if len(chunk) < 50:  # 50자 미만은 버린다.
            continue
        chunks.append(chunk)
    return chunks


def paragraph_chunks(
    text: str,
    min_len: int = 50,
) -> List[str]:
    """빈 줄 2개 이상을 기준으로 문단을 분리한다.

    Args:
        text: 원본 텍스트
        min_len: 필터링을 위한 최소 문단 길이(문자 수)
    Returns:
        문단 목록. `min_len` 미만 문단은 건너뛴다.
    """
    import re

    # \n{2,} (또는 공백 포함) 로 스플릿
    raw_paragraphs = re.split(r"\n\s*\n", text)
    chunks: List[str] = []
    buf = ""

    for para in raw_paragraphs:
        p = para.strip()
        if not p:
            continue
        # 짧은 문단을 이전 버퍼와 합친다.
        if len(p) < min_len:
            buf = f"{buf} {p}".strip()
            continue
        if buf:
            if len(buf) >= min_len:
                chunks.append(buf)
            buf = ""
        chunks.append(p)

    # 남은 버퍼 flush
    if buf and len(buf) >= min_len:
        chunks.append(buf)

    return chunks


def token_window_chunks(
    text: str,
    tokens: int = 400,  # UPDATED default size
    overlap_ratio: float = 0.2,  # 80 token overlap by default
    model: str = "cl100k_base",
) -> List[str]:
    """토큰 수 기준 슬라이딩 윈도우 분할.

    Requires `tiktoken`.
    """
    if tiktoken is None:
        raise ImportError("tiktoken 패키지를 설치하세요: pip install tiktoken")

    enc = tiktoken.get_encoding(model)
    ids = enc.encode(text)
    step = int(tokens * (1 - overlap_ratio)) or 1
    chunks: List[str] = []
    for start in range(0, len(ids), step):
        sub = ids[start : start + tokens]
        if len(sub) < 20:  # 적어도 20 token
            continue
        chunks.append(enc.decode(sub))
    return chunks 