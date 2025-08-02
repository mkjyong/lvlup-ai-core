"""ChatSession SQLModel – minimal metadata for Gemini chat sessions."""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_session"
    id: Optional[str] = Field(default=None, primary_key=True, max_length=64)
    user_google_sub: str = Field(index=True)
    model: str = Field(max_length=50, default="gemini-2.5-flash")
    system_prompt: str
    title: Optional[str] = Field(default=None, max_length=60)
    context_cache_id: Optional[str] = Field(default=None, max_length=128)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime = Field(default_factory=datetime.utcnow, index=True)