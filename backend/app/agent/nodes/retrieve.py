"""Graph node querying vector store for potential candidate schemes."""

import logging
from typing import Any, Dict

from app.db.vector_store import VectorStore

logger = logging.getLogger(__name__)


async def retrieve_candidates_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieves candidate schemes from the database matching user context.

    Args:
        state: Shared graph state dictionary.

    Returns:
        State updates containing candidate_schemes list.
    """
    query = state.get("user_query", "")
    profile = state.get("extracted_profile", {})
    user_state = profile.get("state")

    store = VectorStore()
    # Fetch schemes ranking by cosine text similarity
    candidates = await store.search_similar_schemes(query, limit=5)

    # Filter out state-specific schemes that don't match the user's state
    filtered = []
    for c in candidates:
        scheme_state = c.get("state")
        if (
            scheme_state
            and user_state
            and scheme_state.lower() != user_state.lower()
        ):
            logger.debug(
                f"[AGENT retrieve_candidates] Filtered out {c['name']} (state mismatch)"
            )
            continue
        filtered.append(c)

    logger.info(
        f"[AGENT retrieve_candidates] Matched {len(filtered)} candidate schemes."
    )
    return {"candidate_schemes": filtered}
