from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from celery_app import app
from config import IG_ACCESS_TOKEN, IG_ACCOUNT_ID, IG_GRAPH_HOST, IG_GRAPH_VERSION
from utils import graph
from utils.logger import get_logger

logger = get_logger(__name__)


def _post(path: str, **fields: Any) -> Any:
    base = f"https://{IG_GRAPH_HOST}/{IG_GRAPH_VERSION}"
    r = httpx.post(
        f"{base}/{path.lstrip('/')}",
        params={"access_token": IG_ACCESS_TOKEN},
        data={k: v for k, v in fields.items() if v is not None},
        timeout=120.0,
    )
    body = r.json() if r.text else r.text
    if r.status_code >= 400:
        raise graph.GraphError(r.status_code, body)
    return body


def _get(path: str, **params: Any) -> Any:
    base = f"https://{IG_GRAPH_HOST}/{IG_GRAPH_VERSION}"
    q = {k: v for k, v in params.items() if v is not None}
    q["access_token"] = IG_ACCESS_TOKEN
    r = httpx.get(
        f"{base}/{path.lstrip('/')}",
        params=q,
        timeout=120.0,
    )
    body = r.json() if r.text else r.text
    if r.status_code >= 400:
        raise graph.GraphError(r.status_code, body)
    return body


@app.task(bind=True, max_retries=2, default_retry_delay=30)
def publish_image_task(self, image_url: str, caption: str | None = None, location_id: str | None = None) -> dict[str, Any]:
    logger.info("publish_image_task started | image_url=%s caption=%s", image_url[:60] if image_url else None, caption)
    try:
        container = _post(
            f"{IG_ACCOUNT_ID}/media",
            image_url=image_url,
            caption=caption,
            location_id=location_id,
        )
        result = _post(f"{IG_ACCOUNT_ID}/media_publish", creation_id=container["id"])
        logger.info("publish_image_task completed | media_id=%s", result.get("id"))
        return {"success": True, "media_id": result.get("id"), "result": result}
    except Exception as exc:
        logger.warning("publish_image_task failed | attempt=%d error=%s", self.request.retries + 1, exc)
        raise self.retry(exc=exc)


def _wait_container(container_id: str, timeout_s: int = 300) -> None:
    elapsed = 0
    while elapsed < timeout_s:
        res = _get(container_id, fields="status_code,status")
        code = res.get("status_code")
        logger.debug("Container %s status=%s elapsed=%ds", container_id, code, elapsed)
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise graph.GraphError(0, {"error": {"message": f"container {container_id} status={code}"}})
        time.sleep(3)
        elapsed += 3
    raise TimeoutError(f"container {container_id} did not finish within {timeout_s}s")


@app.task(bind=True, max_retries=2, default_retry_delay=60)
def publish_reel_task(self, video_url: str, caption: str | None = None, share_to_feed: bool = True, cover_url: str | None = None) -> dict[str, Any]:
    logger.info("publish_reel_task started | video_url=%s caption=%s", video_url[:60] if video_url else None, caption)
    try:
        container = _post(
            f"{IG_ACCOUNT_ID}/media",
            media_type="REELS",
            video_url=video_url,
            caption=caption,
            share_to_feed=str(share_to_feed).lower(),
            cover_url=cover_url,
        )
        _wait_container(container["id"])
        result = _post(f"{IG_ACCOUNT_ID}/media_publish", creation_id=container["id"])
        logger.info("publish_reel_task completed | media_id=%s", result.get("id"))
        return {"success": True, "media_id": result.get("id"), "result": result}
    except Exception as exc:
        logger.warning("publish_reel_task failed | attempt=%d error=%s", self.request.retries + 1, exc)
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def publish_story_task(self, image_url: str | None = None, video_url: str | None = None) -> dict[str, Any]:
    logger.info("publish_story_task started | image_url=%s video_url=%s", bool(image_url), bool(video_url))
    try:
        container = _post(
            f"{IG_ACCOUNT_ID}/media",
            media_type="STORIES",
            image_url=image_url,
            video_url=video_url,
        )
        if video_url:
            _wait_container(container["id"])
        result = _post(f"{IG_ACCOUNT_ID}/media_publish", creation_id=container["id"])
        logger.info("publish_story_task completed | media_id=%s", result.get("id"))
        return {"success": True, "media_id": result.get("id"), "result": result}
    except Exception as exc:
        logger.warning("publish_story_task failed | attempt=%d error=%s", self.request.retries + 1, exc)
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def publish_carousel_task(self, items: list[dict[str, str]], caption: str | None = None) -> dict[str, Any]:
    logger.info("publish_carousel_task started | items=%d caption=%s", len(items), caption)
    try:
        child_ids: list[str] = []
        for i, item in enumerate(items):
            if "image_url" in item:
                child = _post(f"{IG_ACCOUNT_ID}/media", is_carousel_item="true", image_url=item["image_url"])
            elif "video_url" in item:
                child = _post(f"{IG_ACCOUNT_ID}/media", is_carousel_item="true", media_type="VIDEO", video_url=item["video_url"])
                _wait_container(child["id"])
            else:
                raise ValueError(f"Carousel item must contain image_url or video_url: {item}")
            child_ids.append(child["id"])
            logger.debug("Carousel child %d/%d created | id=%s", i + 1, len(items), child["id"])

        parent = _post(
            f"{IG_ACCOUNT_ID}/media",
            media_type="CAROUSEL",
            children=",".join(child_ids),
            caption=caption,
        )
        result = _post(f"{IG_ACCOUNT_ID}/media_publish", creation_id=parent["id"])
        logger.info("publish_carousel_task completed | media_id=%s", result.get("id"))
        return {"success": True, "media_id": result.get("id"), "result": result}
    except Exception as exc:
        logger.warning("publish_carousel_task failed | attempt=%d error=%s", self.request.retries + 1, exc)
        raise self.retry(exc=exc)
