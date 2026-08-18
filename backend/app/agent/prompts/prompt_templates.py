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
You are Sarkari Sahayak, an advanced AI counselor for Indian central and state welfare schemes.
Analyze the user's query: "{query}"
Intent: {intent}
Preferred language: {language}

CRITICAL REASONING & FORMATTING RULES:
1. Language matching:
   - If language is "hi", write the ENTIRE response in pure Hindi (Devanagari script).
   - If language is "hinglish", write in conversational Hinglish (Hindi written in Roman/English script).
   - If language is "en", write in clear, professional English.

2. Ineligibility Handling:
   - If no schemes qualify, respond ONLY with:
     * English: "You are not eligible for any schemes in our current database, but we are expanding our database as we speak. Please visit again soon!"
     * Hindi: "वर्तमान में आप हमारे डेटाबेस की किसी योजना के लिए पात्र नहीं हैं, लेकिन हम लगातार नई योजनाएं जोड़ रहे हैं। कृपया जल्द ही पुनः संपर्क करें!"
     * Hinglish: "Aap hamare current database ki kisi scheme ke liye eligible nahi hain, lekin hum actively new schemes add kar rahe hain. Kripya jald hi dubara visit karein!"

3. When Qualified Schemes Exist, structure in clean, scannable BULLET POINTS (• and -):
   • **[Scheme Name]**
     - **Beneficiary / Target**: [e.g. Primary Applicant (Age X) / Household / Senior Citizen]
     - **Category & Ministry**: [Category] • [Issuing Body]
     - **Key Benefits**: [Concise benefit explanation, including amounts like ₹6,000/yr, ₹5 Lakh cover, ₹3,000/mo pension]
     - **Eligibility**: [Exact matching criteria: age, income limit, land size, state domicile]
     - **Required Documents**: [e.g. Aadhaar Card, Land Revenue Record (Khatauni), Bank Passbook]
     - **Official Portal**: [Visit Official Portal]([source_url])

4. Household & Family Context:
   - If multiple family members were mentioned (e.g. spouse, children), clearly highlight which scheme applies to the primary applicant, spouse, or whole household (e.g. Ayushman Bharat for family health).

5. Transparent Disqualification Alternatives:
   - If the user specifically asked for a scheme that is disqualified due to age or income (e.g. PM-KMY), briefly explain why and point to the qualified alternative (e.g. PM-Kisan or Old Age Pension).

6. Suggested Related Schemes:
   • **Related Welfare Schemes to Explore:**
     - **[Scheme 1]** — [Brief benefit] • [Official Portal]([source_url])
     - **[Scheme 2]** — [Brief benefit] • [Official Portal]([source_url])

7. Domain Limitation Guardrail (Strict Refusal for Non-Scheme Topics):
   - If Intent is "OFF_TOPIC" (e.g. coding, math, sports, recipes, jokes, general knowledge, movies), DO NOT answer the non-scheme question. POLITELY REFUSE and state that you only assist with Indian central and state welfare schemes:
     * English: "I apologize, but I am specifically designed to assist exclusively with Indian government welfare schemes, benefits, and eligibility criteria (such as pensions, farmer subsidies, business loans, health insurance, and scholarships). Please ask a question related to government schemes."
     * Hindi: "क्षमा करें! मैं केवल भारत सरकार और राज्य सरकारों की कल्याणकारी योजनाओं (जैसे पेंशन, किसान लाभ, बिजनेस लोन, छात्रवृत्ति, स्वास्थ्य बीमा) से संबंधित प्रश्नों के उत्तर देने के लिए तैयार किया गया हूँ। कृपया सरकारी योजनाओं से संबंधित प्रश्न पूछें।"
     * Hinglish: "Kshama karein! Main sirf Indian government welfare schemes (jaise pension, kisan labh, business loan, scholarship, health insurance) se related questions ke answers dene ke liye designed hoon. Kripya government schemes se related question poochein."

