# Task Tracker — Agentic Scheme Navigator

> Update this file after every meaningful change. Keep it honest — a task is only "Completed" if it's actually done and tested.

## Current Task
Phase 2 Planning: Design architecture and mock pipeline for voice (Bhashini transcription) and document input (OCR).

## Progress
- **Overall:** 35% (Phase 0 and Phase 1 completed, data pipeline & schema fully verified)
- **Current phase:** Phase 2 — Voice & Document Input Pipeline (0% complete)

## Priority
1. Design webhook receiver handling for voice notes (audio file download -> Bhashini transcribe)
2. Design webhook receiver handling for document images (image download -> Tesseract/Qwen2-VL OCR)

## Pending Tasks
- [ ] Register WhatsApp Cloud API developer account + test number (optional, mocked for now)
- [ ] Implement WhatsApp voice note media downloading endpoint in `backend/app/services/whatsapp.py`
- [ ] Implement WhatsApp image media downloading endpoint in `backend/app/services/whatsapp.py`
- [ ] Integrate Bhashini ASR client inside webhook pipeline (`POST /webhook/whatsapp`)
- [ ] Integrate OCR Tesseract + Qwen2-VL fallback extraction inside webhook pipeline
- [ ] Test conversation session state persistence in Redis (multi-message user tracking)

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

## Open Decisions Needing Team Input
- Hackathon deadline / target timeline — not yet specified, affects how aggressively phases can be compressed
