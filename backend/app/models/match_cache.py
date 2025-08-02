from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel, Relationship

class MatchCache(SQLModel, table=True):
    __tablename__ = "match_cache"
    """외부 API에서 가져온 원본 매치/전적 JSON 캐시."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(foreign_key="user.google_sub", nullable=False, index=True)
    game: str = Field(nullable=False, index=True)
    fetched_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    raw: dict = Field(sa_column=Column(JSON))
    ttl: datetime

    # Relationship omitted in test context 