"""Scrapy pipeline module to save scraped scheme items to database."""

import logging
from typing import Any, Dict

from scrapy import Spider

from app.db.vector_store import VectorStore

logger = logging.getLogger(__name__)


class SchemePipeline:
    """Processes and persists scraped scheme items to VectorStore."""

    async def process_item(
        self, item: Dict[str, Any], spider: Spider
    ) -> Dict[str, Any]:
        """Persists item into the configured database or memory cache.

        Args:
            item: Scraped scheme item attributes.
            spider: Executed spider instance.

        Returns:
            The processed item.
        """
        name = item.get("name", "Unnamed Scheme")
        logger.info(f"[SCRAPER PIPELINE] Ingesting scheme item: name='{name}'")

        # Save scheme to pgvector database (or in-memory cache)
        store = VectorStore()
        await store.add_scheme(item)

        return item
