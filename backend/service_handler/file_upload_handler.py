from __future__ import annotations

from typing import Any
from config import UPLOAD_DIR
import uuid
import os
from fastapi import UploadFile
from sqlalchemy.orm import Session

from models.document_metadata import DocMetadataRepository
from utils.logger import logger


class FileUploadHandler:

    ALLOWED_TYPES = {"image/jpeg", "image/png", "application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def validate_file(file: UploadFile) -> None:
        if not file.filename:
            raise ValueError("No filename provided")
        if file.content_type not in FileUploadHandler.ALLOWED_TYPES:
            raise ValueError(f"File type '{file.content_type}' not allowed. Use: jpg, png, pdf, xlsx")
        if "." not in file.filename:
            raise ValueError("File must have an extension")

    @staticmethod
    def generate_filename(original_name: str) -> str:
        #Generate a unique filename using UUID to avoid collisions.
        return f"{uuid.uuid4().hex}-{original_name}"

    @staticmethod
    def save_to_disk(filename: str, content: bytes) -> str:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(content)
        return filepath

    def save_doc_metadata(self, message_id: int, filename: str, filepath: str, ext: str, content_type: str, size: int) -> None:
        doc_repository = DocMetadataRepository(self.db)
        doc_repository.add_metadata(
            message_id=message_id, 
            file_name=filename, 
            file_path=filepath,
            file_extension=ext, 
            mime_type=content_type, 
            file_size=size
        )
        doc_repository.save()

    async def upload_file(self, file: UploadFile, conv_id: int | None = None) -> dict[str, Any]:
        self.validate_file(file)
        content = await file.read()
        if len(content) > self.MAX_SIZE:
            raise ValueError("File size exceeds")
        
        filename = self.generate_filename(file.filename)
        filepath = self.save_to_disk(filename, content)
        extension = file.filename.rsplit(".", 1)[-1]
        
        return {
            "file_name": file.filename,
            "file_path": filepath,
            "file_extension": extension,
            "mime_type": file.content_type,
            "file_size": len(content),
        }

    # async def upload_and_send_message(self, conv_id: int | None, message: str | None, file: UploadFile | None) -> dict[str, Any]:
    #     # Upload file (if provided) then send message to AI in one call.
    #     try:
    #         file_id = None
    #         if file:
    #             file_id = (await self.upload_file(file, conv_id))["file_id"]
    #         if not message:
    #             message = "Analyze this image" if file else "Hello"
    #         return await MessageHandler().send_message(conv_id, message, file_id)
    #     except Exception:
    #         logger.exception("upload_and_send_message failed")
    #         raise
