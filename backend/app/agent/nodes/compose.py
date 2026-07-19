"""Graph node generating the final formatted user response text."""

import logging
from typing import Any, Dict

from app.services.llm import llm_compose_response

logger = logging.getLogger(__name__)


async def compose_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Composes final checklist response formatted in user's language.

    Args:
        state: Shared graph state dictionary.

    Returns:
        State updates containing composed reply_text.
    """


    profile = state.get("extracted_profile", {})
    eligible = state.get("eligible_schemes", [])
    suggested = state.get("suggested_schemes", [])
    query = state.get("user_query", "")

    # Generate response via template composition
    reply_text = await llm_compose_response(
        profile=profile,
        eligible=eligible,
        suggested=suggested,
        query=query,
    )

    logger.info("[AGENT compose_response] Composed markdown message.")
    return {"reply_text": reply_text}
