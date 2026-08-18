from __future__ import annotations

from typing import Any
import os
import base64

import httpx
from anthropic import APIError as AnthropicError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.chat_core import ChatCore
from mcp_cli import DEFAULT_SYSTEM_PROMPT

from models.conversation import ConversationRepository
from models.message import MessagesRepository
from models.document_metadata import DocMetadataRepository
from service_handler.conversation_handler import ConversationHandler
from utils.logger import logger
from config import CLIENT, ANTHROPIC_MODEL,BASE_URL


class MessageHandler:
    
    def __init__(self, db: Session):
        self.db = db

    async def generate_response(self, conversation: list[dict[str, Any]]) -> str:
        chat = ChatCore(DEFAULT_SYSTEM_PROMPT)
        return await chat.chat_once(conversation, CLIENT, ANTHROPIC_MODEL)

    def _generate_file_url(self, file_path: str) -> str:
        # Construct the public URL for a file using BASE_URL and filename.
        filename = os.path.basename(file_path)
        return f"{BASE_URL}/uploads/{filename}" if BASE_URL else ""

    def _build_upload_content(self, user_message: str, file_id: int) -> tuple[str, str]:
        # Fetch doc metadata and return (content, message_type) for DB storage.
        doc_repository = DocMetadataRepository(self.db)
        docs = doc_repository.get_metadata([file_id])
        if file_id not in docs:
            raise ValueError(f"File {file_id} not found")
        message_type = "image" if docs[file_id]["mime_type"].startswith("image") else "file"
        return user_message or "File uploaded", message_type

    def _build_ai_content(self, message: dict, docs: dict) -> str | list:
        # Build Anthropic content: image/document block + text with public file URL.
        if message["id"] not in docs:
            return message["content"]
        doc = docs[message["id"]]
        file_block = self._build_file_content(doc)
        if not file_block:
            return message["content"]
        url = self._generate_file_url(doc["file_path"])
        # print("url--------------------------",url)
        text = message["content"]
        if url:
            text += f"\n\nFile URL: {url}"
        return [file_block, {"type": "text", "text": text}]

    def build_message_content(self, user_message: str = "", file_id: int | None = None, *, message: dict | None = None, docs: dict | None = None):
        if message is not None:
            return self._build_ai_content(message, docs)
        if not file_id:
            return user_message, "text"
        return self._build_upload_content(user_message, file_id)

    def _build_file_content(self, doc: dict) -> dict | None:
        # Read file from disk and return an Anthropic image/document content block, or None.
        try:
            mime = doc["mime_type"]
            if not (mime.startswith("image/") or mime == "application/pdf"):
                return None
            file_path = doc["file_path"]
            if not os.path.exists(file_path):
                logger.warning("File not found: %s", file_path)
                return None
            with open(file_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
                print(data[:100])
            if mime.startswith("image/"):
                return {"type": "image", "source": {"type": "base64", "media_type": mime, "data": data}}
            return {"type": "document", "source": {"type": "base64", "media_type": mime, "data": data}}
        except Exception:
            logger.exception("_build_file_content failed")
            return None

    def build_ai_history(self, conv_id: int) -> list[dict[str, Any]]:
        messages = MessagesRepository(self.db).list_messages(conv_id, limit=0)
        file_msg_ids = [m["id"] for m in messages if m["message_type"] in ("image", "file") and m["role"] == "user"]
        docs = DocMetadataRepository(self.db).get_metadata(file_msg_ids) if file_msg_ids else {}
        return [{"role": m["role"], "content": self.build_message_content(message=m, docs=docs)} for m in messages]

    async def send_message(self, conv_id: int | None = None, user_message: str = "", file: UploadFile | None = None) -> dict[str, Any]:
        try:
            from service_handler.file_upload_handler import FileUploadHandler
            
            fileupload=FileUploadHandler(self.db)
            conv_id, _ = ConversationHandler(self.db).chk_and_create(conv_id, user_message)
            message_repository = MessagesRepository(self.db)
            file_id = None 
            if file:
                file_id = (await fileupload.upload_file(file, conv_id))["file_id"]

            content, message_type = self.build_message_content(user_message, file_id)
            message_repository.create_message(conv_id, "user", content, message_type)
            
            history = self.build_ai_history(conv_id)
            answer = await self.generate_response(history)
            message_repository.create_message(conv_id, "assistant", answer, "text")
            message_repository.save()

            return {"conv_id": conv_id, "role": "assistant", "content": answer}
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except (AnthropicError, httpx.HTTPError) as e:
            logger.exception("AI service error")
            raise HTTPException(status_code=502, detail="AI service is temporarily unavailable. Please try again.")
        except Exception:
            logger.exception("send_message failed")
            raise HTTPException(status_code=502, detail="Something went wrong while generating the reply. Please try again.")

    def get_chat_detail(self, conv_id: int, page: int = 1, limit: int = 2) -> dict[str, Any]:
        #Return conversation with paginated messages and file metadata.
        try:
            conversation_repository = ConversationRepository(self.db)
            conv = conversation_repository.get_conversation(conv_id)
            if not conv:
                raise ValueError(f"Conversation {conv_id} not found")
            message_repository = MessagesRepository(self.db)
            doc_metadata_repository = DocMetadataRepository(self.db)
            messages = message_repository.list_messages(conv_id, page, limit)
            file_msgs = [m for m in messages if m["message_type"] in ("file", "image")]
            if file_msgs:
                docs = doc_metadata_repository.get_metadata([m["id"] for m in file_msgs])
                for m in messages:
                    if m["id"] in docs:
                        m["document"] = docs[m["id"]]
            conv["messages"] = messages
            return conv
        except Exception:
            logger.exception("get_chat_detail failed")
            raise
