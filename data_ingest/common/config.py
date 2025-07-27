"""Runtime configuration resolved from 환경변수/env file.

모든 값은 모듈 import 시 1회 평가되므로, 테스트 시 `importlib.reload` 필요.
"""

from __future__ import annotations

import os

# --------------------------------------------------
# Quality Score Weights & Threshold
# --------------------------------------------------

QUALITY_WEIGHT_KEYWORD: float = float(os.getenv("QUALITY_WEIGHT_KEYWORD", "0.4"))
QUALITY_WEIGHT_NOVELTY: float = float(os.getenv("QUALITY_WEIGHT_NOVELTY", "0.3"))
QUALITY_WEIGHT_LENGTH: float = float(os.getenv("QUALITY_WEIGHT_LENGTH", "0.2"))
QUALITY_WEIGHT_LLM: float = float(os.getenv("QUALITY_WEIGHT_LLM", "0.1"))

# 임계값(해당 점수 이상만 임베딩)
MIN_QUALITY_SCORE: float = float(os.getenv("MIN_QUALITY_SCORE", "0.75"))

# --------------------------------------------------
# Chunker 기본 설정
# --------------------------------------------------

CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "220"))
CHUNK_OVERLAP_RATIO: float = float(os.getenv("CHUNK_OVERLAP_RATIO", "0.5"))

# --------------------------------------------------
# Embedding 설정
# --------------------------------------------------

EMBED_BATCH_SIZE: int = int(os.getenv("EMBED_BATCH_SIZE", "16")) 