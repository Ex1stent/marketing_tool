from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from mcp.server.fastmcp import FastMCP

from utils import graph, logger

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def _tool(mcp: FastMCP):
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = fn(*args, **kwargs)
                return await result if hasattr(result, "__await__") else result
            except graph.GraphError as e:
                logger.error("GraphError in %s: %s", fn.__name__, e)
                return e.to_dict()
            except (ValueError, TypeError) as e:
                logger.error("ValidationError in %s: %s", fn.__name__, e)
                return {"error": True, "message": str(e), "type": type(e).__name__}

        return mcp.tool()(wrapper)

    return decorator
