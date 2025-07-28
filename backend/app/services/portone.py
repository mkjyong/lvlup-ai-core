"""PortOne 결제 관리 서비스 (아임포트 REST V2).

- Checkout(사전등록) 생성
- Webhook 서명 검증
- 결제 취소
- Webhook 이벤트 처리 (플랜 변경 & 결제 로그 적재)
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import time
from typing import Dict

import httpx
from fastapi import HTTPException
from sqlmodel import select

from app.config import get_settings
from app.models.db import get_session
from app.models.plan_tier import PlanTier
from app.services.security import decrypt_email

settings = get_settings()

# 공용 HTTP 클라이언트 (Connection pooling)
_client = httpx.AsyncClient(
    base_url=settings.PORTONE_BASE_URL,
    timeout=10.0,
    headers={
        "Accept": "application/json",
        "Authorization": f"PortOne {settings.PORTONE_API_SECRET}",
    },
)


async def _request_with_retry(method: str, url: str, **kwargs):  # noqa: D401
    """HTTPX 요청을 재시도 정책과 함께 실행."""

    for attempt in range(settings.HTTP_RETRY_ATTEMPTS):
        try:
            resp = await _client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        except httpx.HTTPError:
            if attempt < settings.HTTP_RETRY_ATTEMPTS - 1:
                await asyncio.sleep(settings.HTTP_RETRY_DELAY_SEC)
                continue
            raise


# ---------------------------------------------------------------------------
# Checkout / Payment
# ---------------------------------------------------------------------------
async def create_checkout(user: "User", offering_id: str, currency: str = "USD") -> Dict:
    """PortOne 결제 사전등록 & Checkout URL 생성.

    반환값 예시: {"checkout_url": "https://checkout.portone.io/<paymentId>", "payment_id": "..."}
    """

    # 가격 조회 (PlanTier → USD)
    async with get_session() as session:
        result = await session.exec(select(PlanTier).where(PlanTier.name == offering_id))
        plan = result.one_or_none()
        price_usd = plan.price_usd if plan else 0.0

    from app.services import currency as _currency

    total_amount = price_usd if currency == "USD" else _currency.convert(price_usd, "USD", currency)

    payment_id = f"{user.google_sub}-{offering_id}-{int(time.time())}"

    try:
        customer_email = decrypt_email(user.email_enc)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid encrypted email. Please re-login.") from exc

    body = {
        "orderName": offering_id,
        "totalAmount": round(total_amount, 2),
        "currency": currency,
        "customer": {
            "email": customer_email,
        },
        "successUrl": f"{settings.DOMAIN_BASE_URL}/billing/success",
        "failUrl": f"{settings.DOMAIN_BASE_URL}/billing/cancel",
    }

    # 사전등록 요청
    await _request_with_retry("POST", f"/payments/{payment_id}/pre-register", json=body)

    # PortOne 결제창 URL (고정 패턴)
    checkout_url = f"https://checkout.portone.io/{payment_id}"

    return {"checkout_url": checkout_url, "payment_id": payment_id}


# ---------------------------------------------------------------------------
# Webhook Verification
# ---------------------------------------------------------------------------
async def verify_webhook(raw_body: bytes, signature: str) -> bool:  # noqa: D401
    """PortOne Webhook HMAC-SHA256 검증."""

    secret = settings.PORTONE_WEBHOOK_SECRET or settings.PORTONE_API_SECRET
    computed = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)


# ---------------------------------------------------------------------------
# Cancel Payment / Subscription
# ---------------------------------------------------------------------------
async def cancel_subscription(user: "User", payment_id: str) -> Dict:
    """PortOne 결제 취소 요청 (즉시 취소)."""

    resp = await _request_with_retry("POST", f"/payments/{payment_id}/cancel", json={"reason": "user_cancelled"})
    return resp.json()


# ---------------------------------------------------------------------------
# Process Webhook Event
# ---------------------------------------------------------------------------
async def process_webhook_event(event: Dict):
    """Webhook 이벤트를 처리하여 플랜 변경 및 결제 로그를 저장한다."""

    user_id = event.get("userId") or event.get("customer", {}).get("id")
    if user_id is None:
        return

    event_type = event.get("status", "unknown")
    offering_id = event.get("orderName", "basic") or "basic"
    amount_usd = event.get("totalAmount", 0.0)

    from app.models.user import User  # 로컬 import to 방지 순환
    from app.models.payment import PaymentLog

    async with get_session() as session:
        # PlanTier 조회 (없으면 fallback)
        stmt = select(PlanTier).where(PlanTier.name == offering_id)
        result = await session.exec(stmt)
        plan: PlanTier | None = result.one_or_none()

        plan_price = plan.price_usd if plan else amount_usd

        user = await session.get(User, user_id)  # type: ignore[arg-type]

        # === 플랜 업데이트 ===
        if event_type == "SUCCEEDED":
            if user and user.plan_tier != "basic":
                user.plan_tier = "basic"
                session.add(user)
        elif event_type in {"CANCELLED", "FAILED"}:
            if user and user.plan_tier != "free":
                user.plan_tier = "free"
                session.add(user)

        # === 결제 로그 적재 ===
        plog = PaymentLog(
            user_google_sub=user_id,
            offering_id=offering_id,
            event_type=event_type,
            amount_usd=plan_price,
            raw_event=event,
        )
        session.add(plog)
        await session.commit()

        # === Slack Notification ===
        from app.services import slack as _slack

        pay_method = event.get("payMethod", event.get("method"))
        cancel_reason = event.get("cancelReason")

        if event_type == "SUCCEEDED":
            await _slack.notify_subscription(user_id, offering_id, plan_price, currency=event.get("currency", "USD"), pay_method=pay_method)
        elif event_type in {"CANCELLED", "FAILED"}:
            await _slack.notify_unsubscription(user_id, offering_id, reason=cancel_reason) 

# ---------------------------------------------------------------------------
# Billing Key (Recurring Payment)
# ---------------------------------------------------------------------------
async def create_billing_key(user: "User") -> str:
    """사용자 결제수단을 BillingKey 로 저장하고 반환."""

    try:
        customer_email = decrypt_email(user.email_enc)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid encrypted email. Please re-login.") from exc

    body = {
        "customer": {
            "id": user.google_sub,
            "email": customer_email,
        }
    }

    resp = await _request_with_retry("POST", "/billing-keys", json=body)
    data = resp.json()
    billing_key = data.get("billingKey")

    if billing_key:
        from app.models.db import get_session
        async with get_session() as session:
            db_user = await session.get(type(user), user.google_sub)  # type: ignore[arg-type]
            if db_user:
                db_user.billing_key = billing_key
                session.add(db_user)
                await session.commit()

    return billing_key or ""


async def charge_with_billing_key(user: "User", payment_id: str, amount: float, currency: str = "USD", order_name: str = "subscription") -> Dict:
    """저장된 BillingKey 로 즉시 결제."""

    if not user.billing_key:
        raise HTTPException(status_code=400, detail="No billing key on file.")

    body = {
        "orderName": order_name,
        "totalAmount": amount,
        "billingKey": user.billing_key,
        "currency": currency,
    }

    resp = await _request_with_retry("POST", f"/payments/{payment_id}/billing-key", json=body)
    return resp.json() 