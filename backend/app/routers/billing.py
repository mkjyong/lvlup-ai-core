"""Billing 라우터."""
from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from pydantic import BaseModel
import json

from app.services import revenuecat as billing
from app.tasks.payments import create_checkout_with_retry
from app.models.plan_tier import PlanTier
from app.models.user import User
from app.deps import get_current_user
from app.models.payment import PaymentLog
from app.models.db import get_session
from sqlmodel import select

router = APIRouter(prefix="/billing", tags=["billing"])


class PaymentRequest(BaseModel):
    offering_id: str  # RevenueCat Offering ID


class PaymentInitResponse(BaseModel):
    checkout_url: str


@router.post("/initiate", response_model=PaymentInitResponse)
async def initiate_payment(payload: PaymentRequest, user: User = Depends(get_current_user)):
    """Checkout 세션 생성.

    RevenueCat API 오류가 발생하면 Celery 태스크로 재시도를 예약한다.
    """

    try:
        data = await billing.create_checkout(user, payload.offering_id)
        return PaymentInitResponse(checkout_url=data.get("checkout_url", ""))
    except Exception as exc:  # noqa: BLE001
        # 첫 실패 → Celery 재시도 예약
        create_checkout_with_retry.delay(user.google_sub, payload.offering_id)
        raise HTTPException(status_code=502, detail="Failed to create checkout session; retry scheduled.") from exc


@router.post("/notify")
async def payment_webhook(request: Request, x_revenuecat_signature: str = Header("")):
    raw = await request.body()
    ok = await billing.verify_webhook(raw, x_revenuecat_signature)
    if not ok:
        raise HTTPException(status_code=400, detail="bad signature")

    body = json.loads(raw)
    # 비즈니스 로직 위임 – 내부에서 plan 업데이트, PaymentLog 작성, 추천인 보상 처리 포함
    await billing.process_webhook_event(body)

    return {"status": "ok"}

# === 구독 취소 ===


class CancelRequest(BaseModel):
    product_id: str  # RevenueCat Product Identifier (Stripe Price ID)


@router.post("/cancel")
async def cancel_subscription(payload: CancelRequest, user: User = Depends(get_current_user)):
    """사용자의 구독을 다음 결제부터 취소한다."""

    result = await billing.cancel_subscription(user, payload.product_id)

    # RevenueCat 측 구독은 취소 요청되었으나, 만료 시점까지 plan 유지
    # 별도 만료 webhook 처리에서 plan_tier 를 free 로 전환한다.

    return {"status": "cancelled", "rc": result} 