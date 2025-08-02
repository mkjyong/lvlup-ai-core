"""LLM Usage 로그 모델."""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class LLMUsage(SQLModel, table=True):
    __tablename__ = "llm_usage"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(index=True)
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    created_at: datetime = Field(default_factory=datetime.utcnow) 