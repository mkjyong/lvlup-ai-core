"""Slack 알림 전송 서비스."""
from __future__ import annotations

import httpx

from app.config import get_settings

settings = get_settings()


async def _post(webhook_url: str | None, text: str) -> None:  # noqa: D401
    """Slack Incoming Webhook 호출."""
    if not webhook_url:
        return  # 미설정 시 무시
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(webhook_url, json={"text": text})
    except Exception:  # noqa: BLE001
        # Slack 장애로 애플리케이션 실패 방지
        pass


async def notify_subscription(user_id: str, offering_id: str, amount_usd: float) -> None:
    """신규 구독 알림."""
    text = f":tada: *Subscription* user={user_id}, plan={offering_id}, amount=${amount_usd:.2f}"
    await _post(settings.SLACK_WEBHOOK_SUBSCRIPTION_TRACKER, text)


async def notify_unsubscription(user_id: str, offering_id: str) -> None:
    """구독 취소 알림."""
    text = f":x: *Unsubscription* user={user_id}, plan={offering_id}"
    await _post(settings.SLACK_WEBHOOK_UNSUBSCRIPTION_TRACKER, text)


async def notify_backend_error(message: str) -> None:
    """백엔드 오류 알림."""
    text = f":rotating_light: *Backend Error*\n```{message}```"
    await _post(settings.SLACK_WEBHOOK_ALERT_BACKEND_ERR, text) 