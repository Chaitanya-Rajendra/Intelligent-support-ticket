import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas
from .database import engine, get_db
from .classifier import classify_ticket

load_dotenv()

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.75))

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Intelligent Support Ticket Triage & Auto-Resolution System")


@app.post("/tickets", response_model=schemas.TicketOut)
def ingest_ticket(payload: schemas.TicketIn, db: Session = Depends(get_db)):
    """
    Entry point called by n8n (or any channel) when a new ticket arrives.
    Classifies the ticket via LLM, decides routing, and persists the result.
    """
    classification = classify_ticket(payload.raw_text)

    ticket = models.Ticket(
        source=payload.source,
        raw_text=payload.raw_text,
        customer_id=payload.customer_id,
        intent=classification["intent"],
        priority=classification["priority"],
        confidence=classification["confidence"],
        suggested_department=classification["suggested_department"],
        auto_response=classification.get("auto_response"),
    )

    # Routing decision
    if classification.get("auto_response") and classification["confidence"] >= CONFIDENCE_THRESHOLD:
        ticket.status = models.Status.auto_resolved
    elif classification["confidence"] < CONFIDENCE_THRESHOLD:
        ticket.status = models.Status.needs_review
    else:
        ticket.status = models.Status.routed

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/tickets", response_model=list[schemas.TicketOut])
def list_tickets(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Ticket)
    if status:
        query = query.filter(models.Ticket.status == status)
    return query.order_by(models.Ticket.created_at.desc()).limit(100).all()


@app.get("/tickets/{ticket_id}", response_model=schemas.TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.post("/tickets/{ticket_id}/review", response_model=schemas.TicketOut)
def mark_reviewed(ticket_id: int, db: Session = Depends(get_db)):
    """Human-in-the-loop endpoint: mark a low-confidence ticket as reviewed."""
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.human_reviewed = True
    ticket.status = models.Status.routed
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Basic metrics: useful for the resume line 'auto-resolved X% of tickets'."""
    total = db.query(func.count(models.Ticket.id)).scalar()
    auto_resolved = db.query(func.count(models.Ticket.id)).filter(
        models.Ticket.status == models.Status.auto_resolved
    ).scalar()
    needs_review = db.query(func.count(models.Ticket.id)).filter(
        models.Ticket.status == models.Status.needs_review
    ).scalar()

    return {
        "total_tickets": total,
        "auto_resolved": auto_resolved,
        "auto_resolution_rate": round(auto_resolved / total, 3) if total else 0,
        "needs_human_review": needs_review,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
