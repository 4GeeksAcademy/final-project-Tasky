from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

db = SQLAlchemy()

class Review(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    review: Mapped[str] = mapped_column(String(10000), nullable=True)
    rate: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    publisher_id: Mapped[int] = mapped_column(ForeignKey('user.id'), unique=True, nullable=False)
    worker_id: Mapped[int] = mapped_column(ForeignKey('user.id'), unique=True, nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey('task.id'), unique=True, nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "review": self.review,
            "rate": self.rate,
            "created_at": self.created_at,
            "worker_id": self.worker_id,
            "task_id": self.task_id,
            # do not serialize the password, its a security breach
        }
    
class Message(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[str] = mapped_column(String(100000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dealed_id: Mapped[int] = mapped_column(ForeignKey('task_dealed.id'), unique=True, nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey('user.id'), unique=True, nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "body": self.body,
            "created_at": self.created_at,
            "dealed_id": self.dealed_id,
            "sender_id": self.sender_id,
            # do not serialize the password, its a security breach
        }

class Dispute(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    details: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    resolution: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dealed_id: Mapped[int] = mapped_column(ForeignKey('task_dealed.id'), unique=True, nullable=False)
    raised_by: Mapped[int] = mapped_column(ForeignKey('user.id'), unique=True, nullable=False)
    resolved_by_admin_user: Mapped[int] = mapped_column(ForeignKey('user.id'), unique=True, nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "reason": self.reason,
            "details": self.details,
            "status": self.status,
            "resolution": self.resolution,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "dealed_id": self.dealed_id,
            "raised_by": self.raised_by,
            "resolved_by_admin_user": self.resolved_by_admin_user,
        }
    
class Admin_action(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dispute_id: Mapped[int] = mapped_column(ForeignKey('dispute.id'), unique=True, nullable=False)
    admin_user: Mapped[int] = mapped_column(ForeignKey('user.id'), unique=True, nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "action": self.action,
            "created_at": self.created_at,
            "dispute_id": self.dispute_id,
            "admin_user": self.admin_user,
            # do not serialize the password, its a security breach
        }