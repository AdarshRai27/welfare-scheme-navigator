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

Also detect target language: "hi" (Hindi in Devanagari), "en" (English), or "hinglish" (Hindi typed in Roman/English script).

Extract EXACT demographic attributes from the user's text:
- "name": string or null
- "annual_income": exact integer in Rupees (e.g. "₹2 lakh" -> 200000, "50k" -> 50000) or null
- "age": exact integer (e.g. "60 years old" -> 60) or null
- "land_size_hectares": float in Hectares (convert 1 acre -> 0.405 ha, e.g. "1.5 acres" -> 0.61) or null
- "state": recognized Indian state name (e.g. "Uttar Pradesh", "Bihar") or null
- "caste_category": string ("SC", "ST", "OBC", "General") or null
- "gender": string ("Male", "Female") or null

Output ONLY valid JSON:
Text: {query}
JSON Output:
"""

RESPONSE_COMPOSITION_PROMPT = """
You are Sarkari Sahayak, a professional Indian government welfare schemes counselor.
Analyze the user's query: "{query}"
Intent: {intent}
Preferred language: {language}

CRITICAL RULES:
1. Language matching:
   - If language is "hi", write the ENTIRE response in pure Hindi (Devanagari script).
   - If language is "hinglish", write in conversational Hinglish (Hindi written in Roman/English script).
   - If language is "en", write in clear English.
2. If the user does not qualify for any schemes (no eligible schemes found), YOU MUST RESPOND WITH:
   - English: "You are not eligible for any schemes in our current database, but we are expanding our database as we speak. Please visit again soon!"
   - Hindi: "वर्तमान में आप हमारे डेटाबेस की किसी योजना के लिए पात्र नहीं हैं, लेकिन हम लगातार नई योजनाएं जोड़ रहे हैं। कृपया जल्द ही पुनः संपर्क करें!"
   - Hinglish: "Aap hamare current database ki kisi scheme ke liye eligible nahi hain, lekin hum actively new schemes add kar rahe hain. Kripya jald hi dubara visit karein!"
3. If eligible schemes exist, structure EVERY response strictly in structured, scannable BULLET POINTS (using • and -):
   • **[Scheme Name]**
     - **Category / Ministry**: [Category & Issuing Body]
     - **Key Benefits**: [1 concise sentence summarizing benefits]
     - **Eligibility**: [Specific criteria like age, income, land, state]
     - **Official Portal**: [Visit Official Portal]([source_url])
4. For suggested/related schemes:
   • **Related Welfare Schemes to Explore:**
     - **[Scheme 1]** — [Brief description] • [Official Link]([source_url])
     - **[Scheme 2]** — [Brief description] • [Official Link]([source_url])
