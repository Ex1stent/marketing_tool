from __future__ import annotations

from models.scheduled_post import update_post_status
from utils import graph
from utils.async_util import run_async
from utils.logger import logger


def run_task_with_status(self, post_id: int | None, coro, log_name: str):
    try:
        result = run_async(coro)
        logger.info("%s completed", log_name)
        if post_id:
            update_post_status(post_id, "posted")
        return result
    except Exception as exc:
        logger.warning("%s failed | attempt=%d error=%s", log_name, self.request.retries + 1, exc)
        if post_id and self.request.retries >= self.max_retries - 1:
            update_post_status(post_id, "failed", str(exc))
        raise self.retry(exc=exc)
    finally:
        run_async(graph.close_client())
