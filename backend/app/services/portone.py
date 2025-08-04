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
from datetime import datetime, timedelta
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
# Webhook Verification
# ---------------------------------------------------------------------------
async def verify_webhook(raw_body: bytes, signature: str) -> bool:  # noqa: D401
    """PortOne Webhook HMAC-SHA256 검증."""


    secret = settings.PORTONE_WEBHOOK_SECRET 
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
async def create_billing_key(user: "User") -> Dict:
    """PortOne BillingKey 발급 요청.

    반환값 예시:
        {
            "issue_url": "https://checkout.portone.io/billing-keys/issue/abcd",
            "billing_key": "bk_live_xxx"  # 카드 인증 완료 후에만 포함
        }
    """

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
    issue_url = data.get("issueUrl") or data.get("issue_url")

    # 카드 인증 완료 직후 Webhook 을 받기 전에도 billingKey 가 바로 내려올 수 있다.
    if billing_key:
        from app.models.db import get_session
        async with get_session() as session:
            db_user = await session.get(type(user), user.google_sub)  # type: ignore[arg-type]
            if db_user:
                db_user.billing_key = billing_key
                session.add(db_user)
                await session.commit()

    return {"issue_url": issue_url or "", "billing_key": billing_key}


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

# ---------------------------------------------------------------------------
# Schedule Next Recurring Payment
# ---------------------------------------------------------------------------
async def schedule_next_payment(user: "User", billing_key: str, amount_usd: float, currency: str = "USD", days_after: int = 30):  # noqa: ANN001
    """포트원 결제 예약 API 호출 – 다음 회차 결제를 예약한다."""

    if not billing_key:
        raise HTTPException(status_code=400, detail="billing_key required")

    time_to_pay = (datetime.utcnow() + timedelta(days=days_after)).isoformat() + "Z"
    payment_id = f"{user.google_sub}-scheduled-{int(time.time())}"

    body = {
        "payment": {
            "billingKey": billing_key,
            "orderName": "subscription-recurring",
            "customer": {"id": user.google_sub},
            "amount": {"total": round(amount_usd, 2)},
            "currency": currency,
        },
        "timeToPay": time_to_pay,
    }

    await _request_with_retry(
        "POST",
        f"/payments/{payment_id}/schedule",
        json=body,
    )

    return payment_id