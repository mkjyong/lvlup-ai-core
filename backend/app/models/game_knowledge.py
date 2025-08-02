"""RAG 검색용 임베딩 청크 저장 테이블 (game_knowledge)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, UniqueConstraint, Float, JSON  # type: ignore
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, SQLModel


class GameKnowledge(SQLModel, table=True):
    __tablename__ = "game_knowledge"
    """게임 전략 문서 임베딩 청크."""

    id: Optional[int] = Field(default=None, primary_key=True)
    doc_id: str = Field(index=True)
    chunk_id: int = 0  # 원본 문서 내 청크 순번
    text: str
    # pgvector 확장 사용 시 ARRAY → vector 타입으로 마이그레이션
    embedding: List[float] = Field(sa_column=Column(ARRAY(Float)))
    score: float = Field(ge=0, le=1)
    meta: dict | None = Field(default=None, alias="metadata", sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("doc_id", "chunk_id", name="uq_doc_chunk"),
    ) 