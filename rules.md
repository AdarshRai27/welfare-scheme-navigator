# Development Rules — Agentic Scheme Navigator

These rules are always in effect. Any generated code must follow them. If a request conflicts with a rule here, flag the conflict instead of silently violating the rule.

## Coding Standards
- **Python** is the primary language (FastAPI backend, LangGraph agent, Scrapy spiders). Target Python 3.11+.
- Follow **PEP 8**; use `black` for formatting and `ruff` (or `flake8`) for linting.
- Type hints are required on all function signatures — this is an agentic/data-heavy system where implicit types cause silent bugs.
- Use **async/await** consistently in FastAPI routes and any I/O-bound service calls (Bhashini, OCR, DB) — don't mix blocking calls into async routes.
- Every module, class, and non-trivial function gets a docstring explaining purpose, not just what the code literally does.
- No commented-out dead code committed to the repo.

## Best Practices
- Keep the LangGraph agent's reasoning steps as **separate, named nodes** (extract-profile, retrieve-candidates, evaluate-rules, forward-chain, compose-response) — never collapse reasoning into one giant prompt/function.
- Scheme eligibility rules should be **data**, not hardcoded logic — store rules as structured JSONB in `schemes.eligibility_rules` so the ruleset can grow without code changes.
- All external service calls (Bhashini, OCR, Ollama, WhatsApp API) go through a dedicated service module — no inline HTTP calls scattered through route handlers.
- Write idempotent scraper pipelines — a spider run twice on the same day should not duplicate scheme records.
- Config (API keys, DB URLs, tokens) comes from environment variables only — never hardcoded, never committed.

## Libraries/Frameworks to Use
- Backend: **FastAPI**, **Redis** (via `redis-py`), **SQLAlchemy** (async) for PostgreSQL
- Agent: **LangGraph**, **Ollama** client for Llama 3.1 70B
- OCR: **pytesseract** (Tesseract wrapper), **Qwen2-VL** (via its official inference library)
- Voice: **Bhashini AI** official APIs
- Vector search: **pgvector** (PostgreSQL extension)
- Embeddings: **BGE-M3**
- Scraping: **Scrapy**, **Celery** + **Celery Beat**
- Testing: **pytest**, **pytest-asyncio**
- WhatsApp integration: **WhatsApp Cloud API** (direct via Meta, or a thin official SDK if available) — avoid unofficial/reverse-engineered WhatsApp libraries

## Libraries/Approaches to Avoid
- **No paid LLM or OCR APIs** (OpenAI, Anthropic, Google Vision, etc.) — violates the zero-paid-API constraint. If a free/open-source option genuinely can't do the job, flag it as a decision point rather than silently substituting a paid one.
- **No unofficial WhatsApp libraries** (e.g., libraries that automate the WhatsApp consumer app via browser automation) — only the official WhatsApp Cloud API. Unofficial approaches risk account bans and are not production-safe.
- **No ORM-bypassing raw SQL string concatenation** — always use parameterized queries/SQLAlchemy to avoid injection risk, given this system handles sensitive documents.
- **No client-side/browser storage patterns** — this is a backend/agent system with no browser frontend; irrelevant here but noted to avoid confusion if a dashboard is added later.
- **No synchronous blocking calls inside async FastAPI route handlers.**

## Error-Handling Guidelines
- Every external call (Bhashini, OCR, Ollama, WhatsApp send, scraper HTTP requests) must handle timeouts and failures gracefully — a failed ASR call should degrade to "please try again" over WhatsApp, not a silent crash or a stuck session.
- Log errors with enough context to debug (session ID, step in the LangGraph flow) but **never log raw sensitive document contents or full document images** to standard logs.
- Scraper spiders must handle source-site structure changes without crashing the whole scheduled job — isolate failures per-spider so one broken source doesn't block others.
- User-facing error messages (sent back over WhatsApp) should be simple, in the user's language where possible, and never expose stack traces or internal system details.

## Security Guidelines
- This system processes **sensitive personal documents** (Aadhaar, income certificates, caste certificates, land records). Treat this as a hard constraint, not a nice-to-have:
  - Encrypt sensitive extracted document fields at rest.
  - Define and enforce a data retention policy — don't keep raw document images/extracted PII indefinitely; retention limits should be decided explicitly (see tasks.md as an open decision).
  - Store user identifiers (WhatsApp ID) hashed, not in plaintext, per the architecture design.
- All inbound WhatsApp webhook payloads must be verified against Meta's `X-Hub-Signature-256` before processing — never trust an unverified payload.
- All admin/internal routes require authentication; never expose scheme-management or scrape-trigger endpoints without an API key/token check.
- Secrets (Bhashini credentials, WhatsApp tokens, DB passwords) live in environment variables / a secrets manager — never in source control.
- Validate and sanitize all OCR-extracted text before using it in prompts or storing it, to avoid prompt injection via a malicious document image.

## Performance Expectations
- Target scheme-data staleness: **under 24 hours** from source changes, per the daily Celery Beat scraping schedule.
- WhatsApp responses should acknowledge receipt quickly (e.g., a "processing..." message) if the full agent reasoning pipeline will take more than a few seconds, so users on slow connections aren't left wondering if the message was received.
- OCR pipeline should try Tesseract first (fast path) and only fall back to Qwen2-VL (slower, heavier) when needed — don't run both unconditionally.
- Scraper jobs should scrape **incrementally** where the source allows it, not full re-scrapes every run.

## File Organization Rules
- Follow the folder structure defined in `architecture.md` — don't introduce new top-level directories without updating that file.
- One responsibility per module: services (external calls), agent (reasoning), db (persistence), scraper (data ingestion), api (HTTP routes) stay separated.
- Tests mirror the source structure (`tests/agent/`, `tests/services/`, etc.).

## Naming Conventions
- Python: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Database tables/columns: `snake_case`, plural table names (`schemes`, `user_sessions`).
- LangGraph node names: descriptive verb-first (`extract_user_profile`, `retrieve_candidate_schemes`), matching the node list in architecture.md.
- Environment variables: `UPPER_SNAKE_CASE`, prefixed by service (`BHASHINI_API_KEY`, `WHATSAPP_ACCESS_TOKEN`).

## AI Boundaries — Things the AI Should Never Do
- **Never hardcode or invent scheme eligibility rules.** Eligibility logic must come from scraped/verified source data, not assumptions about what a scheme "probably" requires — incorrect eligibility guidance has real consequences for vulnerable users.
- **Never fabricate scheme data** (names, benefit amounts, deadlines) when a scraper fails to retrieve something — surface the gap honestly rather than filling it with a plausible-sounding guess.
- **Never log, print, or persist raw sensitive document content** (Aadhaar numbers, etc.) outside of the designated encrypted storage path.
- **Never introduce a paid API call** without first flagging it as a deviation from the zero-paid-API constraint and getting explicit confirmation.
- **Never bypass the webhook signature verification** step, even temporarily "for testing," in code that could reach a shared/production branch.
- **Never work on more than one phase from `phases.md` at a time** unless explicitly told to — see phases.md for the phase boundaries.
- **Never mark a task complete in `tasks.md` without it actually being done and tested.**
- **Never restructure or delete content in `memory.md`** — only append/update it as development progresses; it's the project's persistent record.
