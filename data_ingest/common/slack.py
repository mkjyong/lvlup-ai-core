"""Data Ingestor Slack 알림 헬퍼."""
from __future__ import annotations

import os
import asyncio
import aiohttp


async def _post(text: str) -> None:  # noqa: D401
    webhook_url = os.getenv("SLACK_WEBHOOK_ALERT_DATA_INGESTOR_ERR")
    if not webhook_url:
        return
    try:
        async with aiohttp.ClientSession(timeout=5) as session:
            await session.post(webhook_url, json={"text": text})
    except Exception:  # noqa: BLE001
        pass


def send_slack_message(text: str) -> None:  # noqa: D401
    """이벤트 루프 여부에 따라 Slack 메시지 전송."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # 루프가 없으면 동기 실행
        asyncio.run(_post(text))
    else:
        # 이미 루프 실행 중 → fire-and-forget
        asyncio.create_task(_post(text)) 