8. Greetings & Meta Commands:
   - If Intent is "GENERAL_GREETING", warmly welcome the user and explain you cover 125+ central & state welfare schemes.
   - If Intent is "META_LANGUAGE_COMMAND", acknowledge the language preference change politely.

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

        # Scheme localization helper for pure Hindi / Hinglish translation
        HINDI_SCHEMES_MAP = {
            "PM-Kisan Samman Nidhi": {
                "name_hi": "पीएम-किसान सम्मान निधि (PM-KISAN)",
                "category_hi": "कृषि",
                "body_hi": "कृषि एवं किसान कल्याण मंत्रालय, भारत सरकार",
                "desc_hi": "पात्र भूमिधारक किसान परिवारों को ₹6,000 प्रति वर्ष की प्रत्यक्ष वित्तीय सहायता (₹2,000 की 3 समान किश्तों में सीधे बैंक खाते में)।",
                "desc_hinglish": "Eligible landowning farmer families ko ₹6,000 har saal DBT ke through (₹2,000 ki 3 installments me)."
            },
            "Pradhan Mantri Fasal Bima Yojana (PMFBY)": {
                "name_hi": "प्रधानमंत्री फसल बीमा योजना (PMFBY)",
                "category_hi": "कृषि",
                "body_hi": "कृषि एवं किसान कल्याण मंत्रालय, भारत सरकार",
                "desc_hi": "बाढ़, सूखा, कीट हमले और बेमौसम बारिश से फसल नुकसान के विरुद्ध 1.5% से 2% के न्यूनतम प्रीमियम पर व्यापक बीमा सुरक्षा।",
                "desc_hinglish": "Fasal nuksan, baadh ya sookha ke against kam premium (1.5%-2%) par complete crop insurance coverage."
            },
            "Kisan Credit Card (KCC) Scheme": {
                "name_hi": "किसान क्रेडिट कार्ड (KCC) योजना",
                "category_hi": "कृषि एवं ऋण",
                "body_hi": "कृषि एवं किसान कल्याण मंत्रालय, भारत सरकार",
                "desc_hi": "कृषि उत्पादन, डेयरी, पशुपालन और मत्स्य पालन के लिए 4% की रियायती ब्याज दर पर ₹3,00,000 तक का आसान संस्थागत ऋण।",
                "desc_hinglish": "Kheti, dairy aur pashupalan ke liye 4% cheap interest rate par ₹3 Lakh tak ka concessional credit limit."
            },
            "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY - Micro Irrigation)": {
                "name_hi": "प्रधानमंत्री कृषि सिंचाई योजना (PMKSY - सूक्ष्म सिंचाई)",
                "category_hi": "कृषि एवं सिंचाई",
                "body_hi": "कृषि एवं किसान कल्याण मंत्रालय, भारत सरकार",
                "desc_hi": "खेतों में ड्रिप और स्प्रिंकलर सिंचाई प्रणाली लगाने के लिए छोटे और सीमांत किसानों को 55% तक की प्रत्यक्ष सरकारी सब्सिडी।",
                "desc_hinglish": "Drip aur sprinkler micro-irrigation system lagane ke liye 55% tak ki government subsidy."
            },
            "Sub-Mission on Agricultural Mechanization (SMAM - Tractor & Farm Machinery Subsidy)": {
                "name_hi": "कृषि यंत्रीकरण उप-मिशन (SMAM - ट्रैक्टर एवं कृषि यंत्र सब्सिडी)",
                "category_hi": "कृषि यंत्रीकरण",
                "body_hi": "कृषि एवं किसान कल्याण मंत्रालय, भारत सरकार",
                "desc_hi": "ट्रैक्टर, पावर टिलर और आधुनिक कृषि उपकरण खरीदने के लिए किसानों को 40% से 50% तक की वित्तीय सब्सिडी।",
                "desc_hinglish": "Tractors aur modern agriculture machinery purchase karne ke liye 40% se 50% tak ki subsidy."
            },
            "UP Senior Pension Scheme": {
                "name_hi": "उत्तर प्रदेश वृद्धावस्था पेंशन योजना",
                "category_hi": "सामाजिक सुरक्षा एवं पेंशन",
                "body_hi": "समाज कल्याण विभाग, उत्तर प्रदेश सरकार",
                "desc_hi": "60 वर्ष या उससे अधिक आयु के बीपीएल/गरीब वरिष्ठ नागरिकों को ₹1,000 प्रति माह की प्रत्यक्ष मासिक पेंशन सहायता।",
                "desc_hinglish": "60+ age ke eligible senior citizens ko ₹1,000 per month direct monthly pension support."
            },
            "Indira Gandhi National Old Age Pension Scheme (IGNOAPS)": {
                "name_hi": "इंदिरा गांधी राष्ट्रीय वृद्धावस्था पेंशन योजना (IGNOAPS)",
                "category_hi": "सामाजिक सुरक्षा एवं पेंशन",
                "body_hi": "ग्रामीण विकास मंत्रालय, भारत सरकार",
                "desc_hi": "60 वर्ष या अधिक आयु के बीपीएल परिवारों के वृद्ध नागरिकों को केंद्र एवं राज्य सरकार द्वारा मासिक पेंशन।",
                "desc_hinglish": "60+ age ke BPL senior citizens ke liye monthly social security pension."
            },
            "Ayushman Bharat - PMJAY (Pradhan Mantri Jan Arogya Yojana)": {
                "name_hi": "आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना (PM-JAY)",
                "category_hi": "स्वास्थ्य सुरक्षा",
                "body_hi": "राष्ट्रीय स्वास्थ्य प्राधिकरण, भारत सरकार",
                "desc_hi": "पात्र परिवारों एवं 70 वर्ष से अधिक आयु के सभी वरिष्ठ नागरिकों को प्रति वर्ष ₹5 लाख तक का कैशलेस अस्पताल इलाज।",
                "desc_hinglish": "Eligible families aur 70+ age ke sabhi senior citizens ko ₹5 Lakh/year tak ka cashless hospital treatment."
            },
            "PM Surya Ghar: Muft Bijli Yojana": {
                "name_hi": "पीएम सूर्य घर: मुफ्त बिजली योजना",
                "category_hi": "नवीकरणीय ऊर्जा",
                "body_hi": "नवीन एवं नवीकरणीय ऊर्जा मंत्रालय, भारत सरकार",
                "desc_hi": "छतों पर सोलर पैनल लगाने के लिए ₹78,000 तक की प्रत्यक्ष सब्सिडी और 300 यूनिट मुफ्त बिजली प्रति माह।",
                "desc_hinglish": "Rooftop solar panels lagane ke liye ₹78,000 subsidy aur 300 units free electricity per month."
            },
            "Pradhan Mantri Mudra Yojana (PMMY)": {
                "name_hi": "प्रधानमंत्री मुद्रा योजना (PMMY - शिशु/किशोर/तरुण)",
                "category_hi": "व्यापार एवं सूक्ष्म ऋण",
                "body_hi": "वित्तीय सेवाएं विभाग, भारत सरकार",
                "desc_hi": "दुकान, नया व्यवसाय और सूक्ष्म उद्यम शुरू या बढ़ाने के लिए बिना किसी गारंटी के ₹50,000 से ₹10 लाख तक का व्यापार ऋण।",
                "desc_hinglish": "Small business aur startup ke liye collateral-free loan up to ₹10,00,000."
            }
        }

        def get_loc_field(s, field):
            name = s.get("name", "")
            loc_entry = None
            for k, v in HINDI_SCHEMES_MAP.items():
                if k.lower() in name.lower() or name.lower() in k.lower():
                    loc_entry = v
                    break
            
            if lang == "hi":
                if field == "name": return loc_entry.get("name_hi") if loc_entry else name
                if field == "category": return loc_entry.get("category_hi") if loc_entry else (s.get("category") or "कल्याण")
                if field == "body": return loc_entry.get("body_hi") if loc_entry else (s.get("issuing_body") or "भारत सरकार")
                if field == "desc": return loc_entry.get("desc_hi") if loc_entry else (s.get("description") or "")
            elif lang == "hinglish":
                if field == "desc": return loc_entry.get("desc_hinglish") if loc_entry else (s.get("description") or "")
                if field == "category": return s.get("category") or "Welfare"
                if field == "body": return s.get("issuing_body") or "Government"
                if field == "name": return name
            return s.get(field) or ""

        # Output in clean, structured bullet points with explicit Markdown spacing
        output = []
        if lang == "hi":
            output.append("नमस्ते! आपके विवरण के आधार पर आप निम्नलिखित योजनाओं के लिए पात्र हैं:\n")
            for s in eligible:
                s_name = get_loc_field(s, "name")
                s_cat = get_loc_field(s, "category")
                s_body = get_loc_field(s, "body")
                s_desc = get_loc_field(s, "desc")
                docs = "आधार कार्ड, बैंक पासबुक, भू-अभिलेख (खतौनी)" if "Agriculture" in s.get("category", "") or "कृषि" in str(s_cat) else "आधार कार्ड, बैंक पासबुक, आय प्रमाण पत्र"
                output.append(
                    f"• **{s_name}**\n"
                    f"  - **श्रेणी / विभाग**: {s_cat} • {s_body}\n"
                    f"  - **मुख्य लाभ**: {s_desc}\n"
                    f"  - **पात्रता मापदंड**: {format_rules(s.get('eligibility_rules'))}\n"
                    f"  - **आवश्यक दस्तावेज़**: {docs}\n"
                    f"  - **आधिकारिक आवेदन लिंक**: {s.get('source_url') or 'https://myscheme.gov.in'}\n"
                )
            if suggested:
                output.append("• **संबद्ध कल्याणकारी योजनाएं:**")
                for s in suggested:
                    s_name = get_loc_field(s, "name")
                    s_desc = get_loc_field(s, "desc")
                    output.append(f"  - **{s_name}** — {s_desc} • [पोर्टल लिंक]({s.get('source_url') or 'https://myscheme.gov.in'})")
        elif lang == "hinglish":
            output.append("Namaste! Aapke profile details ke base par aap in schemes ke liye eligible hain:\n")
            for s in eligible:
                s_name = s.get("name", "")
                s_desc = get_loc_field(s, "desc")
                docs = "Aadhaar Card, Bank Passbook, Land Record (Khatauni)" if "Agriculture" in s.get("category", "") else "Aadhaar Card, Bank Passbook, Income Certificate"
                output.append(
                    f"• **{s_name}**\n"
                    f"  - **Category / Ministry**: {s.get('category', 'Welfare')} • {s.get('issuing_body', 'Government')}\n"
                    f"  - **Key Benefits**: {s_desc}\n"
                    f"  - **Eligibility criteria**: {format_rules(s.get('eligibility_rules'))}\n"
                    f"  - **Required Documents**: {docs}\n"
                    f"  - **Official Portal**: {s.get('source_url') or 'https://myscheme.gov.in'}\n"
                )
            if suggested:
                output.append("• **Related schemes:**")
                for s in suggested:
                    s_desc = get_loc_field(s, "desc")
                    output.append(f"  - **{s['name']}** — {s_desc} • [Official Link]({s.get('source_url') or 'https://myscheme.gov.in'})")
        else:
            output.append("Hello! Based on your profile, you qualify for the following schemes:\n")
            for s in eligible:
                docs = "Aadhaar Card, Bank Passbook, Land Revenue Record (Khatauni)" if "Agriculture" in s.get("category", "") else "Aadhaar Card, Bank Passbook, Income Certificate"
                output.append(
                    f"• **{s['name']}**\n"
                    f"  - **Category / Ministry**: {s.get('category', 'Welfare')} • {s.get('issuing_body', 'Government of India')}\n"
                    f"  - **Key Benefits**: {s.get('description', '')}\n"
                    f"  - **Eligibility criteria**: {format_rules(s.get('eligibility_rules'))}\n"
                    f"  - **Required Documents**: {docs}\n"
                    f"  - **Official Application Portal**: {s.get('source_url') or 'https://myscheme.gov.in'}\n"
                )
            if suggested:
                output.append("• **Additional Related Schemes:**")
                for s in suggested:
                    output.append(f"  - **{s['name']}** — {s.get('description', '')} • [Official Portal]({s.get('source_url') or 'https://myscheme.gov.in'})")

        return "\n\n".join(output)

    return "Mock Response text"
