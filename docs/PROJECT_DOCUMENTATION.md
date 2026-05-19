# AI-Powered Business Automation Assistant — Project Documentation

## 1. Executive Summary

The **AI-Powered Business Automation Assistant** is a web-based business support system designed to help training and consulting organizations interact with prospects, capture leads, automate follow-up workflows, and monitor activity through an admin interface. The application combines a conversational AI assistant (powered by large language models), structured lead capture, persistent data storage, rule-based and event-driven automation, and a password-protected administrative dashboard.

The system is built with **Python** and **Streamlit**, uses **SQLite** for data persistence, integrates with **Google Gemini** (or optionally **OpenAI**) for intelligent responses, and can be deployed publicly on **Streamlit Community Cloud** without Docker.

---

## 2. Problem Statement & Objectives

### 2.1 Problem Statement

Small and mid-sized businesses offering courses or consulting services often lack an integrated tool that:

- Answers repetitive questions about programs and services 24/7
- Captures visitor contact information in a structured way
- Triggers follow-up actions (notifications, logging) automatically
- Provides staff with a single view of leads and conversations

### 2.2 Project Objectives

| Objective | How It Is Met |
|-----------|----------------|
| Intelligent user interaction | AI chatbot for business/course-related queries |
| Lead management | Validated lead capture form with persistent storage |
| Data storage | SQLite database with export capability |
| Automation | Workflows on lead submit and chat interactions |
| Operational visibility | Admin dashboard with metrics and tables |
| Deployability | Streamlit Cloud–ready configuration |

---

## 3. Scope & Features

### 3.1 In Scope

- Multi-page Streamlit web application
- AI-powered chat with conversation history (session-based)
- Lead capture form with required field validation
- SQLite storage for leads, chat logs, and automation events
- Automation: database logging, file logging, optional email notifications
- Admin dashboard with authentication, data tables, and CSV export
- Environment-based configuration (API keys, SMTP, admin password)
- Demo/fallback mode when no LLM API key is configured
- Quota-aware fallback when LLM API limits are exceeded

### 3.2 Out of Scope (Current Version)

- User registration/login for end visitors
- Payment processing or CRM integrations
- Vector database / RAG document search
- Docker containerization (per project constraints)
- Multi-tenant or role-based admin roles

---

## 4. System Architecture

### 4.1 Architectural Style

The application follows a **modular monolith** pattern:

- **Presentation layer:** Streamlit UI (`app.py`)
- **Service layer:** Python modules under `src/`
- **Data layer:** SQLite database and flat-file automation log
- **External integrations:** Gemini/OpenAI APIs, optional SMTP

### 4.2 High-Level Architecture Diagram

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Browser[Web Browser]
    end

    subgraph Presentation["Presentation Layer"]
        ST[Streamlit - app.py]
        Pages[Home | AI Assistant | Lead Capture | Admin]
    end

    subgraph Services["Service Layer"]
        CB[src/chatbot.py]
        AUTO[src/automation.py]
        DBL[src/database.py]
        CFG[src/config.py]
    end

    subgraph Persistence["Persistence Layer"]
        SQLite[(SQLite DB)]
        FileLog[automation.log]
    end

    subgraph External["External Services"]
        Gemini[Google Gemini API]
        OpenAI[OpenAI API - optional]
        SMTP[SMTP Email Server - optional]
    end

    Browser --> ST
    ST --> Pages
    Pages --> CB
    Pages --> AUTO
    Pages --> DBL
    CB --> CFG
    AUTO --> CFG
    DBL --> CFG
    CB --> Gemini
    CB --> OpenAI
    DBL --> SQLite
    AUTO --> SQLite
    AUTO --> FileLog
    AUTO --> SMTP
