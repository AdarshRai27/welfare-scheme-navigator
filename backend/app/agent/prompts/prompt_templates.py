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
You are a government welfare advisor counselor.
Analyze the user's query: "{query}"

Match the language of your response exactly to the language of the user's query:
- If the query is in English, reply in English.
- If the query is in Hindi (Devanagari), reply in Hindi (Devanagari).
- If the query is in Hinglish (Hindi words typed in English script, e.g. "mujhko scheme chahiye"), reply in Hinglish.

Format instructions:
1. Keep the response short, direct, and compact (WhatsApp format). Do not include verbose headers or long introductions.
2. For each eligible scheme:
   - Print the scheme name on its own line (e.g. **Scheme Name**).
   - Print the application/info link on the very next line (e.g. Link: http://example.com).
   - Print a brief bulleted list of the eligibility criteria for that scheme on the following lines.
   - Separate schemes with a blank line.

Profile details: {profile}
Eligible schemes: {eligible}
Suggested related schemes: {suggested}

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
        query = variables.get("query", "").lower()

        # Detect language based on query content
        is_hindi = any(2304 <= ord(c) <= 2431 for c in query)
        is_hinglish = any(w in query for w in ["chahiye", "yojana", "mera", "karna", "krna", "liya", "liye", "kaise", "batao", "ko"])
        
        if is_hindi:
            lang = "hi"
        elif is_hinglish:
            lang = "hinglish"
        else:
            lang = "en"

        if not eligible and not suggested:
            if lang == "hi":
                return "नमस्ते, आपके विवरण के आधार पर आप अभी किसी योजना के लिए पात्र नहीं हैं।"
            elif lang == "hinglish":
                return "Namaste, aapke profile details ke base par aap abhi kisi yojana ke liye eligible nahi hain."
            return "Hello, based on your details, you do not currently qualify for any welfare schemes."

        output = []
        if lang == "hi":
            output.append("नमस्ते! आपके विवरण के आधार पर आप निम्नलिखित योजनाओं के लिए पात्र हैं:\n")
            for s in eligible:
                output.append(f"✅ **{s['name']}**")
                output.append(f"लिंक: {s.get('source_url') or 'https://myscheme.gov.in'}")
                output.append(f"पात्रता मानदंड: {s.get('eligibility_rules')}\n")
            if suggested:
                output.append("\n💡 **संबद्ध योजनाएं:**")
                for s in suggested:
                    output.append(f"🔗 **{s['name']}**")
                    output.append(f"लिंक: {s.get('source_url') or 'https://myscheme.gov.in'}\n")
        elif lang == "hinglish":
            output.append("Namaste! Aapke profile details ke base par aap in schemes ke liye eligible hain:\n")
            for s in eligible:
                output.append(f"✅ **{s['name']}**")
                output.append(f"Link: {s.get('source_url') or 'https://myscheme.gov.in'}")
                output.append(f"Eligibility criteria: {s.get('eligibility_rules')}\n")
            if suggested:
                output.append("\n💡 **Related schemes:**")
                for s in suggested:
                    output.append(f"🔗 **{s['name']}**")
                    output.append(f"Link: {s.get('source_url') or 'https://myscheme.gov.in'}\n")
        else:
            output.append("Hello! Based on your profile, you qualify for the following schemes:\n")
            for s in eligible:
                output.append(f"✅ **{s['name']}**")
                output.append(f"Link: {s.get('source_url') or 'https://myscheme.gov.in'}")
                output.append(f"Eligibility criteria: {s.get('eligibility_rules')}\n")
            if suggested:
                output.append("\n💡 **Additional Related Schemes:**")
                for s in suggested:
                    output.append(f"🔗 **{s['name']}**")
                    output.append(f"Link: {s.get('source_url') or 'https://myscheme.gov.in'}\n")

        return "\n".join(output)

    return "Mock Response text"
