from __future__ import annotations

from models.database import SessionLocal,ScheduledPost



class ScheduledPostRepository:
    
    model=ScheduledPost
    
    
    def get_session(self):
        return SessionLocal()
    
    def save(self,session,post:dict)->row:
        row = self.model(
            post_type=post["post_type"],
            platform=post["platform"],
            scheduled_time=post["scheduled_time"],
            media_url=post.get("media_url"),
            message=post.get("message"),
            topic=post.get("topic"),
            recipient_id=post.get("recipient_id"),
            location_id=post.get("location_id"),
            status=post.get("status", "pending"),
            task_id=post.get("task_id"),
            result=post.get("result"),
            error_message=post.get("error_message"),
        )

        session.add(row)
        # session.commit()
        session.refresh(row)
        return row
    
    def to_dict(self,row)->dict:
        return{
            "id":row.id,
            "post_type":row.post_type,
            "platform":row.platform,
            "media_url":row.media_url,
            "message":row.message,
            "topic":row.topic,
            "recipient_id":row.recipient_id,
            "location_id":row.location_id,
            "scheduled_time":row.scheduled_time.isoformat() if row.scheduled_time else None,
            "status":row.status,
            "task_id":row.task_id,
            "result":row.result,
            "error_message":row.error_message,
        }
    







# class ScheduledPost(Base):
#     __tablename__ = "scheduled_posts"
#     __table_args__ = {"schema": "meta"}

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     post_type = Column(String(50), nullable=False)
#     platform = Column(String(50), nullable=False)
#     media_url = Column(Text, nullable=True)
#     message = Column(Text, nullable=True)
#     topic = Column(Text, nullable=True)
#     recipient_id = Column(Text, nullable=True)
#     location_id = Column(Text, nullable=True)
#     scheduled_time = Column(DateTime(timezone=False), nullable=False)
#     status = Column(String(50), default="pending")
#     task_id = Column(String(255), nullable=True)
#     result = Column(JSON, nullable=True)
#     error_message = Column(Text, nullable=True)
#     created_at = Column(DateTime(timezone=False), server_default=func.now())
#     updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

#     def to_dict(self) -> dict[str, Any]:
#         return {
#             "id": self.id,
#             "post_type": self.post_type,
#             "platform": self.platform,
#             "media_url": self.media_url,
#             "message": self.message,
#             "topic": self.topic,
#             "recipient_id": self.recipient_id,
#             "location_id": self.location_id,
#             "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
#             "status": self.status,
#             "task_id": self.task_id,
#             "result": self.result,
#             "error_message": self.error_message,
#             "created_at": self.created_at.isoformat() if self.created_at else None,
#         }
