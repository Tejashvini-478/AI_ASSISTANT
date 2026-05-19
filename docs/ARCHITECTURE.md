# System Architecture

## Overview

The Business Automation Assistant is a monolithic Streamlit application with a modular Python backend. All business logic lives under `src/`; `app.py` orchestrates pages and user flows.

## Component diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend (app.py)                  │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │   Home   │  │ AI Assistant │  │Lead Capture │  │   Admin   │ │
│  └────┬─────┘  └──────┬───────┘  └──────┬──────┘  └─────┬─────┘ │
└───────┼───────────────┼─────────────────┼───────────────┼────────┘
        │               │                 │               │
        ▼               ▼                 ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Service Layer (src/)                     │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐  │
│  │  chatbot.py │    │  automation.py   │    │  database.py    │  │
│  │  LLM calls  │    │  email + logging │    │  SQLite CRUD    │  │
│  └──────┬──────┘    └────────┬─────────┘    └────────┬────────┘  │
│         │                    │                       │            │
│  ┌──────┴────────────────────┴───────────────────────┴──────┐    │
│  │                      config.py                            │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
        │                    │                       │
        ▼                    ▼                       ▼
   OpenAI / Gemini      SMTP Server          data/business_assistant.db
                        automation.log
```

## Data model

### `leads`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| name, email | TEXT | Required |
| phone, company, interest, message | TEXT | Optional |
| created_at | TEXT ISO UTC | Timestamp |

### `chat_logs`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| session_id | TEXT | Per-conversation ID |
| role | TEXT | `user` or `assistant` |
| content | TEXT | Message body |
| created_at | TEXT | |

### `automation_events`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| event_type | TEXT | e.g. `lead_notification`, `chat_auto_response` |
| payload | TEXT JSON | Event context |
| status | TEXT | e.g. `email_sent`, `logged` |
| created_at | TEXT | |

## Request flows

### Chat message flow

1. User enters prompt in Streamlit chat UI.
2. `app.py` appends to session history and calls `log_chat()`.
3. `generate_reply()` in `chatbot.py` selects OpenAI, Gemini, or fallback.
4. Assistant text is displayed, logged to `chat_logs`, and `on_chat_interaction()` records an automation event.

### Lead submission flow

1. User submits validated form.
2. `insert_lead()` writes to SQLite.
3. `send_lead_notification()` attempts SMTP email; always writes automation event and file log.

## Security considerations

- Admin dashboard protected by `ADMIN_PASSWORD`.
- API keys and SMTP credentials via environment variables only.
- Do not commit `.env` or Streamlit secrets to Git.

## Scalability notes

Current design targets assessment scope. For production:

- Replace SQLite with PostgreSQL for multi-instance deploys.
- Add rate limiting on chat endpoint.
- Use a job queue (Celery, RQ) for email retries.
