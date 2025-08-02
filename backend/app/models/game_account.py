from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import UniqueConstraint as SAUniqueConstraint
from sqlmodel import Field, SQLModel, Relationship

class GameAccount(SQLModel, table=True):
    __tablename__ = "game_account"
    """유저의 게임별 계정 ID 저장."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(foreign_key="user.google_sub", nullable=False, index=True)
    game: str = Field(nullable=False, index=True)
    account_id: str = Field(nullable=False)
    region: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship omitted in test context

    # Runtime import to ensure User model is registered for this relationship
    if TYPE_CHECKING:
        from .user import User  # pragma: no cover
    else:
        from . import user as _user  # noqa: F401

    __table_args__ = (
        SAUniqueConstraint("user_google_sub", "game", name="uq_user_game_account"),
    ) 