```

### 4.3 Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| Main application | `app.py` | Routing, UI pages, session state, orchestration |
| Configuration | `src/config.py` | Environment variables, paths, system prompt |
| Database | `src/database.py` | Schema init, CRUD, statistics |
| Chatbot | `src/chatbot.py` | LLM provider selection, message generation, fallbacks |
| Automation | `src/automation.py` | Email notifications, event logging, file audit trail |

---

## 5. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Language | Python 3.10+ | Core implementation |
| Web framework | Streamlit 1.32+ | UI, forms, chat widget, dashboard |
| AI / LLM | Google Gemini (`gemini-2.5-flash`) | Primary intelligent responses |
| AI / LLM (alt.) | OpenAI (`gpt-4o-mini`) | Optional provider |
| Database | SQLite 3 | Leads, chats, automation events |
| Data analysis | Pandas | Admin tables and CSV export |
| Configuration | python-dotenv | Load `.env` locally |
| Email | smtplib (stdlib) | Optional lead notifications |

---

## 6. Functional Modules (Detailed)

### 6.1 AI Assistant / Chatbot

**Purpose:** Answer business and course-related questions using an LLM.

**User flow:**

1. User navigates to **AI Assistant**
2. User types a message in the chat input
3. System logs the user message to `chat_logs`
4. System sends conversation history to the configured LLM
5. Assistant reply is displayed, logged, and triggers automation logging

**LLM behavior:**

- **System prompt** defines the assistant as a business/training consultant helper
- **Provider priority:** Configured via `LLM_PROVIDER` (`gemini` or `openai`)
- **Auto-fallback:** If preferred provider has no API key, switches to the other if available
- **Demo mode:** Rule-based responses when no API keys exist
- **Quota fallback:** If API returns rate-limit/quota errors, returns guided fallback text with a notice

**Session management:** Each browser session receives a unique `session_id` (UUID fragment) to group chat logs.

### 6.2 Lead Capture System

**Purpose:** Collect prospect contact details through a structured form.

**Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| Full name | Yes | Contact name |
| Email | Yes | Validated for `@` presence |
| Phone | No | Contact number |
| Company | No | Organization name |
| Area of interest | No | Dropdown (courses, consulting, etc.) |
| Message | No | Free-text inquiry |

**On submit:**

1. Server-side validation
2. Insert into `leads` table
3. Trigger `send_lead_notification()` automation workflow
4. Display success or partial-success message to user

### 6.3 Data Storage

**Storage method:** SQLite relational database at `data/business_assistant.db`

**Tables:**

#### `leads`
Stores form submissions with timestamp.

#### `chat_logs`
Stores every user and assistant message with `session_id`, `role`, and `content`.

#### `automation_events`
Audit trail for automated actions (`event_type`, JSON `payload`, `status`, `created_at`).

**Additional persistence:** `data/automation.log` — human-readable append-only log for automation actions.

**Export:** Admin dashboard provides **Export leads CSV** for reporting.

### 6.4 Automation Workflows

#### Workflow A: Lead Capture → Notification & Logging

```
Form Submit → insert_lead() → send_lead_notification()
                                    ├── If SMTP configured → send email to NOTIFY_EMAIL
                                    ├── log_automation("lead_notification", ...)
                                    └── append to automation.log
```

**Statuses recorded:** `email_sent`, `email_skipped_no_smtp_config`, or `email_failed: <reason>`

#### Workflow B: Chat Interaction → Auto-Response & Logging

```
User Message → generate_reply() → Display Response
                      ├── log_chat(user)
                      ├── log_chat(assistant)
                      └── on_chat_interaction() → automation_events + automation.log
```

These workflows satisfy the assessment requirement for at least one automation workflow; this project implements **two**.

### 6.5 Admin Dashboard

**Purpose:** Internal view of system data and metrics.

**Authentication:** Password gate using `ADMIN_PASSWORD` (default `admin123` for development; must be changed in production).

**Features:**

- Summary metrics: total leads, chat messages, automation events
- Tabbed views: Leads, Chat logs, Automation events
- CSV export for leads
- Logout control

---

## 7. Data Model (Entity Relationship Overview)

```
leads (1) ── independent records per submission

chat_logs (N) ── grouped by session_id

