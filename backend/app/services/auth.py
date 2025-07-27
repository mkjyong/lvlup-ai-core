"""인증·권한 비즈니스 로직."""
from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt
# Email/password 기능 제거로 Passlib 미사용. 추후 필요 시 복구 가능.
# from passlib.context import CryptContext
# from sqlmodel import select

from app.config import get_settings
# from app.exceptions import AIError
# from app.models.user import User
# from app.models.db import get_session

# Google OAuth 단일 플로우이므로 비밀번호 검증 로직 제거
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


# === JWT Helpers ===

def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


# Refresh Token Helpers

def create_refresh_token(data: dict[str, Any], expires_days: int | None = None) -> str:
    refresh_claims = data.copy()
    exp = datetime.utcnow() + timedelta(days=expires_days or settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_claims.update({"exp": exp, "typ": "refresh"})
    return jwt.encode(refresh_claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_refresh_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("typ") != "refresh":
            raise JWTError("Invalid token type")
        return payload
    except JWTError as exc:
        raise JWTError("Invalid refresh token") from exc


# 아래 함수들은 이메일/비밀번호 플로우 제거로 비활성화
# 유지가 필요하면 NotImplementedError 를 발생시켜 추후 구현 가능성을 열어둔다.

def verify_password(*_args, **_kwargs):  # pragma: no cover
    raise NotImplementedError("Google OAuth 전용 서비스에서는 사용하지 않습니다.")


def get_password_hash(*_args, **_kwargs):  # pragma: no cover
    raise NotImplementedError("Google OAuth 전용 서비스에서는 사용하지 않습니다.")


async def authenticate_user(*_args, **_kwargs):  # pragma: no cover
    return None


async def create_user(*_args, **_kwargs):  # pragma: no cover
    raise NotImplementedError("Google OAuth 전용 서비스에서는 사용하지 않습니다.") 