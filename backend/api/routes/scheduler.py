from __future__ import annotations

import os

from fastapi import APIRouter, Body, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from models.engine import get_db
from service_handler.scheduler_handler import SchedulerHandler
from config import TEMPLATE_PATH

scheduler_routes = APIRouter()


@scheduler_routes.get("/scheduler/stats")
def get_stats(db: Session = Depends(get_db)):
    return SchedulerHandler(db).get_stats()


@scheduler_routes.post("/scheduler/uploadexcel")
async def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await SchedulerHandler(db).upload_excel(file)


@scheduler_routes.get("/scheduler/posts")
def list_posts(status: str | None = None, batch_id: int | None = None, db: Session = Depends(get_db)):
    return SchedulerHandler(db).list_posts(status, batch_id)


# @scheduler_routes.patch("/scheduler/posts/{post_id}")
# def update_post(post_id: int, body: dict = Body(default={}), db: Session = Depends(get_db)):
#     return SchedulerHandler(db).update_post(post_id, **body)


@scheduler_routes.post("/scheduler/posts/{post_id}/cancel")
def cancel_post(post_id: int, db: Session = Depends(get_db)):
    return SchedulerHandler(db).cancel_post(post_id)


@scheduler_routes.get("/scheduler/batches")
def get_batches(db: Session = Depends(get_db)):
    return SchedulerHandler(db).get_batches()


@scheduler_routes.get("/scheduler/batches/{batch_id}/posts")
def get_batch_posts(batch_id: int, db: Session = Depends(get_db)):
    return SchedulerHandler(db).get_batch_posts(batch_id)


@scheduler_routes.delete("/scheduler/batches/{batch_id}")
def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    return SchedulerHandler(db).delete_batch(batch_id)


@scheduler_routes.get("/scheduler/template")
def download_template():
    return FileResponse(TEMPLATE_PATH, filename="scheduler_template.xlsx")


@scheduler_routes.post("/scheduler/batches/{batch_id}/schedule")
def schedule_batch(batch_id: int, db: Session = Depends(get_db)):
    return SchedulerHandler(db).schedule_batch(batch_id)
