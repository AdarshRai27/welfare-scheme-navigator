"""Prompt templates and simulated LLM inference wrapper for offline testing."""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

PROFILE_EXTRACTION_PROMPT = """
You are an intent classification and demographic extraction engine for "Sarkari Sahayak", an Indian government welfare schemes assistant.

First, classify the user query into ONE of these 4 intents:
1. "META_LANGUAGE_COMMAND": The user wants to change or specify response language (e.g., "answer in hindi", "speak in english", "hinglish me bolo").
2. "GENERAL_GREETING": Greetings or general questions about what you do (e.g., "hi", "hello", "namaste", "who are you", "what can you do").
3. "OFF_TOPIC": Questions unrelated to Indian government welfare schemes (e.g. coding, sports, recipes, jokes, general knowledge).
4. "SCHEME_QUERY": Questions seeking welfare schemes, loans, pensions, subsidies, scholarships, or sharing personal profile details (age, income, land, state, Aadhaar).

Also detect target language: "hi" (Hindi), "en" (English), or "hinglish" (Hindi typed in English script).

Output ONLY valid JSON with keys:
- "_intent": string (one of "SCHEME_QUERY", "META_LANGUAGE_COMMAND", "GENERAL_GREETING", "OFF_TOPIC")
- "_language": string (one of "hi", "en", "hinglish")
- "name": string or null
- "annual_income": integer or null
- "age": integer or null
- "land_size_hectares": float or null
- "state": string or null
- "caste_category": string or null

Text: {query}
JSON Output:
"""

RESPONSE_COMPOSITION_PROMPT = """
You are a government welfare advisor counselor.
Analyze the user's query: "{query}"
Intent: {intent}
Preferred language: {language}

Format instructions:
1. Keep responses short, direct, and compact (WhatsApp style).
2. If intent is "META_LANGUAGE_COMMAND", politely acknowledge the requested language change and invite scheme questions in that language.
3. If intent is "GENERAL_GREETING", provide a friendly introduction explaining you assist with 50+ government welfare schemes.
4. If intent is "OFF_TOPIC", state politely that you only assist with Indian government welfare schemes and benefits.
5. If intent is "SCHEME_QUERY":
   - Print each eligible scheme name on its own line (e.g. **Scheme Name**).
   - Print the link on the next line (e.g. Link: http://example.com).
   - Print a brief bulleted list of eligibility criteria.

Profile details: {profile}
Eligible schemes: {eligible}
Suggested related schemes: {suggested}

Response:
"""

