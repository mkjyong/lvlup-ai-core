from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ChatMessage(SQLModel, table=True):
    """사용자 질문/답변 히스토리."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(index=True)
    question: str
    answer: str
    game: str = Field(default="generic", index=True, max_length=10)  # 대화창 구분 (generic|lol|pubg)
    created_at: datetime = Field(default_factory=datetime.utcnow) 