from __future__ import annotations

import config
import os
import sys

from celery import Celery

DATABASE_URL = config.DATABASE_URL
RABBITMQ_URL = config.RABBITMQ_URL

from utils.logger import logger

_project_root = os.path.abspath(os.path.dirname(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

app = Celery(
    "meta_scheduler",
    broker=RABBITMQ_URL,
    backend=f"db+{DATABASE_URL}",
    include=[
        "scheduler.instagram_tasks",
        "scheduler.whatsapp_tasks",
        "scheduler.facebook_tasks",
        "scheduler.scheduler_tasks",
    ],
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    task_track_started=True,
    task_soft_time_limit=240,
    task_time_limit=300,
    worker_max_tasks_per_child=500,
    result_expires=3600,
    beat_schedule={
        "check-scheduled-posts": {
            "task": "scheduler.scheduler_tasks.check_and_enqueue_posts",
            "schedule": 60.0,
        }
    },
)

logger.info(
    "Celery app initialised | broker=%s backend=%s beat=%s",
    RABBITMQ_URL,
    f"db+{DATABASE_URL}",
    list(app.conf.beat_schedule.keys()),
)