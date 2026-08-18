from __future__ import annotations

from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP

from fastapi import FastAPI

from api.routes.webhooks import webhook_routes
from mcp_.tools.excel_service import register_excel_tools
from mcp_.tools.facebook_service import register_facebook_tools
from mcp_.tools.insta_service import register_instagram_tools
from mcp_.tools.schedule_service import register_schedule_tools
from mcp_.tools.whatsapp_service import register_whatsapp_tools
from utils import graph
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MCP app starting up")
    yield
    await graph.close_client()
    logger.info("MCP app shut down cleanly")


tools_mcp = FastMCP("meta-mcp", lifespan=lifespan)

register_instagram_tools(tools_mcp)
register_whatsapp_tools(tools_mcp)
register_facebook_tools(tools_mcp)
register_schedule_tools(tools_mcp)
register_excel_tools(tools_mcp)

logger.info("MCP tools registered")



