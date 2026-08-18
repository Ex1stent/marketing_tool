from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.conversation import ConversationRepository
from models.engine import row_to_dict
from utils.logger import logger


class ConversationHandler:

    def __init__(self, db: Session):
        self.db = db

    def generate_title(self, payload):
        # Extract first 100 chars of user message as conversation title.
        user_message = payload.get("user_message")
        title = user_message[:100] + ("..." if len(user_message) > 100 else "")
        return title

    def create_conversation(self, title: str = "New Chat") -> dict[str, Any]:
        conversation_repository = ConversationRepository(self.db)
        conv = conversation_repository.create({"title": title})
        conversation_repository.save()
        return row_to_dict(conv)

    def list_conversations(self, page: int = 1, limit: int = 20) -> list[dict[str, Any]]:
        # List conversations with pagination.
        try:
            conversation_repository = ConversationRepository(self.db)
            return conversation_repository.list_all(page, limit)
        except Exception:
            logger.exception("list_conversations failed")
            raise

    def search_conversations(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        # Search conversations by title.
        try:
            conversation_repository = ConversationRepository(self.db)
            return conversation_repository.search(query, limit)
        except Exception:
            logger.exception("search_conversations failed")
            raise

    def get_conversation(self, conv_id: int) -> dict[str, Any] | None:
        if not conv_id:
            raise ValueError("conv_id is required")
        conversation_repository = ConversationRepository(self.db)
        return conversation_repository.get_conversation(conv_id)

    def delete_conversation(self, conv_id: int) -> bool:
        # Delete a conversation and return True. Raises ValueError if not found.
        try:
            conversation_repository = ConversationRepository(self.db)
            deleted = conversation_repository.delete(conv_id)
            if not deleted:
                raise ValueError(f"Conversation {conv_id} not found")
            conversation_repository.save()
            return True
        except Exception:
            logger.exception("delete_conversation failed")
            raise

    def update_conversation(self, conv_id: int, payload: dict) -> dict[str, Any]:
        # Update conversation fields (e.g. title). Raises ValueError if not found.
        try:
            conversation_repository = ConversationRepository(self.db)
            if not conversation_repository.get_conversation(conv_id):
                raise ValueError(f"Conversation {conv_id} not found")
            conversation_repository.update(conv_id, payload)
            conversation_repository.save()
            return conversation_repository.get_conversation(conv_id)
        except Exception:
            logger.exception("update_conversation failed")
            raise

    def chk_and_create(self, conv_id: int | None, user_message: str) -> tuple[int, ConversationRepository]:
        conv = self.get_conversation(conv_id) if conv_id else None
        conversation_repository = ConversationRepository(self.db)

        if conv:
            conv_id = conv.get("id")
            if conv.get("title") == "New Chat":
                title = self.generate_title({"user_message": user_message})
                conversation_repository.update(conv_id, {"title": title})
        else:
            title = self.generate_title({"user_message": user_message})
            new_conv = self.create_conversation(title)
            conv_id = new_conv.get("id")

        return conv_id, conversation_repository
