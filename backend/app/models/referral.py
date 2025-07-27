from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship


class Referral(SQLModel, table=True):
    """유저 초대(레퍼럴) 기록."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # 추천인 / 피추천인
    referrer_google_sub: str = Field(foreign_key="user.google_sub", index=True)
    referred_google_sub: str = Field(foreign_key="user.google_sub", index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 첫 결제 시점에 채워짐(보상 지급 여부)
    rewarded_at: Optional[datetime] = None

    # SQLModel Relationship 설정 (지연 참조 해소를 위해 문자열 사용)
    referrer: Optional["User"] = Relationship(back_populates="referrals", sa_relationship_kwargs={"foreign_keys": "[Referral.referrer_google_sub]"})
    referred: Optional["User"] = Relationship(sa_relationship_kwargs={"foreign_keys": "[Referral.referred_google_sub]"}) 