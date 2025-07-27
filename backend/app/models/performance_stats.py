from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel, Relationship

class PerformanceStats(SQLModel, table=True):
    """주간/월간 집계된 게임 성과 지표."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(foreign_key="user.google_sub", nullable=False, index=True)
    game: str = Field(nullable=False, index=True)
    period: str = Field(nullable=False, index=True)  # 'weekly' | 'monthly'
    period_start: date
    period_end: date
    metrics: dict = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship() 