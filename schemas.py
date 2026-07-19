from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TicketIn(BaseModel):
    source: str
    raw_text: str
    customer_id: Optional[str] = None


class ClassificationResult(BaseModel):
    intent: str
    priority: str
    confidence: float
    suggested_department: str
    auto_response: Optional[str] = None


class TicketOut(BaseModel):
    id: int
    source: str
    raw_text: str
    customer_id: Optional[str]
    intent: Optional[str]
    priority: Optional[str]
    confidence: Optional[float]
    suggested_department: Optional[str]
    auto_response: Optional[str]
    status: str
    human_reviewed: bool
    created_at: datetime

    class Config:
        from_attributes = True
