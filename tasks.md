# Task Tracker — Agentic Scheme Navigator

> Update this file after every meaningful change. Keep it honest — a task is only "Completed" if it's actually done and tested.

## Current Task
Phase 3 Planning: Design architectural changes and planning for the reasoning agent (LangGraph flow).

## Progress
- **Overall:** 55% (Phase 0, Phase 1, and Phase 2 completed, media input parsing & state tracking fully verified)
- **Current phase:** Phase 3 — Reasoning Agent (LangGraph) (0% complete)

## Priority
1. Design LangGraph state machine sequence (extract-profile -> retrieve-candidates -> evaluate-rules -> forward-chain -> compose-response)
2. Define schema for graph state and Ollama Llama 3.1 70B prompt structures

## Pending Tasks
- [ ] Register WhatsApp Cloud API developer account + test number (optional, mocked for now)
- [ ] Implement LangGraph workflow graph schema and state definition in `backend/app/agent/graph.py`
- [ ] Implement individual reasoning nodes in `backend/app/agent/nodes/`
- [ ] Write prompt templates under `backend/app/agent/prompts/`
- [ ] Integrate forward-chaining rules logic (trigger related schemes)
- [ ] Write unit and integration tests to verify agent's reasoning against test user profiles

## Blocked Tasks
None.

## Completed Tasks
- [x] Defined project scope and problem statement (source: team's pitch deck)
- [x] Defined tech stack and system architecture (source: team's pitch deck)
- [x] Created `requirements.md`, `architecture.md`, `rules.md`, `phases.md`, `tasks.md`, `memory.md` in workspace root
- [x] Decided on Ollama hosting, data retention policy, and initial scraping target
- [x] Scaffolded repo directory structure per `architecture.md`
- [x] Wrote `docker-compose.yml` for PostgreSQL+pgvector and Redis
- [x] Created `backend/.env.example`
- [x] Implemented mock services for WhatsApp, Bhashini, and OCR
- [x] Implemented webhook verification handshake and basic echo receiver
- [x] Verified Phase 0 setup by executing test suite passing 6/6 tests
- [x] Designed database schema (`schema.sql`) and SQLAlchemy async models (`models.py`)
- [x] Implemented `VectorStore` (supporting cosine distance vector search and keyword fallback ranking)
- [x] Scaffolded Scrapy project spiders for MyScheme and Uttar Pradesh portals
- [x] Implemented `SchemePipeline` for database ingestion and daily `scheduler.py` configuration
- [x] Verified Phase 1 implementation by executing full test suite passing 11/11 tests
- [x] Implemented WhatsApp media download helper in `whatsapp.py`
- [x] Integrated `SessionManager` in webhook router (`webhook.py`)
- [x] Integrated Bhashini ASR and NMT translation inside webhook pipeline
- [x] Integrated OCR document field extraction inside webhook pipeline
- [x] Implemented multi-turn profile accumulation and privacy purging (Option A)
- [x] Verified Phase 2 implementation by executing full test suite passing 13/13 tests

## Open Decisions Needing Team Input
- Hackathon deadline / target timeline — not yet specified, affects how aggressively phases can be compressed