def simulate_llm_call(prompt_type: str, variables: Dict[str, Any]) -> str:
    """Simulates Llama output for testing without requiring remote endpoints.

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

        # Detect Hindi / Hinglish / English
        is_hindi = any(2304 <= ord(c) <= 2431 for c in query)
        words = query.split()
        is_hinglish = any(w in words for w in ["chahiye", "yojana", "mera", "karna", "krna", "liya", "liye", "kaise", "batao", "ko", "dukan", "kisan", "me", "mein", "bolo"])
        lang = "hi" if is_hindi else ("hinglish" if is_hinglish else "en")

        # 1. Meta Language Command Check
        lang_keywords = ["answer in hindi", "reply in hindi", "speak in hindi", "in hindi", "hindi me", "hindi mein", "hindi me batao", "hindi me bolo", "response in hindi", "change language to hindi", "answer in english", "reply in english", "speak in english", "in english", "english me", "english mein", "change language to english", "answer in hinglish", "reply in hinglish", "in hinglish", "hinglish me", "hinglish mein"]
        if any(k in query for k in lang_keywords):
            if "hindi" in query:
                target_lang = "hi"
            elif "english" in query:
                target_lang = "en"
            else:
                target_lang = "hinglish"
            return json.dumps({"_intent": "META_LANGUAGE_COMMAND", "_language": target_lang})

        # 2. General Greetings Check
        greetings = ["hi", "hello", "namaste", "hey", "who are you", "who r u", "kya kar sakte ho", "help", "madad", "kaun ho tum", "tell me about yourself", "what can you do"]
        if query in greetings or (len(query) < 15 and any(g in query for g in ["hi", "hello", "namaste", "hey"])):
            return json.dumps({"_intent": "GENERAL_GREETING", "_language": lang})

        # 3. Off-Topic Check
        off_topic_indicators = [
            "python", "java", "code", "programming", "function", "algorithm", "sort",
            "cricket", "world cup", "match", "score", "football", "ipl",
            "recipe", "cook", "cake", "biryani", "food",
            "joke", "movie", "actor", "song", "weather", "temperature",
            "who is prime minister", "who is president", "capital of"
        ]
        scheme_keywords = ["scheme", "yojana", "loan", "pension", "farmer", "kisan", "land", "income", "subsidy", "scholarship", "aadhaar", "certificate", "bima", "insurance", "ration", "business", "student", "female", "woman", "widow", "senior", "caste", "dukan", "mudra", "ayushman"]
        if any(o in query for o in off_topic_indicators) and not any(s in query for s in scheme_keywords):
            return json.dumps({"_intent": "OFF_TOPIC", "_language": lang})

        # 4. Default to SCHEME_QUERY & extract parameters
        extracted["_intent"] = "SCHEME_QUERY"
        extracted["_language"] = lang
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
        intent = variables.get("intent", "SCHEME_QUERY")
        explicit_lang = variables.get("language")
        if explicit_lang and explicit_lang in ["en", "hinglish", "hi"]:
            lang = explicit_lang
        else:
            is_hindi = any(2304 <= ord(c) <= 2431 for c in query)
            words = query.split()
            is_hinglish = any(w in words for w in ["chahiye", "yojana", "mera", "karna", "krna", "liya", "liye", "kaise", "batao", "ko", "dukan", "me", "mein", "bolo"])
            lang = "hi" if is_hindi else ("hinglish" if is_hinglish else "en")

        # Handle Meta Language Commands
        if intent == "META_LANGUAGE_COMMAND":
            if lang == "hi":
                return "नमस्ते! मैंने उत्तर देने की भाषा बदलकर हिंदी कर दी है। आप किस सरकारी योजना या सहायता के बारे में जानना चाहते हैं?"
            elif lang == "hinglish":
                return "Namaste! Maine response language badalkar Hinglish kar di hai. Aap kis sarkari yojana ke baare me janna chahte hain?"
            else:
                return "Hello! I have updated my response language to English. What government welfare scheme or benefit are you looking for today?"

        # Handle General Greetings
        if intent == "GENERAL_GREETING":
            if lang == "hi":
                return "नमस्ते! मैं आपका सरकारी सहायक हूँ। मैं आपको 50+ सरकारी कल्याणकारी योजनाओं (जैसे किसान सम्मान निधि, मुद्रा लोन, वरिष्ठ पेंशन, आयुष्मान भारत) की पात्रता जांचने और आवेदन करने में सहायता कर सकता हूँ। आप अपना प्रश्न पूछें या अपने दस्तावेज की फोटो स्कैन करें।"
            elif lang == "hinglish":
                return "Namaste! Main aapka Sarkari Sahayak hoon. Main aapko 50+ government welfare schemes (jaise PM-Kisan, Mudra Loan, Pension, Ayushman Bharat) me eligibility check karne aur search karne me help kar sakta hoon. Aap apna question poochein ya document scan karein."
            else:
                return "Hello! I am Sarkari Sahayak, your AI counselor for Indian government welfare schemes. I can help you discover and check eligibility for over 50 central and state schemes (such as PM-Kisan, Mudra Loans, Senior Pension, and Ayushman Bharat). How can I assist you today?"

        # Handle Off-Topic Queries (Domain Limitation Guardrail)
        if intent == "OFF_TOPIC":
            if lang == "hi":
                return "क्षमा करें! मैं केवल भारत सरकार की कल्याणकारी योजनाओं (जैसे पेंशन, किसान लाभ, बिजनेस लोन, छात्रवृत्ति) और उनकी पात्रता से संबंधित प्रश्नों के उत्तर देने के लिए ही तैयार किया गया हूँ। कृपया कल्याणकारी योजनाओं से संबंधित प्रश्न पूछें।"
            elif lang == "hinglish":
                return "Kshama karein! Main sirf Indian government welfare schemes (jaise pension, kisan labh, business loan, scholarship) aur unki eligibility check karne ke liye hi designed hoon. Kripya welfare schemes se related question poochein."
            else:
                return "I apologize, but I am specifically designed to assist only with Indian government welfare schemes, benefits, and eligibility checks (such as pensions, farmer subsidies, business loans, and scholarships). Please ask a question related to government schemes."

        # Handle Scheme Queries
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