automation_events (N) ── independent audit records
```

No foreign keys between tables in v1; correlation is logical (timestamps, session_id) rather than relational.

---

## 8. Configuration Reference

Environment variables (`.env` locally, Streamlit Secrets when deployed):

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | For Gemini | Google AI Studio API key |
| `OPENAI_API_KEY` | For OpenAI | OpenAI API key (alternative) |
| `LLM_PROVIDER` | No | `gemini` or `openai` (default: `openai`) |
| `GEMINI_MODEL` | No | Model ID (default: `gemini-2.5-flash`) |
| `ADMIN_PASSWORD` | Recommended | Admin dashboard password |
| `SMTP_HOST` | For email | SMTP server hostname |
| `SMTP_PORT` | For email | SMTP port (default 587) |
| `SMTP_USER` | For email | SMTP username |
| `SMTP_PASSWORD` | For email | SMTP password / app password |
| `NOTIFY_EMAIL` | For email | Recipient for new lead alerts |

**Security note:** Never commit `.env` or API keys to version control. `.gitignore` excludes `.env` and `data/*.db`.

---

## 9. Installation & Running Locally

```bash
cd chatbot
python -m venv .venv

# Windows
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# Edit .env with API keys

streamlit run app.py
```

Access: **http://localhost:8501**

---

## 10. Deployment

### Recommended: Streamlit Community Cloud

1. Push repository to GitHub (exclude secrets)
2. Create app at [share.streamlit.io](https://share.streamlit.io)
3. Set main file: `app.py`
4. Add secrets (GEMINI_API_KEY, ADMIN_PASSWORD, etc.)
5. Deploy and use public URL for submission

See `DEPLOY.md` for step-by-step instructions.

### Considerations on Free Hosting

- SQLite file may reset on redeploy or instance restart
- For production scale, migrate to PostgreSQL or a managed database

---

## 11. Testing & Verification

### Manual Test Cases

| ID | Test | Expected Result |
|----|------|-----------------|
| T1 | Open app | Home page loads, sidebar shows LLM status |
| T2 | Chat: "What courses do you offer?" | Live Gemini response; sidebar shows "live" |
| T3 | Submit lead form | Success message; lead count increases |
| T4 | Admin login | Tables show leads, chats, automation events |
| T5 | Export CSV | File downloads with lead data |

### Automated Smoke Test (CLI)

```bash
python -c "from src.chatbot import generate_reply, get_provider_status; print(get_provider_status())"
```

---

## 12. Security Considerations

- Admin dashboard protected by password
- API keys and SMTP credentials stored in environment only
- No plain-text password storage for end users (visitor-facing pages are open)
- Input validation on required lead fields
- CSRF handled by Streamlit defaults

**Recommendations for production:**

- Use strong `ADMIN_PASSWORD`
- Rotate API keys periodically
- Enable HTTPS via hosting platform
- Restrict admin access by network or SSO if required

---

## 13. Limitations & Future Enhancements

### Current Limitations

- Single admin password (no multi-user RBAC)
- SQLite not ideal for multi-instance cloud deployments
- Deprecated `google.generativeai` SDK (migration to `google.genai` recommended)
- Email automation optional and requires manual SMTP setup

### Possible Enhancements

- PostgreSQL / MongoDB backend
- LangChain + vector DB for document-grounded answers
- CRM integration (HubSpot, Salesforce)
- WhatsApp / email bot channels
- Analytics charts in admin dashboard
- Rate limiting and abuse protection on chat

---

## 14. Project Structure

```
chatbot/
├── app.py                      # Streamlit entry point & UI
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── run.ps1                     # Local startup script (Windows)
├── DEPLOY.md                   # Deployment guide
├── README.md                   # Quick start & overview
├── src/
│   ├── config.py               # Settings & system prompt
│   ├── database.py             # SQLite operations
│   ├── chatbot.py              # LLM integration
│   └── automation.py           # Workflows & email
├── data/
│   ├── business_assistant.db   # Runtime database
│   └── automation.log          # Automation file log
├── docs/
│   ├── ARCHITECTURE.md         # Technical architecture
│   └── PROJECT_DOCUMENTATION.md  # This document
└── .streamlit/
    ├── config.toml             # Theme & server settings
    └── secrets.toml.example    # Cloud secrets template
```

---

## 15. Assessment Alignment

| Assessment Requirement | Project Deliverable |
|------------------------|---------------------|
| AI Assistant / Chatbot | AI Assistant page + `src/chatbot.py` |
| Lead Capture System | Lead Capture page + form validation |
| Data Storage | SQLite + CSV export |
| Automation Workflow | Lead notification + chat logging workflows |
| Dashboard / Admin View | Admin Dashboard with auth |
| Deployment | Streamlit Cloud ready (`DEPLOY.md`) |
| Documentation | README, ARCHITECTURE.md, this document |
| Architecture Diagram | Mermaid diagrams in README & docs |

---

## 16. Submission Deliverables Checklist

- [ ] **GitHub Repository Link** — public repo with source code
- [ ] **Live Hosted Project Link** — Streamlit Cloud URL
- [ ] **5–7 Minute Demo Video** — walkthrough of all modules
- [ ] **Architecture Diagram** — included in README and documentation
- [ ] **README / Documentation** — README.md + docs folder

---

## 17. Demo Video Suggested Script (5–7 Minutes)

1. **Introduction (30s)** — Project name, purpose, tech stack
2. **Architecture (45s)** — Show diagram; explain layers
3. **AI Assistant (2m)** — Live chat demo with business questions
4. **Lead Capture (1m)** — Submit form; explain automation
5. **Admin Dashboard (1.5m)** — Login; show leads, chats, events, CSV export
6. **Automation (45s)** — Explain email + logging; show automation tab
7. **Deployment (30s)** — Show live URL and GitHub repo

---

## 18. Author & Version

| Item | Detail |
|------|--------|
| Project name | AI-Powered Business Automation Assistant |
| Version | 1.0.0 |
| Primary stack | Python, Streamlit, SQLite, Google Gemini |
| License | MIT (assessment / portfolio use) |

---

*This document is intended for technical reviewers, assessors, and future maintainers. For quick setup instructions, see the root `README.md`.*
