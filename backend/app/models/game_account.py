from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint as SAUniqueConstraint
from sqlmodel import Field, SQLModel, Relationship

class GameAccount(SQLModel, table=True):
    """유저의 게임별 계정 ID 저장."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(foreign_key="user.google_sub", nullable=False, index=True)
    game: str = Field(nullable=False, index=True)
    account_id: str = Field(nullable=False)
    region: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship back to User
    user: "User" = Relationship(back_populates="game_accounts")

    __table_args__ = (
        SAUniqueConstraint("user_google_sub", "game", name="uq_user_game_account"),
    ) 