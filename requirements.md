# Requirements — Agentic Scheme Navigator

## What Needs to Be Built
A **WhatsApp-first AI agent** that helps Indian citizens — especially rural, low-literacy, and non-English-speaking users — discover which government welfare schemes they're eligible for and get help applying, using nothing but voice messages and photos sent to a WhatsApp number.

The user sends a voice note or a photo of a document (Aadhaar, income certificate, land record, etc.) on WhatsApp. The agent transcribes/reads it, reasons over a database of 500+ central and state schemes, and replies with a personalized eligibility checklist and pre-filled application forms — no app install, no literacy required, works on basic phones.

## Problem Being Solved
- 1,500+ central and state welfare schemes exist, but citizens don't know which apply to them.
- ~40% of INR 50,000 Cr in welfare funds goes unspent due to low uptake.
- Fewer than 50% of construction workers are registered with labor welfare boards.
- Only 27% of rural adults are financially literate; ~20% effectively use digital financial services.
- Root causes: information asymmetry, documentation complexity (Aadhaar + income + land + caste + bank docs), the digital divide, and frequently changing bureaucratic rules.

## Why Existing Solutions Fail
| Approach | Limitation |
|---|---|
| Static portals (MyScheme.gov.in) | Keyword search only, requires literacy + knowing scheme names |
| Basic FAQ chatbots | Single-turn, no multi-step reasoning |
| Mobile apps | Requires install, storage constraints, friction |
| NGO outreach camps | Manual, not scalable, can't reach 600K+ villages |

**Key insight driving this project:** no existing solution combines voice input + document auto-fill + multi-step eligibility reasoning on a platform (WhatsApp) rural users already have.

## Project Goals
1. Let a user discover eligible schemes using only voice or photo input on WhatsApp — zero typing required.
2. Reason across scheme eligibility rules so one qualifying scheme can surface related/forward-chained schemes (e.g., PM-Kisan eligibility auto-suggests KCC, Fasal Bima).
3. Auto-fill application forms/checklists from OCR'd documents.
4. Support all 22 scheduled Indian languages via Bhashini for voice input/output.
5. Keep scheme data fresh via scheduled scraping of official sources (target: <24h staleness).
6. Run entirely on free-tier / open-source components — zero paid APIs.

## Target Users
- Primary: rural and semi-urban Indian citizens, including non-literate or low-literacy users, applying for welfare schemes (farmers, construction/gig workers, women's welfare beneficiaries, students, senior citizens).
- Secondary: NGO field workers and Common Service Centre (CSC) operators who assist citizens and could use the agent as a force-multiplier.
- Constraint driving design: target users may have only basic phones, unreliable connectivity, and no comfort installing or navigating a dedicated app.

## Core Features (MVP)
1. **WhatsApp intake** — accept voice notes, text, and document photos via WhatsApp Cloud API webhook.
2. **Voice transcription & synthesis** — Bhashini ASR (speech-to-text) and TTS (text-to-speech) across 22 languages, plus NMT for translation.
3. **Document OCR** — extract structured data (name, income, land size, caste category, etc.) from photographed documents using Tesseract + Qwen2-VL for low-quality/rotated images.
4. **Scheme eligibility reasoning agent** — a LangGraph-based multi-step agent (backed by Llama 3.1 70B) that matches extracted user data against scheme eligibility rules, including forward-chaining to related schemes.
5. **Scheme knowledge base** — PostgreSQL + pgvector store of 500+ schemes with structured eligibility rules and semantic search over scheme descriptions.
6. **Response generation** — personalized eligibility checklist and auto-filled application form data, delivered back over WhatsApp as text/voice.
7. **Scheduled data refresh** — Celery Beat + Scrapy jobs that scrape MyScheme.gov.in, state portals, e-Shram, NPCI DBT dashboard, and government gazette PDFs to keep the scheme database current.

## Optional / Future-Scope Features
- Full Bhashini voice integration across all 22 scheduled languages (MVP may launch with a subset).
- Direct application submission via UMANG APIs (one-tap apply, no manual form download).
- Regional utilization analytics — recommend schemes based on regional uptake/success patterns.
- Multi-turn conversational memory across sessions (returning users, application status follow-up).
- CSC/NGO operator dashboard for assisted-mode usage.

## Success Criteria
- A user can, using only a voice note and/or photo, receive an accurate list of schemes they're eligible for.
- Scheme database contains 500+ schemes with machine-readable eligibility rules.
- Scheme data staleness stays under 24 hours from source changes.
- ASR handles diverse regional accents at a target of 80%+ word-error-rate performance (per team's own target — track and revisit as real usage data comes in).
- End-to-end flow (voice/photo in → checklist out) works on a basic smartphone with only WhatsApp installed, no other app required.
- Zero paid third-party APIs in the running system.

## Constraints & Assumptions
- **Budget constraint:** must run on free-tier and open-source components only (per team's stated tech choices) — no paid LLM/OCR/voice APIs.
- **Compute assumption:** self-hosting Llama 3.1 70B via Ollama requires a GPU-capable server; this is a real infrastructure dependency that needs to be resourced (not yet decided — flag for team).
- **Device assumption:** end users may be on basic/low-end Android phones with limited storage — the solution must not require anything beyond WhatsApp.
- **Connectivity assumption:** rural connectivity may be intermittent; the system should be resilient to slow/dropped webhook responses.
- **Data source dependency:** scheme accuracy depends entirely on scraped government sources (MyScheme.gov.in, state portals, e-Shram, NPCI DBT, gazette PDFs) — no official structured API is guaranteed to exist for all of these, so scraping fragility is a real risk.
- **Regulatory/compliance:** the system will process sensitive personal documents (Aadhaar, income, caste certificates) — data privacy and secure handling requirements are a hard constraint, not optional.
- **Current stage:** this is a hackathon-originated project; no prototype exists yet as of this writing. Timeline is currently unscoped — to be defined once the team commits to a hackathon deadline or a longer build plan.
