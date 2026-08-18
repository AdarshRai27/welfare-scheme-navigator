"""LLM service client for querying Groq API."""

import json
import logging
from typing import Any, Dict, List

import httpx

from app.agent.prompts.prompt_templates import (
    PROFILE_EXTRACTION_PROMPT,
    RESPONSE_COMPOSITION_PROMPT,
    simulate_llm_call,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


async def run_llm_completion(
    prompt: str, system_message: str = "You are a helpful assistant."
) -> str:
    """Sends a chat completion request prioritizing OpenAI (gpt-4o-mini) with Groq (llama-3.3-70b) failover.

    Args:
        prompt: User input string.
        system_message: Developer/System guidance instructions.

    Returns:
        Generated text response content.
    """
    # 1. Primary: OpenAI API (gpt-4o-mini) - Superior reasoning & multilingual instruction adherence
    if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock"):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.info("[OPENAI LLM] gpt-4o-mini primary response fetched successfully.")
                    return content
                else:
                    logger.warning(
                        f"[OPENAI LLM] API error ({res.status_code}): {res.text}. Trying Groq failover..."
                    )
        except Exception as err:
            logger.warning(f"[OPENAI LLM] Connection error: {err}. Trying Groq failover...")

    # 2. Secondary: Groq API (llama-3.3-70b-versatile) - Ultra-fast failover
    if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("mock"):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.info("[GROQ LLM] Response fetched successfully via failover.")
                    return content
                else:
                    logger.warning(f"[GROQ LLM] Failed response ({res.status_code}): {res.text}")
        except Exception as err:
            logger.warning(f"[GROQ LLM] Connection error: {err}")

    return ""


async def llm_extract_profile(query: str) -> Dict[str, Any]:
    """Extracts demographic parameters from raw text queries using LLM.

    Args:
        query: User text string.

    Returns:
        Parsed attributes dictionary.
    """
    has_api = (
        (settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("mock"))
        or (settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock"))
    )

    if has_api:
        prompt = PROFILE_EXTRACTION_PROMPT.format(query=query)
        response_text = await run_llm_completion(
            prompt=prompt,
            system_message=(
                "You are a JSON-only extraction engine for an Indian welfare schemes navigator. "
                "Extract exact numeric age, annual_income, land_size_hectares, state, caste_category, "
                "intent (_intent), and language (_language: 'hi', 'en', or 'hinglish'). "
                "Output ONLY valid raw JSON without markdown formatting or code fences."
            ),
        )
        if response_text:
            try:
                cleaned = (
                    response_text.replace("```json", "")
                    .replace("```", "")
                    .strip()
                )
                data = json.loads(cleaned)
                logger.info(
                    f"[LLM EXTRACT] Extracted parameters: {data}"
                )
                return data
            except Exception as err:
                logger.warning(
                    f"[LLM EXTRACT] Failed parsing JSON response '{response_text}': {err}"
                )

    # Fallback to deterministic simulation
    simulated_json = simulate_llm_call("extract", {"query": query})
    return json.loads(simulated_json)


async def llm_compose_response(
    profile: Dict[str, Any],
    eligible: List[Dict[str, Any]],
    suggested: List[Dict[str, Any]],
    query: str,
    intent: str = "SCHEME_QUERY",
    language: str = "hi",
) -> str:
    """Composes localized response markup using LLM.

    Args:
        profile: Active user demographic context.
        eligible: Matches passing rule constraints.
        suggested: Chained related matches.
        query: Original user query message.
        intent: Classified user query intent.
        language: Preferred language code.

    Returns:
        Markdown response.
    """
    has_api = (
        (settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("mock"))
        or (settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock"))
    )

    if has_api:
        prompt = RESPONSE_COMPOSITION_PROMPT.format(
            query=query,
            intent=intent,
            language=language,
            profile=json.dumps(profile, indent=2),
            eligible=json.dumps(eligible, indent=2),
            suggested=json.dumps(suggested, indent=2),
        )
        response_text = await run_llm_completion(
            prompt=prompt,
            system_message=(
                "You are Sarkari Sahayak, an AI government welfare advisor counselor. "
                "Strictly follow the bullet-point format rules, language matching rules, and ineligibility rules. "
                "Never suggest schemes that violate age, income, or land constraints."
            ),
        )
        if response_text:
            return response_text

    # Fallback to templates
    return simulate_llm_call(
        "compose",
        {
            "profile": profile,
            "eligible": eligible,
            "suggested": suggested,
            "query": query,
            "intent": intent,
            "language": language,
        },
    )


