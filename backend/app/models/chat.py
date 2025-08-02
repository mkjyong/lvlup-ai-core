from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"
    """사용자 질문/답변 히스토리."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(index=True)
    session_id: str | None = Field(default=None, foreign_key="chat_session.id", index=True)
    question: str
    answer: str
    game: str = Field(default="generic", index=True, max_length=10)  # 대화창 구분 (generic|lol|pubg)
    created_at: datetime = Field(default_factory=datetime.utcnow) 