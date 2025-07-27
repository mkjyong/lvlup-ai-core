"""RevenueCat 구독 관리 서비스."""
import hmac
import hashlib
import time
from typing import Dict

import httpx
import asyncio
from fastapi import HTTPException

from app.config import get_settings
from app.models.user import User
from app.services.security import decrypt_email
from app.models.payment import PaymentLog
from app.models.db import get_session
from app.models.plan_tier import PlanTier
from sqlmodel import select

settings = get_settings()

_client = httpx.AsyncClient(base_url=settings.REVENUECAT_BASE_URL, timeout=10.0, headers={
    "Accept": "application/json",
    "X-Platform": "stripe",
    "Authorization": f"Bearer {settings.REVENUECAT_API_KEY}",
})


# -----------------------------
# HTTP Retry Helper
# -----------------------------


async def _request_with_retry(method: str, url: str, **kwargs):  # noqa: D401
    """httpx 요청 재시도(3초 * 3회).

    settings.HTTP_RETRY_ATTEMPTS, settings.HTTP_RETRY_DELAY_SEC 사용.
    """

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


async def create_checkout(user: User, offering_id: str) -> Dict:
    """RevenueCat Stripe checkout 세션 생성."""
    try:
        customer_email = decrypt_email(user.email_enc)
    except Exception as exc:  # noqa: BLE001
        # 이메일 복호화 실패 → 사용자 데이터 불일치
        raise HTTPException(status_code=400, detail="Invalid encrypted email. Please re-login.") from exc

    body = {
        "app_user_id": user.google_sub,
        "new_app_user": True,
        "offering_id": offering_id,
        "customer": {
            "email": customer_email,
        },
        "idempotency_key": f"{user.google_sub}-{offering_id}",
        "success_url": f"{settings.DOMAIN_BASE_URL}/billing/success",
        "cancel_url": f"{settings.DOMAIN_BASE_URL}/billing/cancel",
    }
    resp = await _request_with_retry("POST", "/v1/checkouts", json=body)
    return resp.json()


async def verify_webhook(raw_body: bytes, signature: str) -> bool:  # noqa: D401
    """RevenueCat Webhook 서명 검증 (sha256 + Webhook Secret).

    공식 사양: 요청 본문 raw bytes 에 대해 HMAC-SHA256 을 계산.
    """
    secret = (
        settings.REVENUECAT_WEBHOOK_SECRET
        if settings.REVENUECAT_WEBHOOK_SECRET
        else settings.REVENUECAT_API_KEY
    )
    computed = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)


# === Subscription Cancellation ===

async def cancel_subscription(user: User, product_id: str) -> Dict:
    """RevenueCat 구독 취소 (다음 갱신부터).

    product_id 는 Stripe Price ID 또는 RevenueCat Product Identifier.
    """

    resp = await _request_with_retry("DELETE", f"/v1/subscribers/{user.google_sub}/subscriptions/{product_id}")
    return resp.json()


async def process_webhook_event(event: Dict):
    """RevenueCat Webhook 본문을 처리해 사용자 플랜 업데이트 및 결제 로그 생성."""
    user_id = event.get("app_user_id") or event.get("event", {}).get("app_user_id")
    if user_id is None:
        return
    event_type = event.get("type") or event.get("event_type") or "unknown"
    async with get_session() as session:
        from app.models.user import User  # 로컬 import to avoid circular

        # === Plan 가격 조회 ===
        offering_id = event.get("offering_id", "basic") or "basic"

        # 우선 offering_id 와 동일한 PlanTier 가 있는지 확인 (basic, basic_annual 등)
        plan_stmt = select(PlanTier).where(PlanTier.name == offering_id)
        plan_result = await session.exec(plan_stmt)
        plan: PlanTier | None = plan_result.one_or_none()

        if plan is None:
            # fallback: 기본 basic 플랜
            fallback_stmt = select(PlanTier).where(PlanTier.name == "basic")
            fallback_result = await session.exec(fallback_stmt)
            plan = fallback_result.one_or_none()

        plan_price = plan.price_usd if plan else 0.0

        # === 사용자 업데이트 ===
        user = await session.get(User, user_id)  # type: ignore[arg-type]

        # 이벤트 유형별 처리
        if event_type in {"INITIAL_PURCHASE", "NON_RENEWING_PURCHASE", "RENEWAL"}:
            # 구독 활성화 → basic
            if user and user.plan_tier != "basic":
                user.plan_tier = "basic"
                session.add(user)
        elif event_type in {"CANCELLATION", "BILLING_ERROR", "EXPIRATION"}:
            # 만료(취소) 이벤트에서 free 로 다운그레이드
            if user and user.plan_tier != "free":
                user.plan_tier = "free"
                session.add(user)

        # 결제 로그 적재 (가격은 PlanTier 기반, 할인 정보는 webhook 에 포함될 수도)
        plog = PaymentLog(
            user_google_sub=user_id,
            offering_id=offering_id,
            event_type=event_type,
            amount_usd=plan_price,
            raw_event=event,
        )
        session.add(plog)
        await session.commit() 
        # --- Slack Notification ---
        from app.services import slack as _slack  # 로컬 import to avoid circular

        if event_type in {"INITIAL_PURCHASE", "NON_RENEWING_PURCHASE", "RENEWAL"}:
            await _slack.notify_subscription(user_id, offering_id, plan_price)
        elif event_type in {"CANCELLATION", "BILLING_ERROR", "EXPIRATION"}:
            await _slack.notify_unsubscription(user_id, offering_id) 