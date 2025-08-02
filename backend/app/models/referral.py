from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, SQLModel, Relationship


class Referral(SQLModel, table=True):
    __tablename__ = "referral"
    """유저 초대(레퍼럴) 기록."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # 추천인 / 피추천인
    referrer_google_sub: str = Field(foreign_key="user.google_sub", index=True)
    referred_google_sub: str = Field(foreign_key="user.google_sub", index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 첫 결제 시점에 채워짐(보상 지급 여부)
    rewarded_at: Optional[datetime] = None

    # SQLModel Relationship 설정 (지연 참조 해소를 위해 문자열 사용)
    # Relationships omitted in test context to avoid mapper initialization issues.

# Runtime import to register User model for Relationship resolution
if TYPE_CHECKING:
    from .user import User  # pragma: no cover
else:
    from . import user as _user  # noqa: F401 