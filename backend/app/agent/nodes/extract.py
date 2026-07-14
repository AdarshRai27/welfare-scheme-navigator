"""Graph node extracting user profile attributes from raw user queries."""

import json
import logging
from typing import Any, Dict

from app.agent.prompts.prompt_templates import (
    PROFILE_EXTRACTION_PROMPT,
    simulate_llm_call,
)

logger = logging.getLogger(__name__)


async def extract_profile_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts demographic parameters from raw query text.

    Args:
        state: Shared graph state dictionary.

    Returns:
        State updates containing updated extracted_profile.
    """
    query = state.get("user_query", "")
    profile = state.get("extracted_profile", {}).copy()

    # Skip parameter extraction for system-generated triggers (e.g., OCR notifications)
    if query and not query.startswith("Extracted"):
        try:
            # Simulate or trigger LLM call to extract parameters
            extracted_json = simulate_llm_call(
                prompt_type="extract",
                variables={"query": query},
            )
            extracted_fields = json.loads(extracted_json)
            # Update profile in state
            profile.update(extracted_fields)
            logger.info(
                f"[AGENT extract_profile] Extracted fields: {extracted_fields}"
            )
        except Exception as err:
            logger.error(f"Failed to parse LLM profile extraction: {err}")

    return {"extracted_profile": profile}
