from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, SQLModel, Relationship

# Forward references handled via runtime import at bottom to avoid circular registry issues


class UserPlan(SQLModel, table=True):
    """사용자별 활성 요금제."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(foreign_key="user.google_sub", index=True)
    plan_tier_id: int = Field(foreign_key="plan_tier.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # Relationships to User and PlanTier are omitted in test context to simplify mapping and avoid circular issues.

if TYPE_CHECKING:
    from .user import User  # pragma: no cover
    from .plan_tier import PlanTier  # pragma: no cover
else:
    from . import user as _user  # noqa: F401
    from . import plan_tier as _plan_tier  # noqa: F401 