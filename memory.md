# Project Memory — Agentic Scheme Navigator

> Working memory for this project. Updated continuously as development progresses. Append/update — never restructure or delete history.

## What Has Been Completed
- 2026-07-14: Initial project docs created (`requirements.md`, `architecture.md`, `rules.md`, `phases.md`, `tasks.md`, `memory.md`) based on the team's pitch deck content. Scaffolded all 6 files directly at the project root workspace `c:\Users\rinku\OneDrive\Desktop\Rag bot` per development requirements.
- 2026-07-14: Git repository initialized, `.gitignore` created, and all Phase 0 changes committed under user credentials.

## Decisions Made & Why
- **WhatsApp as the sole UI** — chosen because 500M+ Indians already use it and it requires zero app install, directly addressing the "digital divide" root cause.
- **Zero paid APIs** — entire stack (Bhashini, Tesseract/Qwen2-VL, Llama 3.1 70B via Ollama, LangGraph, BGE-M3, PostgreSQL+pgvector, FastAPI+Redis, Celery+Scrapy) chosen to be free-tier or open-source.
- **PostgreSQL + pgvector instead of separate relational/vector stores** — reduces operational complexity to one database.
- **Tesseract-first, Qwen2-VL-fallback OCR** — keeps the common case fast/cheap, reserves the heavier multimodal model for genuinely hard images.
- **Phases ordered data-pipeline-first (Phase 1) before the reasoning agent (Phase 3)** — the agent is worthless without real scheme data to reason over.
- **Cloud GPU instance / free developer tier for Llama 3.1 70B** — since local GPU hardware is unavailable, cloud-based free GPU services/APIs will be used for production model execution.
- **Mock Handlers for development/testing** — mock layers for Bhashini, OCR, and WhatsApp will be built to allow testing the system end-to-end without network or credential blocks.
- **Option A Data Retention** — sensitive extracted document fields will be purged immediately upon WhatsApp session closure/completion to preserve user privacy.
- **Uttar Pradesh State Portal Target** — selected as the first state-level source to target for scheme scraping.
- **Docker unavailable on dev host** — since Docker is not installed, local development uses mock service layers and Redis/DB in-memory fallbacks.

## Current Implementation Status
Phase 3 complete. LangGraph workflow, extract-retrieve-evaluate-chain-compose reasoning nodes, and LLM prompts are written and verified passing 16/16 tests. Next is Phase 4 (Response Delivery & Form Auto-Fill).

## Which File is Currently Being Worked On
c:/Users/rinku/OneDrive/Desktop/Rag bot/tasks.md

## Important Context for Future Sessions
- The GPU-hosting question for Llama 3.1 70B is the single biggest open infrastructure risk.
- Scraper fragility is a known risk: several data sources don't have guaranteed structured APIs.

## Known Issues
None yet.

## Future Improvements
- Full 22-language Bhashini voice coverage
- UMANG API direct application submission
- Regional utilization analytics
- NGO/CSC operator dashboard
