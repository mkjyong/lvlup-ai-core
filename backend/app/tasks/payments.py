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

# 기존 checkout retry 태스크 유지 -------------------------------------------------
@shared_task(bind=True, max_retries=settings.RETRY_PAYMENT_MAX_ATTEMPTS, default_retry_delay=settings.RETRY_PAYMENT_INTERVAL_HOURS * 3600)
def create_checkout_with_retry(self, user_id: str, offering_id: str, currency: str = "USD"):  # type: ignore[override]
    from app.services import portone as billing
    from app.models.user import User  # pylint: disable=import-error

    async def _inner() -> None:
        async with get_session() as sess:
            user = await sess.get(User, user_id)
            if user is None:
                return
            await billing.create_checkout(user, offering_id, currency)

    try:
        asyncio.run(_inner())
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc)