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
        from app.db.vector_store import VectorStore
        vs = VectorStore()
        if not vs._in_memory_schemes:
            # 1. PM-Kisan
            await vs.add_scheme({
                "name": "PM-Kisan Samman Nidhi",
                "issuing_body": "Ministry of Agriculture",
                "state": "Uttar Pradesh",
                "category": "Agriculture",
                "description": "Financial support for landowning farmers across India",
                "eligibility_rules": {
                    "min_age": 18,
                    "income_limit": 999999999,
                    "requires_land": True,
                }
            })
            # 2. UP Senior Pension
            await vs.add_scheme({
                "name": "UP Senior Pension Scheme",
                "issuing_body": "Social Welfare Department",
                "state": "Uttar Pradesh",
                "category": "Pension",
                "description": "Old age pension support for citizens in UP",
                "eligibility_rules": {
                    "min_age": 60,
                    "income_limit": 46080,
                }
            })
            # 3. UP Kanya Sumangala Yojana (Women/Girls)
            await vs.add_scheme({
                "name": "UP Kanya Sumangala Yojana",
                "issuing_body": "Women and Child Development Department",
                "state": "Uttar Pradesh",
                "category": "Women & Child",
                "description": "Financial assistance for girls' education, health, and welfare in Uttar Pradesh",
                "eligibility_rules": {
                    "min_age": 0,
                    "max_age": 25,
                    "income_limit": 300000,
                    "gender": "female",
                }
            })
            # 4. UP Free Tablet Smartphone Scheme (Education/Youth)
            await vs.add_scheme({
                "name": "UP Free Tablet Smartphone Yojana",
                "issuing_body": "Department of IT and Electronics",
                "state": "Uttar Pradesh",
                "category": "Education",
                "description": "Free tablets and smartphones for college students and youth pursuing higher education in Uttar Pradesh",
                "eligibility_rules": {
                    "min_age": 18,
                    "max_age": 35,
                    "income_limit": 200000,
                }
            })
            # 5. Ayushman Bharat Yojana (Health)
            await vs.add_scheme({
                "name": "Ayushman Bharat Yojana",
                "issuing_body": "National Health Authority",
                "state": "Uttar Pradesh",
                "category": "Health",
                "description": "Universal health insurance coverage providing up to ₹5 Lakhs per family per year for hospitalization",
                "eligibility_rules": {
                    "income_limit": 250000,
                }
            })
            logger.info("[STARTUP] Auto-seeded local mock schemes successfully.")
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
