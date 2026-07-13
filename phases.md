# Development Phases — Agentic Scheme Navigator

Work on **one phase at a time**, in order, unless explicitly instructed otherwise. Do not start a phase whose dependencies aren't met.

---

## Phase 0: Project Setup & Infrastructure Decisions
**Objective:** Get the repo, environments, and unresolved infra decisions (GPU hosting for Ollama, etc.) in place before any feature work starts.

**Features to implement:** N/A — this is scaffolding, not user-facing features.

**Deliverables:**
- Repo structure matching `architecture.md`
- `docker-compose.yml` with PostgreSQL (+pgvector), Redis, and a placeholder Ollama service
- `.env.example` with all required environment variables documented (no real secrets)
- Decision recorded on where Ollama/Llama 3.1 70B will actually run (self-hosted GPU box, cloud GPU instance, etc.) — this is a real open question, not yet decided
- WhatsApp Cloud API developer account + test number set up, webhook verification working end-to-end (even if it just echoes messages)
- Bhashini API access/credentials obtained

**Dependencies:** None — this is the starting point.

**Completion checklist:**
- [ ] Repo scaffolded per architecture.md folder structure
- [ ] docker-compose brings up DB + Redis locally
- [ ] WhatsApp webhook verified and receiving test messages
- [ ] Bhashini credentials obtained and a test ASR call succeeds
- [ ] Ollama hosting decision made and documented in memory.md

---

## Phase 1: Scheme Data Pipeline
**Objective:** Get real scheme data into the database before building any reasoning on top of it — the agent is useless without accurate scheme data.

**Features to implement:**
- Scrapy spiders for MyScheme.gov.in and at least one state portal
- `schemes` and `scheme_documents_required` tables (per architecture.md schema)
- Celery Beat schedule for daily scraping
- BGE-M3 embedding generation for scheme descriptions, stored in pgvector

**Deliverables:**
- Working scraper(s) populating the `schemes` table with structured eligibility rules
- Scheduled scraping job running on Celery Beat
- Vector search over scheme descriptions returning sensible results for a sample query
- `scrape_runs` table logging each run's outcome

**Dependencies:** Phase 0 (DB + infra in place).

**Completion checklist:**
- [ ] At least one spider successfully scrapes and structures scheme data
- [ ] Eligibility rules stored as structured JSONB, not free text
- [ ] Vector search returns relevant schemes for test queries
- [ ] Scheduled job runs automatically and logs to `scrape_runs`
- [ ] Scraper failure on one source doesn't crash the whole job

---

## Phase 2: Voice & Document Input Pipeline
**Objective:** Get raw WhatsApp input (voice, photo) converted into structured, usable data.

**Features to implement:**
- WhatsApp webhook handling for voice notes, text, and images
- Bhashini ASR integration (voice → text)
- OCR pipeline: Tesseract first pass + Qwen2-VL fallback
- Redis session store for in-progress conversations

**Deliverables:**
- A user can send a voice note and get back a correct transcription (internally, not yet a full answer)
- A user can send a document photo and get back correctly extracted structured fields
- Session state persists across a multi-message conversation

**Dependencies:** Phase 0 (infra, WhatsApp webhook). Can run in parallel with Phase 1 if resourcing allows, but reasoning (Phase 3) needs both done.

**Completion checklist:**
- [ ] Voice notes transcribed accurately across at least 2-3 test languages
- [ ] Document OCR extracts correct structured fields from a clear test document
- [ ] OCR fallback triggers correctly on a deliberately poor-quality test image
- [ ] Session state correctly tracks a multi-turn test conversation

---

## Phase 3: Reasoning Agent (LangGraph)
**Objective:** Build the core eligibility-reasoning agent that ties scheme data (Phase 1) and user input (Phase 2) together.

**Features to implement:**
- LangGraph graph with the node sequence defined in architecture.md (extract-profile → retrieve-candidates → evaluate-rules → forward-chain → compose-response)
- Llama 3.1 70B integration via Ollama
- Forward-chaining logic (one qualifying scheme surfaces related schemes)
- Response composition (checklist + form data)

**Deliverables:**
- End-to-end: structured user data in → correct list of eligible schemes + checklist out
- Forward-chaining demonstrably works on at least one real scheme relationship (e.g., PM-Kisan → KCC/Fasal Bima)

**Dependencies:** Phase 1 (scheme data must exist) and Phase 2 (need structured user input to reason over).

**Completion checklist:**
- [ ] Agent correctly identifies eligibility for a set of test user profiles
- [ ] Forward-chaining surfaces at least one correct related-scheme suggestion
- [ ] Agent gracefully handles a user profile that matches no schemes
- [ ] No hardcoded/fabricated eligibility rules — all sourced from the `schemes` table

---

## Phase 4: Response Delivery & Form Auto-Fill
**Objective:** Turn the agent's output into a usable WhatsApp reply, including auto-filled forms.

**Features to implement:**
- Form auto-fill generation from OCR'd + reasoned data
- Bhashini TTS for voice replies (matching the user's input language/mode)
- WhatsApp response formatting (checklist as readable text, form data as attachment or structured message)

**Deliverables:**
- A full round trip: user sends voice note + document photo → receives a checklist and pre-filled form info back on WhatsApp, in their language if voice was used

**Dependencies:** Phase 3 (agent must produce structured output to render).

**Completion checklist:**
- [ ] Checklist renders clearly as a WhatsApp text message
- [ ] Auto-filled form data is accurate against the source document
- [ ] Voice replies (TTS) work for at least the languages tested in Phase 2
- [ ] Full round-trip tested manually end-to-end on a real WhatsApp test number

---

## Phase 5: Hardening, Security & Testing
**Objective:** Make the system safe to put in front of real users with sensitive documents.

**Features to implement:**
- Encryption at rest for sensitive extracted document fields
- Data retention policy implementation (auto-purge per policy)
- Webhook signature verification enforced everywhere
- Test coverage across services, agent nodes, and scraper pipelines
- Error handling audit against rules.md guidelines

**Deliverables:**
- Security review checklist passed (see rules.md security guidelines)
- Test suite covering core paths (ASR, OCR, agent reasoning, scraper)
- Documented data retention policy

**Dependencies:** Phases 1–4 functionally complete.

**Completion checklist:**
- [ ] Sensitive data encrypted at rest
- [ ] Retention policy defined and enforced
- [ ] All webhook payloads signature-verified
- [ ] Test suite passes across core modules
- [ ] No sensitive data appears in logs (manual audit)

---

## Phase 6+ (Future Scope — not yet scheduled)
Not started until explicitly prioritized:
- Full 22-language Bhashini coverage
- UMANG API direct-submission integration
- Regional utilization analytics
- NGO/CSC operator dashboard

These are tracked in requirements.md under "Optional / Future-Scope Features" and should stay out of active phases until the MVP (Phases 0–5) is solid.
