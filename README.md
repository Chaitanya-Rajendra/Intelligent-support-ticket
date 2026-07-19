# Intelligent Support Ticket Triage & Auto-Resolution System

Automated pipeline that classifies incoming support tickets, scores priority/confidence via an LLM, auto-resolves simple cases, and routes everything else to the right team — with a human-in-the-loop fallback for low-confidence classifications.

## Architecture

```
Ticket sources (email/chat/form)
        │
        ▼
   n8n Webhook  ──────────────►  FastAPI /tickets endpoint
        │                              │
        │                              ▼
        │                     LLM classification
        │                     (intent, priority,
        │                      confidence, dept,
        │                      auto-response)
        │                              │
        │                              ▼
        │                     PostgreSQL (audit log)
        │                              │
        ▼                              │
  Auto-resolved? ◄─────────────────────┘
   ├─ Yes → Send auto-response email
   └─ No  → Notify support channel (Slack) / human review queue
```

## Stack
- **n8n** – ingestion, orchestration, routing, notifications
- **FastAPI** – classification API + persistence layer
- **PostgreSQL** – ticket + audit log storage
- **OpenAI API** – intent/priority classification via prompt-engineered calls

## Setup

1. Clone and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your OpenAI key + database URL.
3. Start PostgreSQL (or use Docker):
   ```bash
   docker run --name triage-db -e POSTGRES_PASSWORD=password -e POSTGRES_DB=ticket_triage -p 5432:5432 -d postgres
   ```
4. Run the API:
   ```bash
   uvicorn backend.main:app --reload
   ```
5. Import `n8n/ticket-triage-workflow.json` into your n8n instance and point the HTTP Request node at your running FastAPI URL.

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/tickets` | Ingest + classify a new ticket |
| GET | `/tickets` | List recent tickets (filter by `?status=`) |
| GET | `/tickets/{id}` | Get a single ticket |
| POST | `/tickets/{id}/review` | Mark a low-confidence ticket as human-reviewed |
| GET | `/stats` | Auto-resolution rate and volume metrics |

### Sample request
```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"source": "email", "raw_text": "I forgot my password and cant log in", "customer_id": "cust_123"}'
```

### Sample response
```json
{
  "id": 1,
  "source": "email",
  "raw_text": "I forgot my password and cant log in",
  "customer_id": "cust_123",
  "intent": "login_problem",
  "priority": "medium",
  "confidence": 0.91,
  "suggested_department": "technical_support",
  "auto_response": "Hi! You can reset your password from the login page by clicking 'Forgot Password'...",
  "status": "auto_resolved",
  "human_reviewed": false,
  "created_at": "2026-07-19T10:00:00"
}
```

## Notes
- The confidence threshold for auto-resolution is configurable via `CONFIDENCE_THRESHOLD` in `.env` (default 0.75).
- Every classification is logged to PostgreSQL for traceability, even auto-resolved ones.
- `prompts/classification_prompt.txt` holds the prompt template — iterate here to improve accuracy without touching code.
