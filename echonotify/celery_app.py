"""Celery application configuration."""

from celery import Celery

from echonotify.constants import (
    BEAT_SCHEDULE_DAILY_AT_MIDNIGHT,
    BEAT_SCHEDULE_EVERY_30_MINUTES,
    BEAT_SCHEDULE_EVERY_SIX_HOURS,
    RESULT_EXPRIRES,
    TASK_SOFT_TIME_LIMIT,
    TASK_TIME_LIMIT,
    WORKER_MAX_TASKS_PER_CHILD,
    WORKER_PREFETCH_MULTIPLIER,
)
from echonotify.settings import Settings

settings = Settings()

app = Celery("echonotify")
app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=TASK_TIME_LIMIT,
    task_soft_time_limit=TASK_SOFT_TIME_LIMIT,
    worker_prefetch_multiplier=WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=WORKER_MAX_TASKS_PER_CHILD,
    worker_pool_restarts=True,
    worker_hijack_root_logger=False,
    result_expires=RESULT_EXPRIRES,
    beat_schedule={
        "cleanup_expired_sessions": {
            "task": "echonotify.infrastructure.celery.tasks.cleanup_expired_sessions_task",  # noqa
            "schedule": BEAT_SCHEDULE_EVERY_SIX_HOURS,  # Every 6 hours
        },
        "cleanup_old_orders": {
            "task": "echonotify.infrastructure.celery.tasks.cleanup_old_orders_task",  # noqa
            "schedule": BEAT_SCHEDULE_DAILY_AT_MIDNIGHT,  # Daily at midnight
        },
        "cleanup_old_messages": {
            "task": "echonotify.infrastructure.celery.tasks.cleanup_old_messages_task",  # noqa
            "schedule": BEAT_SCHEDULE_DAILY_AT_MIDNIGHT,  # Daily at midnight
        },
        "health_check": {
            "task": "echonotify.infrastructure.celery.tasks.health_check",
            "schedule": BEAT_SCHEDULE_EVERY_30_MINUTES,  # Every 30 minutes
        },
    },
)

# Register tasks

if __name__ == "__main__":
    app.start()
