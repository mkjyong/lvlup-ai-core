from __future__ import annotations
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy.orm import Mapped

from sqlmodel import Field, SQLModel, Relationship


class PlanTier(SQLModel, table=True):
    """요금제(플랜) 메타데이터 모델."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price_usd: float = 0.0
    prompt_limit: int = 0  # 1회 요청 최대 프롬프트 토큰
    completion_limit: int = 0  # 1회 응답 최대 토큰
    weekly_request_limit: int = 0
    monthly_request_limit: int = 0
    special_monthly_request_limit: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # SQLAlchemy 2.x / SQLModel requires typing.List for forward refs using annotations future
    users: list["UserPlan"] = Relationship(back_populates="plan")

# Runtime import to populate SQLAlchemy registry
if TYPE_CHECKING:
    from .user_plan import UserPlan  # pragma: no cover
else:
    from . import user_plan  # noqa: F401 