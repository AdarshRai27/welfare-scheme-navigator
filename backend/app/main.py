"""Main entrypoint for the FastAPI application."""

import logging
from typing import Dict

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.webhook import router as webhook_router

# Configure basic logging layout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title="Agentic Scheme Navigator Backend",
    description="FastAPI orchestrator handling WhatsApp messages, OCR pipelines, and the reasoning agent.",
    version="0.1.0",
)

# Mount static files folder dynamically relative to application directory
current_file_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(os.path.dirname(current_file_dir), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include webhook route paths
app.include_router(webhook_router)


@app.on_event("startup")
async def startup_event():
    """Seed mock database lists on server startup for preview modes."""
    try:
        import json
        from app.db.vector_store import VectorStore
        vs = VectorStore()
        if not vs._in_memory_schemes:
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            seed_path = os.path.join(current_file_dir, "db", "schemes_seed.json")
            if os.path.exists(seed_path):
                with open(seed_path, "r", encoding="utf-8") as f:
                    schemes = json.load(f)
                    for scheme in schemes:
                        await vs.add_scheme(scheme)
                logger.info(f"[STARTUP] Auto-seeded {len(schemes)} mock schemes from JSON successfully.")
            else:
                logger.warning(f"[STARTUP] Seed file not found at: {seed_path}")
    except Exception as err:
        logger.error(f"[STARTUP] Failed auto-seeding local mock schemes: {err}")

@app.get("/internal/health")
async def health_check() -> Dict[str, str]:
    """Endpoint for basic container health checks.

    Returns:
        Dictionary containing status and server indicator.
    """
    logger.debug("Health check requested.")
    return {"status": "healthy", "service": "orchestrator"}
