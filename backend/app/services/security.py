"""보안 유틸리티 - 이메일 암호화/복호화, 로그 마스킹."""
import base64
import re
from typing import Callable

from cryptography.fernet import Fernet, InvalidToken
import structlog

from app.config import get_settings

settings = get_settings()

if not settings.EMAIL_ENC_KEY:
    raise RuntimeError("EMAIL_ENC_KEY 환경변수가 설정되지 않았습니다.")

_fernet = Fernet(settings.EMAIL_ENC_KEY.encode())
_logger = structlog.get_logger()


def encrypt_email(email: str) -> str:
    token = _fernet.encrypt(email.encode())
    return token.decode()


def decrypt_email(token: str) -> str:
    try:
        return _fernet.decrypt(token.encode()).decode()
    except InvalidToken as exc:
        # 평문 이메일이 저장된 경우 복호화 대신 그대로 사용
        if "@" in token:
            return token
        _logger.error("Invalid email decrypt token")
        raise exc


EMAIL_PATTERN = re.compile(r"[\w\.-]+@([\w\.-]+)\.[A-Za-z]{2,6}")
# JWT / 토큰 패턴 (대략적)
JWT_PATTERN = re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")
# Stripe / PortOne Secret Key 예시 패턴
SECRET_KEY_PATTERN = re.compile(r"(whsec_|portone_)[A-Za-z0-9]+", re.IGNORECASE)


def mask_pii(value: str) -> str:
    """문자열 내 민감 정보를 *** 로 마스킹."""

    value = EMAIL_PATTERN.sub("***@***", value)
    value = JWT_PATTERN.sub("***.***", value)
    value = SECRET_KEY_PATTERN.sub("****", value)
    return value


def mask_pii_processor(_: Callable, __, event_dict):  # type: ignore[override]
    """structlog processor: PII 마스킹."""

    def _recurse(obj):
        if isinstance(obj, str):
            return mask_pii(obj)
        if isinstance(obj, dict):
            return {k: _recurse(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_recurse(i) for i in obj]
        return obj

    for k, v in event_dict.items():
        event_dict[k] = _recurse(v)
    return event_dict 