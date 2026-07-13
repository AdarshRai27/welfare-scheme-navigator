# Architecture — Agentic Scheme Navigator

## Overall System Architecture

```
USER (WhatsApp: Voice / Text / Photo)
        │
        ▼
Meta Cloud API (Webhook)
        │
        ▼
FastAPI Orchestrator  ──────► Bhashini AI (ASR / TTS / NMT)
  + Redis Session Store ────► Vision OCR (Tesseract + Qwen2-VL)
        │              ────► LangGraph Agent (Llama 3.1 70B)
        │              ────► PostgreSQL + pgvector (500+ schemes)
        │                            ▲
        │                            │
        │                  Celery Beat + Scrapy
        │                  (Daily Scheduled Scraping)
        │                            ▲
        │                            │
        │                  Data Sources:
        │                   - MyScheme.gov.in API
        │                   - State Government Portals
        │                   - e-Shram Portal
        │                   - NPCI DBT Dashboard
        │                   - Government Gazette PDFs
        ▼
WhatsApp Response (Schemes + Checklist + Auto-filled Forms)
```

**Request flow:**
1. User sends a voice note, text, or document photo to the WhatsApp number.
2. Meta Cloud API delivers it to the FastAPI orchestrator via webhook.
3. Orchestrator persists/loads session state in Redis (multi-turn context).
4. Voice → Bhashini ASR transcribes to text (and NMT normalizes language if needed). Photo → Vision OCR (Tesseract first pass, Qwen2-VL fallback for low-quality/rotated images) extracts structured fields.
5. Extracted text/data is handed to the LangGraph reasoning agent (backed by Llama 3.1 70B via Ollama), which queries PostgreSQL + pgvector for candidate schemes, applies eligibility rules, and forward-chains to related schemes.
6. The agent composes a response: eligibility checklist + auto-filled form data.
7. Response is translated/synthesized back via Bhashini (TTS) if the interaction was voice-based, and sent back to the user over WhatsApp.
8. Independently, Celery Beat triggers Scrapy spiders on a schedule to keep the scheme database fresh from official sources.

## Folder Structure

```
agentic-scheme-navigator/
├── requirements.md
├── architecture.md
├── rules.md
├── phases.md
├── tasks.md
├── memory.md
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entrypoint
│   │   ├── api/
│   │   │   └── webhook.py          # WhatsApp Cloud API webhook routes
│   │   ├── core/
│   │   │   ├── config.py           # env/config loading
│   │   │   └── session.py          # Redis session management
│   │   ├── services/
│   │   │   ├── bhashini.py         # ASR/TTS/NMT client
│   │   │   ├── ocr.py              # Tesseract + Qwen2-VL pipeline
│   │   │   ├── whatsapp.py         # WhatsApp send/receive helpers
│   │   │   └── forms.py            # form auto-fill generation
│   │   ├── agent/
│   │   │   ├── graph.py            # LangGraph agent definition
│   │   │   ├── nodes/              # individual reasoning nodes
│   │   │   └── prompts/            # prompt templates
│   │   ├── db/
│   │   │   ├── models.py           # SQLAlchemy models
│   │   │   ├── schema.sql
│   │   │   └── vector_store.py     # pgvector helpers
│   │   └── scraper/
│   │       ├── spiders/            # Scrapy spiders per source
│   │       ├── pipelines.py
│   │       └── scheduler.py        # Celery Beat schedule config
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── infra/
│   ├── docker-compose.yml
│   └── deploy/
└── docs/
    └── (design notes, ADRs, API contracts)
```

## Technology Stack

| Layer | Technology | Why This Choice | Cost |
|---|---|---|---|
| Channel | WhatsApp Cloud API (Meta) | 500M+ Indian users already have it, zero install | Free tier |
| Voice | Bhashini AI (Govt of India) | 22 Indian languages, free ASR + TTS + NMT | Free |
| OCR | Tesseract + Qwen2-VL | Handles Indic scripts; Qwen2-VL as multimodal fallback for low-res/rotated images | Open source |
| LLM | Llama 3.1 70B (via Ollama) | Self-hosted, bilingual reasoning, no per-call cost | Open source |
| Agent framework | LangGraph | Multi-step reasoning with memory, supports forward-chaining logic | Open source |
| Embeddings | BGE-M3 | Multilingual embeddings for scheme semantic search | Open source |
| Database | PostgreSQL + pgvector | ACID guarantees for scheme/user data + vector similarity search in one store | Open source |
| Backend framework | FastAPI + Redis | Async request handling, Redis for session/webhook state | Open source |
| Scheduler | Celery Beat + Scrapy | Daily incremental scraping of scheme sources | Open source |

**Zero paid APIs** is a deliberate constraint — every layer above is free-tier or self-hosted open source.

## Frontend Architecture
There is no traditional frontend. **WhatsApp itself is the UI.** All user interaction happens through:
- Voice notes (input) and TTS audio replies (output)
- Text messages (input/output)
- Photos of documents (input) and formatted text/PDF-style checklists (output)