5. If intent is "META_LANGUAGE_COMMAND", politely acknowledge the language switch and invite questions.
6. If intent is "GENERAL_GREETING", welcome the user and explain you cover 125+ central & state welfare schemes.
7. If intent is "OFF_TOPIC", politely remind the user you specialize exclusively in Indian government welfare schemes.

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
        hinglish_words = {"chahiye", "yojana", "mera", "meri", "karna", "krna", "liya", "liye", "kaise", "batao", "bataiye", "ko", "dukan", "kisan", "kheti", "me", "mein", "bolo", "batao", "hai", "shuru", "milega", "padhai"}
        is_hinglish = any(w in hinglish_words for w in words)
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

        # 4. Default to SCHEME_QUERY & extract dynamic parameters using NLP regex
        from app.agent.nodes.extract import extract_demographics_from_text
        extracted = extract_demographics_from_text(query)
        extracted["_intent"] = "SCHEME_QUERY"
        extracted["_language"] = lang
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
            hinglish_words = {"chahiye", "yojana", "mera", "meri", "karna", "krna", "liya", "liye", "kaise", "batao", "bataiye", "ko", "dukan", "me", "mein", "bolo", "hai", "shuru", "milega", "padhai"}
            is_hinglish = any(w in hinglish_words for w in words)
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
                return "नमस्ते! मैं आपका सरकारी सहायक हूँ। 🙏\n\n• मैं आपको 125+ से अधिक केंद्रीय और राज्य सरकार की कल्याणकारी योजनाओं की पात्रता जांचने और आवेदन करने में सहायता कर सकता हूँ।\n• आप अपना प्रश्न पूछें (जैसे: 'मुझे दुकान के लिए लोन चाहिए' या 'किसान योजनाएं'), या अपने दस्तावेज की फोटो स्कैन करें।"
            elif lang == "hinglish":
                return "Namaste! Main aapka Sarkari Sahayak hoon. 🙏\n\n• Main aapko 125+ Central aur State government welfare schemes me eligibility check karne aur apply karne me help kar sakta hoon.\n• Aap apna question poochein ya Didit ID scan karein."
            else:
                return "Hello! I am Sarkari Sahayak, your AI counselor for Indian government welfare schemes. 🙏\n\n• I can help you discover and check eligibility for over 125 central and state welfare schemes (such as PM-Kisan, Mudra Loans, Senior Pension, Ayushman Bharat, and Student Scholarships).\n• How can I assist you today?"

        # Handle Off-Topic Queries (Domain Limitation Guardrail)
        if intent == "OFF_TOPIC":
            if lang == "hi":
                return "क्षमा करें! मैं केवल भारत सरकार की कल्याणकारी योजनाओं (जैसे पेंशन, किसान लाभ, बिजनेस लोन, छात्रवृत्ति) और उनकी पात्रता से संबंधित प्रश्नों के उत्तर देने के लिए ही तैयार किया गया हूँ। कृपया कल्याणकारी योजनाओं से संबंधित प्रश्न पूछें।"
            elif lang == "hinglish":
                return "Kshama karein! Main sirf Indian government welfare schemes (jaise pension, kisan labh, business loan, scholarship) aur unki eligibility check karne ke liye hi designed hoon. Kripya welfare schemes se related question poochein."
            else:
                return "I apologize, but I am specifically designed to assist only with Indian government welfare schemes, benefits, and eligibility checks (such as pensions, farmer subsidies, business loans, and scholarships). Please ask a question related to government schemes."

        # Helper to format eligibility rules cleanly
        def format_rules(r):
            if isinstance(r, dict):
                parts = []
                if "min_age" in r: parts.append(f"Age: {r['min_age']}+ yrs" if lang == "en" else f"आयु: {r['min_age']}+ वर्ष")
                if "max_age" in r: parts.append(f"Max Age: {r['max_age']} yrs" if lang == "en" else f"अधिकतम आयु: {r['max_age']} वर्ष")
                if "income_limit" in r: parts.append(f"Annual Income < ₹{r['income_limit']:,}" if lang == "en" else f"वार्षिक आय < ₹{r['income_limit']:,}")
                if "max_land_size_hectares" in r or "land_size_limit" in r:
                    limit = r.get("max_land_size_hectares") or r.get("land_size_limit")
                    parts.append(f"Landholding < {limit} Ha" if lang == "en" else f"भूमि < {limit} हेक्टेयर")
                if "gender" in r: parts.append(f"Gender: {r['gender']}" if lang == "en" else f"लिंग: {r['gender']}")
                if "caste_categories" in r: parts.append(f"Categories: {', '.join(r['caste_categories'])}" if lang == "en" else f"वर्ग: {', '.join(r['caste_categories'])}")
                if "state" in r: parts.append(f"State: {r['state']}" if lang == "en" else f"राज्य: {r['state']}")
                return "; ".join(parts) if parts else ("Citizen of India" if lang == "en" else "भारतीय नागरिक")
            return str(r)

        # Handle Scheme Queries (Ineligibility fallback requested by user)
        if not eligible and not suggested:
            if lang == "hi":
                return "वर्तमान में आप हमारे डेटाबेस की किसी योजना के लिए पात्र नहीं हैं, लेकिन हम लगातार नई योजनाएं जोड़ रहे हैं। कृपया जल्द ही पुनः संपर्क करें!"
            elif lang == "hinglish":
                return "Aap hamare current database ki kisi scheme ke liye eligible nahi hain, lekin hum actively new schemes add kar rahe hain. Kripya jald hi dubara visit karein!"
            return "You are not eligible for any schemes in our current database, but we are expanding our database as we speak. Please visit again soon!"

        # Output in clean, structured bullet points
        output = []
        if lang == "hi":
            output.append("नमस्ते! आपके विवरण के आधार पर आप निम्नलिखित योजनाओं के लिए पात्र हैं:\n")
            for s in eligible:
                output.append(f"• **{s['name']}**")
                output.append(f"  - **श्रेणी / विभाग**: {s.get('category', 'कल्याण')} • {s.get('issuing_body', 'भारत सरकार')}")
                if s.get("description"):
                    output.append(f"  - **मुख्य लाभ**: {s.get('description')}")
                output.append(f"  - **पात्रता मापदंड**: {format_rules(s.get('eligibility_rules'))}")
                output.append(f"  - **आधिकारिक आवेदन लिंक**: {s.get('source_url') or 'https://myscheme.gov.in'}\n")
            if suggested:
                output.append("• **संबद्ध कल्याणकारी योजनाएं:**")
                for s in suggested:
                    output.append(f"  - **{s['name']}** — {s.get('description', '')} • Link: {s.get('source_url') or 'https://myscheme.gov.in'}")
        elif lang == "hinglish":
            output.append("Namaste! Aapke profile details ke base par aap in schemes ke liye eligible hain:\n")
            for s in eligible:
                output.append(f"• **{s['name']}**")
                output.append(f"  - **Category / Ministry**: {s.get('category', 'Welfare')} • {s.get('issuing_body', 'Government')}")
                if s.get("description"):
                    output.append(f"  - **Key Benefits**: {s.get('description')}")
                output.append(f"  - **Eligibility criteria**: {format_rules(s.get('eligibility_rules'))}")
                output.append(f"  - **Link**: {s.get('source_url') or 'https://myscheme.gov.in'}\n")
            if suggested:
                output.append("• **Related schemes:**")
                for s in suggested:
                    output.append(f"  - **{s['name']}** — {s.get('description', '')} • Link: {s.get('source_url') or 'https://myscheme.gov.in'}")
        else:
            output.append("Hello! Based on your profile, you qualify for the following schemes:\n")
            for s in eligible:
                output.append(f"• **{s['name']}**")
                output.append(f"  - **Category / Department**: {s.get('category', 'Welfare')} • {s.get('issuing_body', 'Government of India')}")
                if s.get("description"):
                    output.append(f"  - **Key Benefits**: {s.get('description')}")
                output.append(f"  - **Eligibility criteria**: {format_rules(s.get('eligibility_rules'))}")
                output.append(f"  - **Link**: {s.get('source_url') or 'https://myscheme.gov.in'}\n")
            if suggested:
                output.append("• **Additional Related Schemes:**")
                for s in suggested:
                    output.append(f"  - **{s['name']}** — {s.get('description', '')} • Link: {s.get('source_url') or 'https://myscheme.gov.in'}")

        return "\n".join(output)

    return "Mock Response text"
