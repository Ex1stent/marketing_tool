from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID", "")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
IG_GRAPH_HOST = os.getenv("IG_GRAPH_HOST", "graph.facebook.com")
IG_GRAPH_VERSION = os.getenv("IG_GRAPH_VERSION", "v21.0")

WHATSAPP_ID = os.getenv("WHATSAPP_ID", "")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")

FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
FACEBOOK_GRAPH_HOST = os.getenv("FACEBOOK_GRAPH_HOST", "graph.facebook.com")
FACEBOOK_GRAPH_VERSION = os.getenv("FACEBOOK_GRAPH_VERSION", "v21.0")
FACEBOOK_WEBHOOK_VERIFY_TOKEN = os.getenv("FACEBOOK_WEBHOOK_VERIFY_TOKEN", "")

META_WEBHOOK_VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1234@localhost:5432/mcp")
DOCUMENT_PATH = os.getenv("DOCUMENT_PATH", "")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")
