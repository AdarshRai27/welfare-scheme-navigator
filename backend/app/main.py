"""Main entrypoint for the FastAPI application."""

import logging
from typing import Dict

from fastapi import FastAPI

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

# Include webhook route paths
app.include_router(webhook_router)


@app.get("/internal/health")
async def health_check() -> Dict[str, str]:
    """Endpoint for basic container health checks.

    Returns:
        Dictionary containing status and server indicator.
    """
    logger.debug("Health check requested.")
    return {"status": "healthy", "service": "orchestrator"}
