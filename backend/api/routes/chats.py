from __future__ import annotations

from fastapi import APIRouter, Body, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from models.engine import get_db
from service_handler.conversation_handler import ConversationHandler
from service_handler.message_handler import MessageHandler
from service_handler.file_upload_handler import FileUploadHandler

chat_routes = APIRouter()


@chat_routes.get("/chats")
def list_chats(db: Session = Depends(get_db)):
    return ConversationHandler(db).list_conversations()


@chat_routes.get("/chats/search")
def search_chats(q: str = "", db: Session = Depends(get_db)):
    return ConversationHandler(db).search_conversations(q)


@chat_routes.post("/chats/create")
def create_chat(title: str = Body("New Chat", embed=True), db: Session = Depends(get_db)):
    return ConversationHandler(db).create_conversation(title)


@chat_routes.get("/chats/{conv_id}")
def get_chat(conv_id: int, page: int = 1, limit: int = 0, db: Session = Depends(get_db)):
    return MessageHandler(db).get_chat_detail(conv_id, page, limit)


@chat_routes.delete("/chats/{conv_id}")
def delete_chat(conv_id: int, db: Session = Depends(get_db)):
    return ConversationHandler(db).delete_conversation(conv_id)


@chat_routes.patch("/chats/{conv_id}")
def update_chat(conv_id: int, payload: dict, db: Session = Depends(get_db)):
    return ConversationHandler(db).update_conversation(conv_id, payload)


# @chat_routes.post("/upload")
# async def upload_file(file: UploadFile = File(...), conv_id: int | None = Body(None)):
#     return await FileUploadHandler().upload_file(file, conv_id)


@chat_routes.post("/chats/new/messages")
async def send_message(conv_id: int | None = None, message: str = Body(embed=True), file: UploadFile | None = File(None), db: Session = Depends(get_db)):
    print(message, "message")
    return await MessageHandler(db).send_message(conv_id, message, file)


@chat_routes.post("/chats/{conv_id}/messages")
async def send_message_to_chat(conv_id: int, message: str = Body(embed=True), file: UploadFile | None = File(None), db: Session = Depends(get_db)):

    return await MessageHandler(db).send_message(conv_id, message, file)


# @chat_routes.post("/chats/new/upload-message")
# async def upload_and_message_new(message: str | None = Form(None), file: UploadFile | None = File(None)):
#     return await FileUploadHandler().upload_and_send_message(None, message, file)


# @chat_routes.post("/chats/{conv_id}/upload-message")
# async def upload_and_message(conv_id: int, message: str | None = Form(None), file: UploadFile | None = File(None)):
#     return await FileUploadHandler().upload_and_send_message(conv_id, message, file)
