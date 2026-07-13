"""Prompt templates and simulated LLM inference wrapper for offline testing."""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

PROFILE_EXTRACTION_PROMPT = """
You are a demographic extraction agent. Output ONLY valid JSON containing parsed fields.
Extract attributes from the text: name, annual_income, age, land_size_hectares, state, caste_category.
Text: {query}
JSON Output:
"""

RESPONSE_COMPOSITION_PROMPT = """
You are an empathetic social worker helper. Formulate a reply in language: {language}.
Profile details: {profile}
Eligible schemes list: {eligible}
Suggested forward-chained schemes: {suggested}
Provide checklist and next steps.
Response:
"""


def simulate_llm_call(prompt_type: str, variables: Dict[str, Any]) -> str:
    """Simulates Llama 3.1 70B output for testing without running Ollama host.

    Args:
        prompt_type: Category identifier ('extract' or 'compose').
        variables: Formatter values needed by the prompt template.

    Returns:
        Structured response string.
    """
    logger.info(
        f"[MOCK LLM INFERENCE] Simulating call: type={prompt_type} | vars={list(variables.keys())}"
    )

    if prompt_type == "extract":
        query = variables.get("query", "").lower()
        extracted: Dict[str, Any] = {}
        # Parse basic parameters from query text
        if "age" in query or "year" in query:
            extracted["age"] = 35
        if "income" in query or "earn" in query:
            extracted["annual_income"] = 45000
        if "hectare" in query or "land" in query or "acre" in query:
            extracted["land_size_hectares"] = 1.5
        if "caste" in query or "obc" in query:
            extracted["caste_category"] = "OBC"
        return json.dumps(extracted)

    elif prompt_type == "compose":
        eligible = variables.get("eligible", [])
        suggested = variables.get("suggested", [])
        lang = variables.get("language", "hi")

        if not eligible and not suggested:
            if lang == "hi":
                return "नमस्ते, आपके विवरण के आधार पर आप अभी किसी योजना के लिए पात्र नहीं हैं।"
            return "Hello, based on your details, you do not currently qualify for any welfare schemes."

        output = []
        if lang == "hi":
            output.append(
                "नमस्ते! आपके विवरण के आधार पर आप निम्नलिखित योजनाओं के लिए पात्र हैं:\n"
            )
            for s in eligible:
                output.append(f"✅ **{s['name']}** — {s['description']}")
            if suggested:
                output.append(
                    "\n💡 **संबद्ध योजनाएं (आप इनके लिए भी पात्र हो सकते हैं):**"
                )
                for s in suggested:
                    output.append(
                        f"🔗 **{s['name']}** (पात्रता PM-Kisan से स्वतः निर्धारित)"
                    )
            output.append("\n📋 **आवश्यक दस्तावेज:** आधार कार्ड, आय प्रमाण पत्र।")
        else:
            output.append(
                "Hello! Based on your profile, you qualify for the following schemes:\n"
            )
            for s in eligible:
                output.append(f"✅ **{s['name']}** — {s['description']}")
            if suggested:
                output.append(
                    "\n💡 **Additional Related Schemes You May Qualify For:**"
                )
                for s in suggested:
                    output.append(
                        f"🔗 **{s['name']}** (auto-suggested via PM-Kisan eligibility)"
                    )
            output.append("\n📋 **Required Checklist:** Aadhaar Card, Income Certificate.")

        return "\n".join(output)

    return "Mock Response text"
