"""원본 텍스트 적재 테이블 (STG1 / raw_data)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Index


class RawData(SQLModel, table=True):
    __tablename__ = "raw_data"
    """추출된 원본 텍스트를 일시 저장하는 Stage1 테이블."""

    id: Optional[int] = Field(default=None, primary_key=True)
    doc_id: str = Field(index=True)
    source: str = Field(index=True)
    text: str
    processed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 인덱스(복합)로 doc_id + source 조회 가속
    __table_args__ = (
        Index("ix_raw_data_doc_source", "doc_id", "source"),
    ) 