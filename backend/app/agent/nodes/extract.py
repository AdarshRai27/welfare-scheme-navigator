"""Graph node extracting user profile attributes from raw user queries."""

import json
import logging
from typing import Any, Dict

from app.services.llm import llm_extract_profile

logger = logging.getLogger(__name__)


async def extract_profile_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts demographic parameters and classifies user intent from raw query text.

    Args:
        state: Shared graph state dictionary.

    Returns:
        State updates containing extracted_profile, query_intent, and preferred_language.
    """
    query = state.get("user_query", "")
    profile = state.get("extracted_profile", {}).copy()
    current_lang = state.get("preferred_language", "hi")

    # If query is a system notification for OCR/Speech extraction (e.g. "Extracted income_certificate parameters...")
    if query and query.startswith("Extracted"):
        try:
            import ast
            import re
            dict_match = re.search(r"\{.*\}", query)
            if dict_match:
                dict_str = dict_match.group(0)
                try:
                    parsed = json.loads(dict_str.replace("'", '"'))
                except Exception:
                    parsed = ast.literal_eval(dict_str)
                for k, v in parsed.items():
                    if v is not None:
                        profile[k] = v
            logger.info(f"[AGENT extract_profile] Merged system extracted payload: {profile}")
            return {
                "extracted_profile": profile,
                "query_intent": "SCHEME_QUERY",
                "preferred_language": current_lang,
            }
        except Exception as err:
            logger.warning(f"Failed parsing Extracted query payload: {err}")

    # 1. Classify Intent and Language
    intent_data = await llm_extract_profile(query)
    
    # Extract fields if intent_data is a dict containing fields or intent info
    intent = intent_data.get("_intent", "SCHEME_QUERY")
    lang = intent_data.get("_language", current_lang)

    # 2. Extract profile fields if it's a scheme query or document upload
    for key, val in intent_data.items():
        if not key.startswith("_") and val is not None:
            profile[key] = val

    logger.info(
        f"[AGENT extract_profile] Intent: {intent} | Language: {lang} | Profile: {profile}"
    )

    return {
        "extracted_profile": profile,
        "query_intent": intent,
        "preferred_language": lang,
    }
