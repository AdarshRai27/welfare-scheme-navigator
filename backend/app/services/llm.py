"""LLM service client for querying Groq or local Ollama instances."""

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
    """Sends a chat completion request to the Groq API.

    Args:
        prompt: User input string.
        system_message: Developer/System guidance instructions.

    Returns:
        Generated text response content.
    """
    if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("mock"):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.info(
                        "[GROQ LLM] Cloud model response fetched successfully."
                    )
                    return content
                else:
                    logger.warning(
                        f"[GROQ LLM] Failed response (status {res.status_code}): {res.text}. Falling back."
                    )
        except Exception as err:
            logger.warning(
                f"[GROQ LLM] Connection error: {err}. Falling back."
            )

    return ""


async def llm_extract_profile(query: str) -> Dict[str, Any]:
    """Extracts demographic parameters from raw text queries using LLM.

    Args:
        query: User text string.

    Returns:
        Parsed attributes dictionary.
    """
    if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("mock"):
        prompt = PROFILE_EXTRACTION_PROMPT.format(query=query)
        response_text = await run_llm_completion(
            prompt=prompt,
            system_message=(
                "You are a JSON-only extraction engine. Output ONLY valid raw JSON "
                "containing parsed fields. Do not include markdown wraps or explanations."
            ),
        )
        if response_text:
            try:
                # Clean potential markdown wraps (e.g. ```json)
                cleaned = (
                    response_text.replace("```json", "")
                    .replace("```", "")
                    .strip()
                )
                data = json.loads(cleaned)
                logger.info(
                    f"[LLM EXTRACT] Extracted parameters via Groq: {data}"
                )
                return data
            except Exception as err:
                logger.warning(
                    f"[LLM EXTRACT] Failed parsing LLM response '{response_text}': {err}"
                )

    # Fallback to simulation
    simulated_json = simulate_llm_call("extract", {"query": query})
    return json.loads(simulated_json)


async def llm_compose_response(
    profile: Dict[str, Any],
    eligible: List[Dict[str, Any]],
    suggested: List[Dict[str, Any]],
    language: str,
) -> str:
    """Composes localized response markup using LLM.

    Args:
        profile: Active user demographic context.
        eligible: Matches passing rule constraints.
        suggested: Chained related matches.
        language: Language preference string.

    Returns:
        Markdown response.
    """
    if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("mock"):
        prompt = RESPONSE_COMPOSITION_PROMPT.format(
            language=language,
            profile=json.dumps(profile, indent=2),
            eligible=json.dumps(eligible, indent=2),
            suggested=json.dumps(suggested, indent=2),
        )
        response_text = await run_llm_completion(
            prompt=prompt,
            system_message=(
                "You are a government welfare schemes counselor. Outline eligibility, "
                "list checklists, and point them to pre-filled applications. Keep replies "
                "clear, empathetic, and formatted in markdown."
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
            "language": language,
        },
    )
