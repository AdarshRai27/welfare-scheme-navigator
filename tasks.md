# Task Tracker — Agentic Scheme Navigator

> Update this file after every meaningful change. Keep it honest — a task is only "Completed" if it's actually done and tested.

## Current Task
Phase 1 Planning: Design DB schema, SQLAlchemy models, and plan the Scrapy scheme spiders.

## Progress
- **Overall:** 15% (Phase 0 fully completed, directories & config set up, mock integration verified)
- **Current phase:** Phase 1 — Scheme Data Pipeline (0% complete)

## Priority
1. Design database schemas and SQLAlchemy models for schemes and scraper runs
2. Scaffold Scrapy scrapers under `backend/app/scraper`

## Pending Tasks
- [ ] Register WhatsApp Cloud API developer account + test number (optional, mocked for now)
- [ ] Design and implement PostgreSQL schema (`schema.sql`) and SQLAlchemy model classes (`app/db/models.py`)
- [ ] Scaffold Scrapy project for web scraping schemes
- [ ] Implement Scrapy spider for MyScheme.gov.in
- [ ] Implement Scrapy spider for Uttar Pradesh scheme portal
- [ ] Implement Celery Beat scraping scheduler

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

## Open Decisions Needing Team Input
- Hackathon deadline / target timeline — not yet specified, affects how aggressively phases can be compressed