Any future admin/analytics surface (e.g., an NGO/CSC operator dashboard, noted in requirements.md as future scope) would be a separate lightweight web app and is out of scope for the MVP.

## Backend Architecture
- **FastAPI orchestrator** is the single entrypoint: receives WhatsApp webhooks, manages session state in Redis, and coordinates calls to Bhashini, the OCR pipeline, and the LangGraph agent.
- **Session state** (Redis) tracks in-progress conversations — e.g., a user who sent a voice note, then a document photo, then asked a follow-up — so the agent can reason across a multi-turn interaction rather than treating each message in isolation.
- **LangGraph agent** encapsulates the eligibility-reasoning logic as a graph of nodes (e.g., extract-user-profile → candidate-scheme-retrieval → rule-evaluation → forward-chain-related-schemes → compose-response). This keeps reasoning steps testable and inspectable rather than one monolithic prompt.
- **OCR pipeline** runs Tesseract first (fast, cheap) and falls back to Qwen2-VL when confidence is low or the image is rotated/poor quality.
- **Scraper subsystem** (Scrapy spiders + Celery Beat schedule) runs independently of the request path, writing into the same PostgreSQL scheme tables that the agent reads from.

## Database Design
PostgreSQL with the pgvector extension, serving two roles: structured relational data and vector similarity search.

Core tables (initial draft — refine during Phase 1):
- `schemes` — scheme_id, name, issuing_body (central/state), category, description, eligibility_rules (JSONB), source_url, last_scraped_at, embedding (vector, via pgvector)
- `scheme_documents_required` — scheme_id (FK), document_type, mandatory (bool)
- `users` — whatsapp_id (hashed/pseudonymized), preferred_language, created_at — **minimal PII by design**
- `user_sessions` — session_id, whatsapp_id (FK), state (JSONB), last_active_at
- `extracted_documents` — session_id (FK), document_type, extracted_fields (JSONB, encrypted at rest), created_at
- `scrape_runs` — source_name, run_at, status, schemes_added, schemes_updated

Design note: raw extracted document data (Aadhaar numbers, income figures, etc.) is sensitive — see security guidelines in rules.md for encryption/retention requirements.

## API Design
Primary interface is the WhatsApp webhook, not a public REST API for end users. Internal API surface (FastAPI):

- `POST /webhook/whatsapp` — receives inbound WhatsApp events (messages, media)
- `GET /webhook/whatsapp` — Meta webhook verification handshake
- `GET /internal/schemes` — (internal/admin) list/search schemes, for debugging and future dashboard
- `POST /internal/scrape/trigger` — (internal/admin) manually trigger a scrape run
- `GET /internal/health` — health check for orchestrator, DB, Redis, Ollama

All internal/admin routes require authentication (see rules.md) and are not exposed to end users.

## Authentication Flow
- **End users** authenticate implicitly via their WhatsApp phone number (through Meta's Cloud API) — no separate login/signup flow, consistent with the zero-friction design goal.
- **Internal/admin routes** (scrape triggers, scheme management) require API-key or token-based auth — never exposed without credentials.
- **Meta webhook verification** uses the standard Meta-provided verify token during webhook setup, and all inbound webhook payloads are validated against Meta's signature (`X-Hub-Signature-256`) before processing.

## Deployment Strategy
- Containerized services (Docker) for: FastAPI orchestrator, Celery worker, Celery Beat, Ollama (LLM serving), PostgreSQL, Redis.
- `docker-compose.yml` for local development; production target to be decided (self-hosted GPU server needed for Ollama/Llama 3.1 70B — this is a real infra decision to make early, since GPU hosting is the one component that isn't naturally "free tier").
- Scraper spiders run as scheduled Celery Beat tasks, not long-running services.
- Config/secrets (WhatsApp tokens, Bhashini credentials, DB credentials) loaded via environment variables, never committed to the repo.

## Important Design Decisions
1. **WhatsApp as the only UI** — deliberate, to hit users where they already are and avoid app-install friction. Trade-off: constrained to what WhatsApp's Cloud API supports (no rich custom UI).
2. **Self-hosted LLM (Llama 3.1 70B via Ollama) instead of a hosted API** — keeps the system on the "zero paid APIs" constraint, but shifts cost/complexity to self-hosted GPU infrastructure, which needs to be planned for explicitly.
3. **LangGraph over a single prompt** — eligibility reasoning is inherently multi-step (extract profile → match rules → forward-chain related schemes), so a graph-based agent keeps this inspectable/debuggable rather than being one large opaque prompt.
4. **PostgreSQL + pgvector over separate relational + vector DBs** — reduces operational surface area (one database to run) while covering both structured eligibility rules and semantic scheme search.
5. **Tesseract-first, Qwen2-VL-fallback OCR** — keeps the common case cheap/fast, reserving the heavier multimodal model for genuinely hard images (poor lighting, rotation).
6. **Minimal PII storage** — user table stores a hashed WhatsApp ID and language preference only; extracted document fields are kept separately and are candidates for encryption-at-rest and retention limits (see rules.md).
