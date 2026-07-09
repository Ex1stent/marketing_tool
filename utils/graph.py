from __future__ import annotations

import os
from typing import Any

import httpx

from config import (
    FACEBOOK_ACCESS_TOKEN,
    FACEBOOK_GRAPH_HOST,
    FACEBOOK_GRAPH_VERSION,
    FACEBOOK_PAGE_ID,
    IG_ACCESS_TOKEN,
    IG_ACCOUNT_ID,
    IG_GRAPH_HOST,
    IG_GRAPH_VERSION,
    IG_USER_ID,
    WHATSAPP_ID,
    WHATSAPP_TOKEN,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class GraphError(RuntimeError):
    def __init__(self, status: int, payload: Any):
        self.status = status
        self.payload = payload
        super().__init__(f"Graph API {status}: {payload}")

    def to_dict(self) -> dict[str, Any]:
        err = self.payload.get("error", {}) if isinstance(self.payload, dict) else {}
        return {
            "error": True,
            "status": self.status,
            "message": err.get("message") or str(self.payload),
            "code": err.get("code"),
            "subcode": err.get("error_subcode"),
            "fbtrace_id": err.get("fbtrace_id"),
        }


_client: httpx.AsyncClient | None = None


def _http() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


def _config() -> tuple[str, str]:
    if not IG_ACCESS_TOKEN:
        raise RuntimeError("IG_ACCESS_TOKEN is not set")
    return f"https://{IG_GRAPH_HOST}/{IG_GRAPH_VERSION}", IG_ACCESS_TOKEN


def _whatsappconfig() -> tuple[str, str]:
    if not WHATSAPP_TOKEN:
        raise RuntimeError("WHATSAPP_TOKEN is not set")
    return f"https://{IG_GRAPH_HOST}/{IG_GRAPH_VERSION}", WHATSAPP_TOKEN


def _facebookconfig() -> tuple[str, str]:
    if not FACEBOOK_ACCESS_TOKEN:
        raise RuntimeError("FACEBOOK_ACCESS_TOKEN is not set")
    return f"https://{FACEBOOK_GRAPH_HOST}/{FACEBOOK_GRAPH_VERSION}", FACEBOOK_ACCESS_TOKEN


def _clean(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _unwrap(r: httpx.Response, label: str = "") -> Any:
    try:
        body = r.json()
    except ValueError:
        body = r.text
    if r.status_code >= 400:
        logger.error("API error %s | status=%d body=%s", label, r.status_code, body)
        raise GraphError(r.status_code, body)
    logger.debug("API success %s | status=%d", label, r.status_code)
    return body


def ig_account_id() -> str:
    if not IG_ACCOUNT_ID:
        raise RuntimeError("IG_ACCOUNT_ID is not set")
    return IG_ACCOUNT_ID


def ig_user_id() -> str:
    if not IG_USER_ID:
        raise RuntimeError("IG_USER_ID is not set")
    return IG_USER_ID


def whatsapp_id() -> str:
    if not WHATSAPP_ID:
        raise RuntimeError("WHATSAPP_ID is not set")
    return WHATSAPP_ID


def facebook_page_id() -> str:
    if not FACEBOOK_PAGE_ID:
        raise RuntimeError("FACEBOOK_PAGE_ID is not set")
    return FACEBOOK_PAGE_ID


async def get(path: str, **params: Any) -> Any:
    base, token = _config()
    q = _clean(params)
    q["access_token"] = token
    label = f"GET {path}"
    logger.debug("API call %s | params=%s", label, {k for k in q if k != "access_token"})
    r = await _http().get(f"{base}/{path.lstrip('/')}", params=q)
    return _unwrap(r, label)


async def post(path: str, **fields: Any) -> Any:
    base, token = _config()
    label = f"POST {path}"
    logger.debug("API call %s | fields=%s", label, set(fields))
    r = await _http().post(
        f"{base}/{path.lstrip('/')}",
        params={"access_token": token},
        data=_clean(fields),
    )
    return _unwrap(r, label)


async def whatsapp_post(path: str, **fields: Any) -> Any:
    base, token = _whatsappconfig()
    label = f"WA POST {path}"
    logger.debug("API call %s | fields=%s", label, set(fields))
    r = await _http().post(
        f"{base}/{path.lstrip('/')}",
        params={"access_token": token},
        data=_clean(fields),
    )
    return _unwrap(r, label)


async def facebook_get(path: str, **params: Any) -> Any:
    base, token = _facebookconfig()
    q = _clean(params)
    q["access_token"] = token
    label = f"FB GET {path}"
    logger.debug("API call %s | params=%s", label, {k for k in q if k != "access_token"})
    r = await _http().get(f"{base}/{path.lstrip('/')}", params=q)
    return _unwrap(r, label)


async def facebook_post(path: str, **fields: Any) -> Any:
    base, token = _facebookconfig()
    label = f"FB POST {path}"
    logger.debug("API call %s | fields=%s", label, set(fields))
    r = await _http().post(
        f"{base}/{path.lstrip('/')}",
        params={"access_token": token},
        data=_clean(fields),
    )
    return _unwrap(r, label)


async def facebook_delete(path: str, **params: Any) -> Any:
    base, token = _facebookconfig()
    q = _clean(params)
    q["access_token"] = token
    label = f"FB DELETE {path}"
    logger.debug("API call %s | params=%s", label, {k for k in q if k != "access_token"})
    r = await _http().delete(f"{base}/{path.lstrip('/')}", params=q)
    return _unwrap(r, label)


async def delete(path: str, **params: Any) -> Any:
    base, token = _config()
    q = _clean(params)
    q["access_token"] = token
    label = f"DELETE {path}"
    logger.debug("API call %s | params=%s", label, {k for k in q if k != "access_token"})
    r = await _http().delete(f"{base}/{path.lstrip('/')}", params=q)
    return _unwrap(r, label)


async def paginate(path: str, max_pages: int = 5, **params: Any) -> dict[str, Any]:
    results: list[Any] = []
    pages = 0
    next_url: str | None = None
    label = f"PAGINATE {path}"

    while pages < max_pages:
        if next_url is None:
            res = await get(path, **params)
        else:
            logger.debug("API call %s | page=%d url=%s", label, pages + 1, next_url)
            r = await _http().get(next_url)
            res = _unwrap(r, f"{label} page={pages + 1}")
        pages += 1
        results.extend(res.get("data", []))
        next_url = res.get("paging", {}).get("next")
        if not next_url:
            break

    logger.debug("Paginate complete %s | pages=%d items=%d has_more=%s", label, pages, len(results), bool(next_url))
    return {"data": results, "pages_fetched": pages, "has_more": bool(next_url)}

