from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, JSON  # type: ignore

from sqlmodel import Field, SQLModel


class PaymentLog(SQLModel, table=True):
    __tablename__ = "payment_log"
    """결제/구독 이벤트 로그."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_google_sub: str = Field(index=True)
    offering_id: str = ""
    event_type: str = ""
    amount_usd: float = 0.0  # 실 결제 금액(할인 적용 후)
    discount_usd: float = 0.0  # referral credit 등으로 적용된 할인액
    raw_event: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))  # json 저장
    created_at: datetime = Field(default_factory=datetime.utcnow) 