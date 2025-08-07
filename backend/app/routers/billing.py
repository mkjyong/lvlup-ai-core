"""Billing 라우터."""
from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from pydantic import BaseModel
import json
from app.config import get_settings

from app.services import portone as billing
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

# === BillingKey 저장 & 첫 결제 ===

class BillingKeyPayload(BaseModel):
    """프런트엔드에서 전달받는 BillingKey 저장 페이로드."""

    billing_key: str
    customer_id: str | None = None  # JS SDK issue 시 전달했던 customer.id
    channel_key: str | None = None  # PayPal 채널 키 (선택)


@router.post("/store-billing-key", status_code=201)
async def store_billing_key(
    payload: BillingKeyPayload,
    user: User = Depends(get_current_user),
):
    """BillingKey 를 DB 에 저장하고 첫 결제(옵션) 수행."""

    # 1) BillingKey 저장
    async with get_session_cm() as sess:
        db_user = await sess.get(User, user.google_sub)
        if db_user:
            db_user.billing_key = payload.billing_key
            sess.add(db_user)
            await sess.commit()

    # 2) 첫 결제 실행
    amount_usd = 15.0  # TODO: 플랜 가격에 따라 동적 계산
    payment_id = f"{user.google_sub}-init"
    try:
        await billing.charge_with_billing_key(
            user,
            payment_id=payment_id,
            amount=amount_usd,
            currency="USD",
            order_name="subscription-initial",
        )
        # 3) 다음 회차 예약 (30일 후)
        await billing.schedule_next_payment(
            user,
            billing_key=payload.billing_key,
            amount_usd=amount_usd,
            currency="USD",
            days_after=30,
        )
    except Exception as exc:  # noqa: BLE001
        # 실패 로깅만 하고 201 반환
        import logging
        logging.getLogger(__name__).exception("BillingKey flow error", exc_info=exc)

    return {"status": "ok"}

# === Billing Failure Logging ===

class BillingFailurePayload(BaseModel):
    """결제/빌링키 발급 실패 로그 페이로드."""
    code: str
    message: str


@router.post("/log-failure", status_code=201)
async def log_billing_failure(
    payload: BillingFailurePayload,
    user: User = Depends(get_current_user),
):
    """PayPal BillingKey 발급 실패·취소 오류를 저장한다."""
    async with get_session_cm() as sess:
        plog = PaymentLog(
            user_google_sub=user.google_sub,
            offering_id="",
            event_type="issue_failed",
            amount_usd=0.0,
            raw_event={"code": payload.code, "message": payload.message},
        )
        sess.add(plog)
        await sess.commit()
    return {"status": "logged"}

# === 구독 취소 ===


class CancelRequest(BaseModel):
    payment_id: str  # PortOne Payment ID


@router.post("/cancel")
async def cancel_subscription(payload: CancelRequest, user: User = Depends(get_current_user)):
    """사용자의 구독을 다음 결제부터 취소한다."""

    result = await billing.cancel_subscription(user, payload.payment_id)

    # 응답 status 분석 (REQUESTED = 승인 대기)
    payment_status = (result.get("status") or "").upper()
    if payment_status == "REQUESTED":
        cancel_status = "pending"
    elif payment_status in {"CANCELLED", "CANCELED"}:
        cancel_status = "cancelled"
    else:
        cancel_status = payment_status.lower() if payment_status else "unknown"

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

    return {"status": cancel_status, "expires_at": expires_at, "rc": result} 