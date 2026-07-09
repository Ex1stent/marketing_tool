# Marketing Tool

Multi-platform content scheduler with MCP tools for Instagram, Facebook, and WhatsApp. Provides webhook-based auto-reply using Anthropic Claude, MCP tools for AI agent control, and scheduled post publishing via Celery.

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI + Uvicorn |
| MCP Framework | `mcp` >= 1.28 (FastMCP, SSE transport) |
| Task Queue | Celery >= 5.5 + RabbitMQ |
| Database | PostgreSQL + SQLAlchemy 2.0 |
| AI/LLM | Anthropic Claude (`claude-sonnet-4-6`) |
| HTTP Client | httpx (async + sync) |

## Project Structure

```
marketing_tool/
├── main.py                     # FastAPI entry point
├── config.py                   # Environment variable loader
├── celery_app.py               # Celery app config + beat schedule
├── mcp_cli.py                  # Standalone MCP chat CLI
│
├── api/routes/
│   └── webhooks.py             # Webhook endpoints (IG, WA, FB)
│
├── app/
│   └── mcp_tools.py            # MCP server, registers all tools
│
├── core/
│   ├── base_webhook_processor.py  # Template: parse → save → AI → dispatch
│   ├── insta_parse.py          # Instagram webhook parser
│   ├── whatsapp_parse.py       # WhatsApp webhook parser
│   └── facebook_parse.py       # Facebook webhook parser
│
├── models/
│   ├── base.py                 # SQLAlchemy declarative base
│   ├── database.py             # Engine, session, automap
│   ├── scheduled_post.py       # ScheduledPost model
│   └── webhook_repository.py   # Webhook events repository
│
├── tasks/
│   ├── instagram_tasks.py      # IG publish tasks
│   ├── whatsapp_tasks.py       # WA message tasks
│   ├── facebook_tasks.py       # FB post/message tasks
│   └── scheduler_tasks.py      # Beat: poll due posts, dispatch
│
├── service_handler/
│   ├── providers.py            # Anthropic Claude wrapper
│   ├── insta_service.py        # 20+ Instagram MCP tools
│   ├── whatsapp_service.py     # 5 WhatsApp MCP tools
│   ├── facebook_service.py     # 10 Facebook MCP tools
│   ├── schedule_service.py     # 5 Schedule CRUD tools
│   ├── excel_service.py        # 2 Excel tools
│   └── *_webhook_processor.py  # Platform-specific processors
│
├── scheduler/
│   └── excel_parser.py         # Excel → post dicts
│
├── utils/
│   ├── logger.py               # Rotating file + console logger
│   ├── graph.py                # Meta Graph API client
│   └── decorators.py           # MCP tool error handling
│
└── logs/                       # Runtime logs (app.log)
```

## Prerequisites

- Python >= 3.11
- PostgreSQL (running on localhost:5432)
- RabbitMQ (running on localhost:5672)

## Environment Setup

1. Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

2. Edit `.env` with your values:

## Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate (Window
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

### 1. FastAPI Server

```bash
uvicorn main:app --port 8000 --reload
```

### 2. Celery Worker

```bash
celery -A celery_app worker --loglevel=info --pool=solo
```

### 3. Celery Beat (Scheduler)

```bash
celery -A celery_app beat --loglevel=info
```

### 4. MCP CLI (Optional)

```bash
python mcp_cli.py
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/meta/webhook` | Instagram webhook verification |
| `POST` | `/meta/webhook` | Receive Instagram events |
| `GET` | `/whatsapp/webhook` | WhatsApp webhook verification |
| `POST` | `/whatsapp/webhook` | Receive WhatsApp events |
| `GET` | `/facebook/webhook` | Facebook webhook verification |
| `POST` | `/facebook/webhook` | Receive Facebook events |
| `GET` | `/mcp/sse` | MCP Server (SSE transport) |

## MCP Tools (42 total)

### Instagram (20)
`get_my_profile`, `list_my_media`, `list_all_media`, `get_media`, `list_tagged_media`, `list_stories`, `search_hashtag`, `hashtag_top_media`, `hashtag_recent_media`, `publish_image`, `publish_reel`, `publish_story`, `publish_carousel`, `list_comments`, `get_comment_replies`, `reply_to_comment`, `hide_comment`, `delete_comment`, `list_conversations`, `get_conversation`, `send_dm`, `get_account_insights`, `get_media_insights`

### WhatsApp (5)
`whatsapp_message`, `whatsapp_imagemessage`, `whatsapp_videomessage`, `whatsapp_documentmessage`, `whatsapp_templatemessage`

### Facebook (10)
`get_page_profile`, `create_page_post`, `list_page_posts`, `get_page_post`, `delete_page_post`, `list_page_comments`, `reply_to_page_comment`, `send_page_message`, `get_page_conversations`, `get_page_conversation`, `get_page_insights`

### Schedule (5)
`schedule_posts_from_excel`, `list_scheduled_posts`, `cancel_scheduled_post`, `update_scheduled_post`, `get_scheduled_post_status`

### Excel (2)
`update_excel_cell`, `read_excel_cell`

## Architecture

```
Meta Platforms (IG, WA, FB)
    ↑ Webhooks (inbound)    ↓ Graph API (outbound)
    ↓
FastAPI Routes ──→ Core Parsers ──→ AI Classify ──→ Auto-Reply
                                      ↓
                               PostgreSQL DB
                               (webhook_events, scheduled_posts)

MCP Server (SSE) ──→ service_handler/ ──→ Graph API / DB / Excel

Celery Beat (60s) ──→ scheduler_tasks ──→ Celery Tasks ──→ Graph API
```

## Database

PostgreSQL with `meta` schema:

- **webhook_events** — Stores inbound/outbound webhook events with full payload JSON
- **scheduled_posts** — Tracks scheduled posts with status (`pending`, `scheduled`, `completed`, `failed`, `cancelled`)

## Celery Tasks

| Task | Platform | Purpose |
|---|---|---|
| `publish_image_task` | Instagram | Publish image post |
| `publish_reel_task` | Instagram | Publish reel (with container wait) |
| `publish_story_task` | Instagram | Publish story |
| `publish_carousel_task` | Instagram | Publish carousel (2-10 items) |
| `whatsapp_message_task` | WhatsApp | Send text message |
| `whatsapp_image_task` | WhatsApp | Send image message |
| `whatsapp_video_task` | WhatsApp | Send video message |
| `create_page_post_task` | Facebook | Create page post |
| `send_page_message_task` | Facebook | Send messenger message |
| `check_and_enqueue_posts` | All | Beat task: poll due posts every 60s |
