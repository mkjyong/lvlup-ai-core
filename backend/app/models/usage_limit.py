from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UsageLimit(SQLModel, table=True):
    __tablename__ = "usage_limit"
    """사용자 기간별 사용량 집계 스냅샷."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(index=True)
    plan_tier: str = Field(index=True)
    period_start: datetime
    period_end: datetime
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow) 