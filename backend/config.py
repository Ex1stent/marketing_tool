from dotenv import load_dotenv

load_dotenv()

import os
from anthropic import Anthropic

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
CLIENT=Anthropic(api_key=ANTHROPIC_API_KEY, base_url=ANTHROPIC_BASE_URL)

# Knowledge base
DOCUMENT_PATH = os.getenv("DOCUMENT_PATH")

# File uploads
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "uploads"))
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Celery / RabbitMQ
RABBITMQ_URL = os.getenv("RABBITMQ_URL")

# MCP
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

# Instagram
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
IG_GRAPH_HOST = os.getenv("IG_GRAPH_HOST")
IG_GRAPH_VERSION = os.getenv("IG_GRAPH_VERSION")
IG_USER_ID = os.getenv("IG_USER_ID")

# Facebook
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
FACEBOOK_GRAPH_HOST = os.getenv("FACEBOOK_GRAPH_HOST")
FACEBOOK_GRAPH_VERSION = os.getenv("FACEBOOK_GRAPH_VERSION")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")

# WhatsApp
WHATSAPP_ID = os.getenv("WHATSAPP_ID")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")

# Meta Ads
META_AD_ACCESS_TOKEN = os.getenv("META_AD_ACCESS_TOKEN")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID")

# Webhook verify tokens
FACEBOOK_WEBHOOK_VERIFY_TOKEN = os.getenv("FACEBOOK_WEBHOOK_VERIFY_TOKEN")
META_WEBHOOK_VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

#Scheduler
TEMPLATE_PATH = r"C:\Users\sharm\Documents\tool_v1\marketing_tool - v1\frontend\src\assets\scheduler_template.xlsx"