"""텍스트 정제(clean) 유틸리티.

기능:
1. HTML 태그 제거
2. 이모지, URL, Markdown 코드블럭 제거
3. 중복 공백 축소
4. 선택적 불용어 제거
5. 언어 감지(ko/en) 실패 시 그대로 반환
"""

import re
from html import unescape
from typing import List
import os
from pathlib import Path

# 언어 감지
try:
    from langdetect import detect
except ImportError:  # pragma: no cover
    detect = None  # type: ignore

# Emoji
import re
import unicodedata

EMOJI_PATTERN = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)

# URL pattern
URL_PATTERN = re.compile(r"https?://\S+")

from bs4 import BeautifulSoup

__all__ = ["clean_text"]

# -------------------------
# Stopword handling
# -------------------------
_DEFAULT_STOPWORDS = [
    # English common
    "the",
    "a",
    "an",
    "and",
    "of",
    "in",
    "to",
    # Korean common
    "이",
    "그",
    "저",
    "것",
    "등",
    "및",
    "수",
    "들",
]

# Allow external stopword file via env
_STOPWORD_FILE = os.getenv("STOPWORD_FILE")  # path to newline-separated file


def _load_stopwords() -> List[str]:
    if _STOPWORD_FILE and Path(_STOPWORD_FILE).exists():
        try:
            return [line.strip() for line in Path(_STOPWORD_FILE).read_text().splitlines() if line.strip()]
        except Exception:  # noqa: BLE001
            pass
    return _DEFAULT_STOPWORDS


STOPWORDS: List[str] = _load_stopwords()


def _strip_html(text: str) -> str:
    return BeautifulSoup(text, "html.parser").get_text(" ")


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _remove_stopwords(text: str) -> str:
    pattern = re.compile(r"\\b(" + "|".join(map(re.escape, STOPWORDS)) + r")\\b", re.IGNORECASE)
    return pattern.sub("", text)


# New helpers
CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")


def _remove_noise(text: str) -> str:
    """Emoji, URL, codeblock 제거."""
    text = EMOJI_PATTERN.sub("", text)
    text = URL_PATTERN.sub("", text)
    text = CODE_BLOCK_PATTERN.sub("", text)
    return text


# ----------------------------------------------
# Public API
# ----------------------------------------------


def clean_text(
    raw: str,
    *,
    remove_stopwords: bool = False,
    require_lang: List[str] | None = None,
) -> str:
    """HTML → 텍스트, 노이즈 제거, 공백 정규화, 선택적 불용어 제거.

    Args:
        raw: 원본 HTML/텍스트
        remove_stopwords: 불용어 제거 여부
        require_lang: 허용 언어 코드 목록(예: ["ko", "en"]) – langdetect 미설치 시 무시
    """

    text = unescape(raw)
    text = _strip_html(text)
    text = _remove_noise(text)
    text = _normalize_whitespace(text)

    # 언어 확인
    if require_lang and detect is not None:
        try:
            lang = detect(text)
            if lang not in require_lang:
                return ""  # 필터링: 허용되지 않은 언어
        except Exception:  # noqa: BLE001
            pass

    if remove_stopwords:
        text = _remove_stopwords(text)
        text = _normalize_whitespace(text)
    return text 