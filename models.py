import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Enum, Boolean
from .database import Base


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class Status(str, enum.Enum):
    open = "open"
    auto_resolved = "auto_resolved"
    routed = "routed"
    needs_review = "needs_review"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)              # e.g. email, chat, form
    raw_text = Column(Text, nullable=False)
    customer_id = Column(String, nullable=True)

    # LLM classification results
    intent = Column(String, nullable=True)
    priority = Column(Enum(Priority), nullable=True)
    confidence = Column(Float, nullable=True)
    suggested_department = Column(String, nullable=True)
    auto_response = Column(Text, nullable=True)

    status = Column(Enum(Status), default=Status.open)
    human_reviewed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
