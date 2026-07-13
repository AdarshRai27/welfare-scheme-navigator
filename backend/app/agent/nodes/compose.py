"""Graph node generating the final formatted user response text."""

import logging
from typing import Any, Dict

from app.agent.prompts.prompt_templates import simulate_llm_call

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
    language = state.get("preferred_language", "hi")

    # Generate response via template composition
    reply_text = simulate_llm_call(
        prompt_type="compose",
        variables={
            "profile": profile,
            "eligible": eligible,
            "suggested": suggested,
            "language": language,
        },
    )

    logger.info("[AGENT compose_response] Composed markdown message.")
    return {"reply_text": reply_text}
