from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship

from .plan_tier import PlanTier
from .user import User


class UserPlan(SQLModel, table=True):
    """사용자별 활성 요금제."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(foreign_key="user.google_sub", index=True)
    plan_tier_id: int = Field(foreign_key="plan_tier.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    user: Optional[User] = Relationship(back_populates="plans")
    plan: Optional[PlanTier] = Relationship(back_populates="users") 