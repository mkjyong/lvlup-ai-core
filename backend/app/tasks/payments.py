from __future__ import annotations

from celery import shared_task
from app.config import get_settings
from app.services import portone as billing
from app.models.user import User
from app.models.db import get_session
from sqlmodel import select

settings = get_settings()


@shared_task(bind=True, max_retries=settings.RETRY_PAYMENT_MAX_ATTEMPTS, default_retry_delay=settings.RETRY_PAYMENT_INTERVAL_HOURS * 3600)
def create_checkout_with_retry(self, user_id: str, offering_id: str, currency: str = "USD"):
    """PortOne Checkout(사전등록) 생성 재시도 태스크.

    최초 호출 실패 시 Celery 가 6시간 간격, 최대 설정 횟수까지 재시도한다.
    """

    import anyio

    async def _inner() -> None:
        async with get_session() as session:
            result = await session.exec(select(User).where(User.google_sub == user_id))  # type: ignore[attr-defined]
            user = result.one_or_none()
            if not user:
                return  # user not found → 중단
            try:
                await billing.create_checkout(user, offering_id, currency)
            except Exception as exc:  # noqa: BLE001
                raise self.retry(exc=exc)

    anyio.run(_inner) 