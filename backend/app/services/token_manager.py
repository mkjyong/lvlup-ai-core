"""Token window 관리 유틸."""
from typing import List, Dict, Any

import tiktoken

ENCODER = tiktoken.get_encoding("cl100k_base")

MAX_CONTEXT_TOKENS = 4096  # gpt-4o context length
RESERVED_COMPLETION_TOKENS = 512
TRIMMED_TOKENS = MAX_CONTEXT_TOKENS - RESERVED_COMPLETION_TOKENS


def message_tokens(msg: Dict[str, Any]) -> int:
    # 기본 텍스트 토큰(역할/콘텐츠 오버헤드 4 포함)
    tokens = len(ENCODER.encode(msg["content"])) + 4

    # 이미지 토큰 가산: `image_count` 키 또는 `images` 리스트 존재 시 반영
    # Gemini 과금 기준이 아직 공식화되지 않았으므로 보수적으로 1장당 512 tokens 가정
    image_cnt = 0
    if "image_count" in msg and isinstance(msg["image_count"], int):
        image_cnt = msg["image_count"]
    elif "images" in msg and isinstance(msg["images"], list):
        image_cnt = len(msg["images"])

    tokens += 150 * image_cnt
    return tokens


def trim_messages(messages: List[Dict[str, str]], max_context_tokens: int = TRIMMED_TOKENS) -> List[Dict[str, str]]:
    """오래된 메시지를 제거해 context 토큰 한도 내로 자른다."""
    total = 0
    trimmed: List[Dict[str, str]] = []
    # Reverse iterate to keep latest messages
    for msg in reversed(messages):
        t = message_tokens(msg)
        if total + t > max_context_tokens:
            break
        trimmed.append(msg)
        total += t
    return list(reversed(trimmed)) 