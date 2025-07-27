"""User 모델 정의."""
from __future__ import annotations

from typing import Optional

from datetime import datetime

from app.services.security import encrypt_email, decrypt_email
from sqlmodel import Field, SQLModel, Relationship


class User(SQLModel, table=True):
    """사용자 테이블."""
    google_sub: str = Field(primary_key=True)
    email_enc: str = Field(nullable=False, alias="email")
    avatar: Optional[str] = None
    plan_tier: str = "free"
    # === Referral System ===
    # 개인별 고유 레퍼럴 코드 및 적립된 할인권(=추천인 수)
    referral_code: str | None = Field(default=None, index=True, sa_column_kwargs={"unique": True})
    referral_credits: int = 0

    # 추천인 Relationship – 역참조
    referrals: list["Referral"] = Relationship(back_populates="referrer")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    plans: list["UserPlan"] = Relationship(back_populates="user")
    game_accounts: list["GameAccount"] = Relationship(back_populates="user")

    @property
    def email(self) -> str:  # type: ignore[override]
        return decrypt_email(self.email_enc)

    @email.setter
    def email(self, value: str) -> None:  # type: ignore[override]
        self.email_enc = encrypt_email(value) 