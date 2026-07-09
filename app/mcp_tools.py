from mcp.server.fastmcp import FastMCP

from service_handler.insta_service import register_instagram_tools
from service_handler.whatsapp_service import register_whatsapp_tools
from service_handler.facebook_service import register_facebook_tools
from service_handler.schedule_service import register_schedule_tools
from service_handler.excel_service import register_excel_tools
from utils.logger import get_logger

logger = get_logger(__name__)

tools_mcp = FastMCP("meta-mcp")
register_instagram_tools(tools_mcp)
register_whatsapp_tools(tools_mcp)
register_facebook_tools(tools_mcp)
register_schedule_tools(tools_mcp)
register_excel_tools(tools_mcp)

logger.info("MCP tools registered (instagram + whatsapp + facebook + schedule + excel)")
