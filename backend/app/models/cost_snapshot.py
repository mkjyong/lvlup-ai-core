from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CostSnapshot(SQLModel, table=True):
    """LLM 호출 1회당 비용 산출 스냅샷."""

    id: Optional[int] = Field(default=None, primary_key=True)
    usage_id: Optional[int] = Field(default=None, foreign_key="llm_usage.id")
    model: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int = 0
    cost_usd: float
    created_at: datetime = Field(default_factory=datetime.utcnow) 