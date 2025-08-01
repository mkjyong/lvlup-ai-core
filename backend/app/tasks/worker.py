"""Celery 워커 진입점 (Stub)."""
from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_coach_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BACKEND_URL,
)

# 태스크 모듈 자동 검색(app.tasks.*)
celery_app.autodiscover_tasks(["app.tasks"])

# Celery Beat – 주기적 작업 스케줄
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "retry-failed-payments": {
        "task": "app.tasks.payments.charge_retry_task",
        "schedule": crontab(minute=0, hour="*/6"),  # 6시간마다 재시도
    },
}
celery_app.conf.timezone = "UTC"


@celery_app.task
def sample_task(x: int, y: int) -> int:
    """샘플 태스크."""
    return x + y 