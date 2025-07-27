from __future__ import annotations

"""Referral 관련 헬퍼 로직."""
import secrets
import string

from sqlmodel import select, SQLModel

from app.models.user import User


async def generate_unique_referral_code(session) -> str:  # noqa: D401
    """충돌이 없을 때까지 6자리 대문자+숫자 코드 생성."""

    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        result = await session.exec(select(User).where(User.referral_code == code))  # type: ignore[attr-defined]
        if result.one_or_none() is None:
            return code 