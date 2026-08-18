import config
from contextlib import asynccontextmanager
import os
from config import UPLOAD_DIR
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from api.routes.chats import chat_routes
from api.routes.scheduler import scheduler_routes
from api.routes.webhooks import webhook_routes
from models.engine import engine as db_engine
from mcp_.server import tools_mcp
from utils import graph
from utils.logger import logger



async def shutdown():
    await graph.close_client()
    db_engine.dispose()
    logger.info("Application shut down cleanly")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    yield
    await shutdown()


app = FastAPI(title="Meta MCP", docs_url=None, redoc_url=None, lifespan=lifespan)
app.include_router(webhook_routes)
app.include_router(chat_routes, prefix="/api")
app.include_router(scheduler_routes, prefix="/api")
app.mount("/mcp", app=tools_mcp.sse_app())



# ponytail: local serving only; add CDN/object store for production
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}


logger.info("Uvicorn app ready | paths: /meta/webhook, /whatsapp/webhook, /facebook/webhook, /mcp, /health")
