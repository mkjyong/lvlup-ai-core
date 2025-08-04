"""Celery tasks for billing operations (checkout, retry charge)."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from celery import shared_task
from sqlmodel import select
from app.config import get_settings
from app.models.payment import PaymentLog
from app.models.db import get_session
from app.services import portone as portone_svc
from app.models.user import User

settings = get_settings()

@shared_task(bind=True, max_retries=settings.RETRY_PAYMENT_MAX_ATTEMPTS, default_retry_delay=settings.RETRY_PAYMENT_INTERVAL_HOURS * 3600)
def charge_retry_task(self):  # type: ignore[override]
    """주기적으로 payment_failed 구독을 재결제한다.

    * PaymentLog.event_type == 'payment_failed'
    * raw_event.retry_count < MAX
    """
    async def _inner() -> None:
        async with get_session() as sess:
            stmt = select(PaymentLog).where(
                PaymentLog.event_type == "payment_failed",
            )
            rows = (await sess.exec(stmt)).all()
            for row in rows:
                rc = (row.raw_event or {}).get("retry_count", 0)
                if rc >= settings.RETRY_PAYMENT_MAX_ATTEMPTS:
                    continue

                # fetch user
                user = await sess.get(User, row.user_google_sub)
                if user is None or not user.billing_key:
                    continue  # cannot retry

                try:
                    await portone_svc.charge_with_billing_key(
                        user,
                        payment_id=row.raw_event.get("payment_id", "retry"),
                        amount=row.amount_usd,
                        currency=row.raw_event.get("currency", "USD"),
                        order_name="subscription-retry",
                    )
                    # success -> log new succeeded row & update existing
                    row.event_type = "payment_succeeded"
                except Exception:
                    # increment retry_count
                    rc += 1
                    if row.raw_event is None:
                        row.raw_event = {}
                    row.raw_event["retry_count"] = rc
                    if rc >= settings.RETRY_PAYMENT_MAX_ATTEMPTS:
                        row.raw_event["final_failed_at"] = datetime.utcnow().isoformat()
                sess.add(row)
            await sess.commit()

    asyncio.run(_inner())

# BillingKey 재시도 태스크 제거 (SDK 발급으로 대체)
