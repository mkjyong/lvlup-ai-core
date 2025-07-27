"""게임 자산(챔피언, 아이템, 무기 등) 이미지 캐시 테이블."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class GameAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game: str = Field(index=True)  # e.g., lol, pubg
    type: str = Field(index=True)  # e.g., champion, item, weapon
    key: str = Field(index=True)   # canonical name or id
    image_url: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        # composite uniqueness
        {
            "sqlite_autoincrement": True,
        },
    ) 