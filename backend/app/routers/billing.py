"""Billing 라우터."""
from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from pydantic import BaseModel
import json
from app.config import get_settings

from app.services import portone as billing
from app.tasks.payments import create_checkout_with_retry
from app.models.plan_tier import PlanTier
from app.models.user import User
from app.deps import get_current_user
from app.models.user_plan import UserPlan
from app.models.payment import PaymentLog
from app.deps import get_session as get_session_dep
from app.models.db import get_session as get_session_cm
from sqlmodel import select

router = APIRouter(prefix="/billing", tags=["billing"])
settings = get_settings()


class PaymentRequest(BaseModel):
    offering_id: str  # PlanTier ID
    currency: str = "USD"  # ISO 4217 (e.g., USD, KRW)


class PaymentInitResponse(BaseModel):
    checkout_url: str


@router.post("/initiate", response_model=PaymentInitResponse)
async def initiate_payment(payload: PaymentRequest, user: User = Depends(get_current_user)):
    """Checkout 세션 생성.

    PortOne API 오류가 발생하면 Celery 태스크로 재시도를 예약한다.
    """

    try:
        data = await billing.create_checkout(user, payload.offering_id, payload.currency)
        return PaymentInitResponse(checkout_url=data.get("checkout_url", ""))
    except Exception as exc:  # noqa: BLE001
        # 첫 실패 → Celery 재시도 예약
        create_checkout_with_retry.delay(user.google_sub, payload.offering_id, payload.currency)
        raise HTTPException(status_code=502, detail="Failed to create checkout session; retry scheduled.") from exc


@router.post("/notify")
async def payment_webhook(request: Request, x_portone_signature: str = Header("")):
    raw = await request.body()
    ok = await billing.verify_webhook(raw, x_portone_signature)
    if not ok:
        raise HTTPException(status_code=400, detail="bad signature")

    body = json.loads(raw)
    # 비즈니스 로직 위임 – 내부에서 plan 업데이트, PaymentLog 작성, 추천인 보상 처리 포함
    await billing.process_webhook_event(body)

    return {"status": "ok"}

# === 구독 상태 조회 ===


class ActiveSubResponse(BaseModel):
    plan_tier: str | None = None  # 예: basic_monthly
    payment_id: str | None = None
    status: str | None = None  # latest event_type
    amount_usd: float | None = None
    currency: str | None = None
    retry_attempts_left: int | None = None
    next_payment_at: str | None = None  # ISO8601
    expires_at: str | None = None


@router.get("/active", response_model=ActiveSubResponse)
async def get_active_subscription(user: User = Depends(get_current_user), session=Depends(get_session_dep)):
    """사용자의 최신 결제 로그를 조회하여 활성 구독 정보를 반환한다.

    실제 PortOne 결제 모델이 복잡할 수 있으므로, 가장 최근 PaymentLog 레코드를
    단순 조회해 payment_id 를 노출한다.
    """
    stmt = (
        select(PaymentLog)
        .where(
            PaymentLog.user_google_sub == user.google_sub,
            PaymentLog.event_type.in_(["payment_succeeded", "paid"]),
        )
        .order_by(PaymentLog.created_at.desc())
        .limit(1)
    )
    row = (await session.exec(stmt)).one_or_none()  # type: ignore[attr-defined]

    if row is None:
        return ActiveSubResponse()

    payment_id = None
    currency = None
    next_payment_at = None
    retry_count = 0
    if isinstance(row.raw_event, dict):
        payment_id = row.raw_event.get("payment_id") or row.raw_event.get("id")
        currency = row.raw_event.get("currency")
        next_payment_at = row.raw_event.get("next_payment_at")
        retry_count = row.raw_event.get("retry_count", 0)

    # expires_at – 최신 UserPlan 레코드 참고
    plan_stmt = (
        select(UserPlan)
        .where(UserPlan.user_google_sub == user.google_sub)
        .order_by(UserPlan.expires_at.desc())
        .limit(1)
    )
    plan_row = (await session.exec(plan_stmt)).one_or_none()  # type: ignore[attr-defined]
    expires_at = plan_row.expires_at.isoformat() if plan_row and plan_row.expires_at else None

    max_attempts = settings.RETRY_PAYMENT_MAX_ATTEMPTS
    return ActiveSubResponse(
        plan_tier=row.offering_id,
        payment_id=payment_id,
        status=row.event_type,
        amount_usd=row.amount_usd,
        currency=currency,
        retry_attempts_left=max(0, max_attempts - retry_count),
        next_payment_at=next_payment_at,
        expires_at=expires_at,
    )

# === 구독 취소 ===


class CancelRequest(BaseModel):
    payment_id: str  # PortOne Payment ID


@router.post("/cancel")
async def cancel_subscription(payload: CancelRequest, user: User = Depends(get_current_user)):
    """사용자의 구독을 다음 결제부터 취소한다."""

    result = await billing.cancel_subscription(user, payload.payment_id)

    # 만료 시점 조회
    async with get_session_cm() as sess:
        plan_row = (
            await sess.exec(
                select(UserPlan)
                .where(UserPlan.user_google_sub == user.google_sub)
                .order_by(UserPlan.expires_at.desc())
                .limit(1)
            )
        ).one_or_none()
        expires_at = plan_row.expires_at.isoformat() if plan_row and plan_row.expires_at else None

    return {"status": "cancelled", "expires_at": expires_at, "rc": result} 