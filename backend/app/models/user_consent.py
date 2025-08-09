"""사용자 약관/개인정보 동의 이력."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UserConsent(SQLModel, table=True):
    __tablename__ = "user_consent"

    # User.google_sub 와 동일 키 사용
    google_sub: str = Field(primary_key=True, index=True)
    terms_accepted_at: Optional[datetime] = None
    privacy_accepted_at: Optional[datetime] = None


