"""User 모델 정의."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING, List

from datetime import datetime

from app.services.security import encrypt_email, decrypt_email
from sqlmodel import Field, SQLModel, Relationship


class User(SQLModel, table=True):
    """사용자 테이블."""
    google_sub: str = Field(primary_key=True)
    email_enc: str = Field(nullable=False, alias="email")
    avatar: Optional[str] = None
    plan_tier: str = "free"
    billing_key: str | None = None  # PortOne BillingKey (토큰화 결제수단)
    # === Referral System ===
    # 개인별 고유 레퍼럴 코드 및 적립된 할인권(=추천인 수)
    referral_code: str | None = Field(default=None, index=True, sa_column_kwargs={"unique": True})
    referral_credits: int = 0


    # Relationships omitted in test context to avoid mapper initialization issues.
    created_at: datetime = Field(default_factory=datetime.utcnow)

    if TYPE_CHECKING:
        from .referral import Referral  # pragma: no cover
        from .user_plan import UserPlan  # pragma: no cover
        from .game_account import GameAccount  # pragma: no cover
    else:
        from . import referral as _referral  # noqa: F401
        from . import user_plan as _user_plan  # noqa: F401
        from . import game_account as _game_account  # noqa: F401

    @property
    def email(self) -> str:  # type: ignore[override]
        return decrypt_email(self.email_enc)

    @email.setter
    def email(self, value: str) -> None:  # type: ignore[override]
        self.email_enc = encrypt_email(value) 