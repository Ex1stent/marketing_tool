from fastapi import FastAPI

from api.routes.webhooks import webhook_routes
from app.mcp_tools import tools_mcp
from models.database import engine as db_engine
from utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Meta MCP", docs_url=None, redoc_url=None)
app.include_router(webhook_routes)
app.mount("/mcp", app=tools_mcp.sse_app())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    db_engine.dispose()
    logger.info("Database engine disposed on shutdown")


logger.info("Uvicorn app ready | paths: /meta/webhook, /whatsapp/webhook, /facebook/webhook, /mcp, /health")
