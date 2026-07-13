"""Scrapy runner and daily scheduler definitions for Celery Beat."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_celery_beat_schedule() -> Dict[str, Any]:
    """Returns the schedule configurations for the daily scraper tasks.

    Returns:
        Dictionary of Celery Beat schedule items.
    """
    return {
        "scrape-myscheme-daily": {
            "task": "app.scraper.tasks.run_myscheme_spider",
            # Run once every 24 hours (86400 seconds)
            "schedule": 86400.0,
        },
        "scrape-up-portal-daily": {
            "task": "app.scraper.tasks.run_up_portal_spider",
            "schedule": 86400.0,
        },
    }
