"""Graph node extracting user profile attributes from raw user queries."""

import json
import logging
import re
from typing import Any, Dict

from app.services.llm import llm_extract_profile

logger = logging.getLogger(__name__)

# Indian States and Union Territories dictionary for entity recognition
INDIAN_STATES = {
    "andhra pradesh": "Andhra Pradesh", "ap": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh", "hp": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh", "mp": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha", "orissa": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu", "tn": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh", "up": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal", "wb": "West Bengal",
    "delhi": "Delhi",
}


# 8 Core Welfare Domain Pillars (Domain Whitelist)
WELFARE_DOMAIN_TAXONOMY = {
    "agriculture": [
        "kisan", "farmer", "agriculture", "crop", "fasal", "kheti", "seed", "fertilizer", "soil", "tractor", "machinery",
        "irrigation", "sinchayee", "drip", "sprinkler", "dairy", "pashupalan", "animal husbandry", "fisheries", "matsya",
        "kcc", "kisan credit", "pm-kisan", "pmkisan", "pmfby", "fasal bima", "krishi", "कृषि", "किसान", "फसल", "खेती"
    ],
    "social_security": [
        "pension", "old age", "vridha", "senior citizen", "widow", "divyang", "disability", "social security",
        "ignaps", "atal pension", "apy", "shramik", "unorganized worker", "पेंशन", "वृद्धावस्था", "विधवा", "दिव्यांग"
    ],
    "healthcare": [
        "health", "medical", "hospital", "doctor", "treatment", "ayushman", "pmjay", "jan arogya", "bima", "insurance",
        "maternity", "matru vandana", "pmmvy", "jan aushadhi", "medicine", "स्वास्थ्य", "इलाज", "अस्पताल", "आयुष्मान"
    ],
    "livelihood_loans": [
        "loan", "credit", "mudra", "svanidhi", "street vendor", "shop", "dukan", "business", "vyapar", "startup",
        "pmegp", "standup india", "vishwakarma", "artisan", "karigar", "self help group", "shg", "लोन", "ऋण", "व्यापार", "दुकान"
    ],
    "education_skills": [
        "scholarship", "student", "school", "college", "education", "padhai", "pmkvy", "skill", "training",
        "pre-matric", "post-matric", "vidyarthi", "छात्रवृत्ति", "छात्र", "शिक्षा", "पढ़ाई", "कौशल"
    ],
    "housing_energy": [
        "awas", "housing", "pmay", "ghar", "makaan", "solar", "surya ghar", "electricity", "bijli", "lpg", "gas", "ujjwala",
        "आवास", "घर", "मकान", "सोलर", "बिजली", "उज्ज्वला"
    ],
    "women_child": [
        "women", "mahila", "girl child", "beti", "sukanya", "samriddhi", "ladli behna", "matru", "widow", "mahila samman",
        "महिला", "बेटी", "सुकन्या", "लाडली"
    ],
    "citizen_profile_params": [
        "scheme", "yojana", "eligibility", "benefit", "apply", "portal", "subsidy", "aadhaar", "income", "land",
        "hectare", "acre", "state", "domicile", "caste", "rashan", "ration", "khatauni", "certificate", "money",
        "financial assistance", "grant", "sarkari sahayata", "sarkari yojana",
        "आधार", "आय", "रकबा", "जमीन", "भूमि", "राशन", "खतौनी", "जाति", "निवास", "पात्रता", "योजना", "सरकारी सहायता"
    ]
}


def is_in_welfare_domain(query: str) -> bool:
    """Checks if query touches any of the 8 Indian Welfare Domain Pillars."""
    lowered = query.lower()
    for pillar, terms in WELFARE_DOMAIN_TAXONOMY.items():
        if any(term in lowered for term in terms):
            return True
    return False


def extract_demographics_from_text(text: str) -> Dict[str, Any]:
    """Deterministic NLP entity extractor for age, income, land, and state from user prompt."""
    lowered = text.lower()
    res: Dict[str, Any] = {}

    # 1. Extract Name
    name_match = re.search(r'(?:मेरा नाम|my name is|name is|i am)\s+([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+)?)', lowered)
    if name_match:
        cand_name = name_match.group(1).strip()
        if not any(w in cand_name.lower() for w in ["a", "an", "the", "farmer", "kisan", "citizen", "from", "years"]):
            res["name"] = cand_name.title()

    # 1a. Extract Primary Age & Birth Year
    # Matches: "52-year-old", "52 years old", "i am a 52 year old", "उम्र 59 साल", "जन्म वर्ष 1964"
    birth_year_match = re.search(r'(?:जन्म वर्ष|जन्म का वर्ष|birth year|year of birth|dob|born in)\s*(?:is|:)?\s*(\d{4})', lowered)
    if birth_year_match:
        try:
            byear = int(birth_year_match.group(1))
            if 1920 <= byear <= 2026:
                res["age"] = 2026 - byear
                res["birth_year"] = byear
        except Exception:
            pass

    if "age" not in res:
        age_match = re.search(r'(\d{1,3})[\s\-]*(?:years?|yrs?|yr|saal|varsh|वर्ष|साल)[\s\-]*(?:old)?', lowered)
        if not age_match:
            age_match = re.search(r'(?:i am|i\'m|age is|age|aged|उम्र|आयु)\s*(?:a|an)?\s*(?:is|:)?\s*(\d{1,3})', lowered)
        if not age_match:
            age_match = re.search(r'(?:farmer|citizen|man|woman|person|applicant)\s*(?:of|aged|age)?\s*(\d{1,3})', lowered)
        if not age_match:
            age_match = re.search(r'\b(\d{1,2})\s*(?:yo|y/o)\b', lowered)
        if age_match:
            try:
                res["age"] = int(age_match.group(1))
            except Exception:
                pass

    # 1b. Extract Spouse & Dependents (Family Context)
    spouse_match = re.search(r'(?:wife|husband|patni|pati|spouse)\s*(?:is|age|of)?\s*(\d{1,3})', lowered)
    if spouse_match:
        try:
            res["spouse_age"] = int(spouse_match.group(1))
        except Exception:
            pass

    child_match = re.search(r'(?:son|daughter|child|kid|baccha|beti|beta)\s*(?:is|age)?\s*(\d{1,3})', lowered)
    if child_match:
        try:
            res["dependent_age"] = int(child_match.group(1))
        except Exception:
            pass

    if any(w in lowered for w in ["student", "school", "college", "padhai", "scholarship", "study", "class"]):
        res["has_student"] = True

    # 2. Extract Annual Income
    # Matches: "₹2 lakh", "₹1.9 लाख", "2 lakh", "2 lac", "₹2,00,000", "45000", "50k", "2L"
    income_match = re.search(r'(?:income|earn|kamai|salary|aay|आय)\s*(?:is|of|:)?\s*₹?\s*([\d,\.]+)\s*(लाख|हजार|करोड़|lakh|lac|k|crore|cr|hazaar|thousand|l)?', lowered)
    if not income_match:
        income_match = re.search(r'₹\s*([\d,\.]+)\s*(लाख|हजार|करोड़|lakh|lac|k|crore|cr|l)?', lowered)
    
    if income_match:
        val_str = income_match.group(1).replace(",", "").strip()
        unit = (income_match.group(2) or "").strip().lower()
        try:
            num = float(val_str)
            if unit in ("lakh", "lac", "l", "लाख"):
                res["annual_income"] = int(num * 100000)
            elif unit in ("k", "hazaar", "thousand", "हजार"):
                res["annual_income"] = int(num * 1000)
            elif unit in ("crore", "cr", "करोड़"):
                res["annual_income"] = int(num * 10000000)
            else:
                res["annual_income"] = int(num)
        except Exception:
            pass

    # 3. Extract Land Size (normalize to hectares)
    # 1 Acre = 0.404686 Hectares
    land_match = re.search(r'([\d\.]+)\s*(acres?|acre|एकड़|hectares?|hectare|ha|हेक्टेयर|bigha|बीघा)', lowered)
    if land_match:
        try:
            val = float(land_match.group(1))
            unit = land_match.group(2).lower()
            if "acre" in unit or "एकड़" in unit:
                res["land_size_hectares"] = round(val * 0.404686, 2)
            elif "bigha" in unit or "बीघा" in unit:
                res["land_size_hectares"] = round(val * 0.25, 2)
            else:
                res["land_size_hectares"] = round(val, 2)
        except Exception:
            pass

    # 4. Extract State (support both English and Devanagari)
    hindi_states_map = {
        "यूपी": "Uttar Pradesh", "यू.पी.": "Uttar Pradesh", "उत्तर प्रदेश": "Uttar Pradesh",
        "बिहार": "Bihar", "राजस्थान": "Rajasthan", "मध्य प्रदेश": "Madhya Pradesh", "एमपी": "Madhya Pradesh",
        "महाराष्ट्र": "Maharashtra", "गुजरात": "Gujarat", "पंजाब": "Punjab", "हरियाणा": "Haryana",
        "उत्तराखंड": "Uttarakhand", "पश्चिम बंगाल": "West Bengal", "दिल्ली": "Delhi",
        "तमिलनाडु": "Tamil Nadu", "कर्नाटक": "Karnataka", "केरल": "Kerala", "ओडिशा": "Odisha",
        "झारखंड": "Jharkhand", "छत्तीसगढ़": "Chhattisgarh", "असम": "Assam", "तेलंगाना": "Telangana",
        "आंध्र प्रदेश": "Andhra Pradesh"
    }
    for h_token, h_full in hindi_states_map.items():
        if h_token in lowered:
            res["state"] = h_full
            break

    if "state" not in res:
        for token, full_name in INDIAN_STATES.items():
            pattern = r'\b' + re.escape(token) + r'\b'
            if re.search(pattern, lowered):
                res["state"] = full_name
                break

    # 5. Extract Caste Category with strict word boundary matching
    if re.search(r'\b(?:sc|अनुसूचित जाति|scheduled caste)\b', lowered):
        res["caste_category"] = "SC"
    elif re.search(r'\b(?:st|अनुसूचित जनजाति|scheduled tribe)\b', lowered):
        res["caste_category"] = "ST"
    elif re.search(r'\b(?:obc|अन्य पिछड़ा वर्ग|other backward)\b', lowered):
        res["caste_category"] = "OBC"
    elif re.search(r'\b(?:general category|सामान्य वर्ग|gen category)\b', lowered):
        res["caste_category"] = "General"

    # 6. Extract Gender with word boundary matching
    if re.search(r'\b(?:female|woman|women|mahila|aurat|lady|girl|महिला|औरत)\b', lowered):
        res["gender"] = "Female"
    elif re.search(r'\b(?:male|man|purush|boy|पुरुष|आदमी)\b', lowered):
        res["gender"] = "Male"

    return res


async def extract_profile_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts demographic parameters and classifies user intent from raw query text.

    Args:
        state: Shared graph state dictionary.

    Returns:
        State updates containing extracted_profile, query_intent, and preferred_language.
    """
    query = state.get("user_query", "")
    profile = state.get("extracted_profile", {}).copy()
    current_lang = state.get("preferred_language", "en")

    # If query is a system notification for OCR/Speech extraction (e.g. "Extracted parameters...")
    if query and query.startswith("Extracted"):
        try:
            import ast
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
            logger.info(f"[AGENT extract_profile] System extracted profile state: {profile}")
            return {
                "extracted_profile": profile,
                "query_intent": "SCHEME_QUERY",
                "preferred_language": current_lang,
            }
        except Exception as err:
            logger.warning(f"Failed parsing Extracted query payload: {err}")

    # 1. Deterministic NLP extraction
    nlp_fields = extract_demographics_from_text(query)
    for k, v in nlp_fields.items():
        if v is not None:
            profile[k] = v

    # 1. Deterministic Language Detection
    is_hindi_script = any(2304 <= ord(c) <= 2431 for c in query)
    words = query.lower().split()
    unambiguous_hinglish = {
        "chahiye", "yojana", "mera", "meri", "karna", "krna", "liya", "liye", "kaise", "batao", "bataiye",
        "dukan", "kisan", "kheti", "mein", "bolo", "shuru", "milega", "padhai", "paisa", "paise", "madad", "sarkari"
    }
    is_hinglish_text = any(w in unambiguous_hinglish for w in words)
    
    if is_hindi_script:
        resolved_lang = "hi"
    elif is_hinglish_text:
        resolved_lang = "hinglish"
    else:
        resolved_lang = current_lang or "en"

    # 2. Meta Language Command Check (Multi-lingual)
    lowered_q = query.lower().strip()
    lang_commands_hi = ["हिंदी में", "हिन्दी में", "हिंदी मे", "हिंदी में बोलो", "हिंदी में बात करो", "हिंदी में बताओ", "भाषा बदलो", "hindi me", "hindi mein", "hindi me bolo", "hindi me batao", "speak in hindi", "reply in hindi", "answer in hindi"]
    lang_commands_en = ["अंग्रेजी में", "इंग्लिश में", "english me", "english mein", "speak in english", "reply in english", "answer in english"]
    lang_commands_hinglish = ["हिंग्लिश में", "hinglish me", "hinglish mein", "speak in hinglish", "reply in hinglish", "answer in hinglish"]

    if any(k in lowered_q for k in lang_commands_hi):
        return {"extracted_profile": profile, "query_intent": "META_LANGUAGE_COMMAND", "preferred_language": "hi"}
    if any(k in lowered_q for k in lang_commands_en):
        return {"extracted_profile": profile, "query_intent": "META_LANGUAGE_COMMAND", "preferred_language": "en"}
    if any(k in lowered_q for k in lang_commands_hinglish):
        return {"extracted_profile": profile, "query_intent": "META_LANGUAGE_COMMAND", "preferred_language": "hinglish"}

    # 3. General Greetings Check (Multi-lingual)
    greetings = [
        "hi", "hello", "hey", "namaste", "namaskar", "who are you", "who r u", "help", "madad",
        "नमस्ते", "नमस्कार", "प्रणाम", "राम राम", "जय श्री राम", "तुम कौन हो", "आप कौन हैं", "क्या कर सकते हो", "मदद करो"
    ]
    if lowered_q in greetings or (len(query.strip()) <= 15 and any(g in lowered_q for g in ["hi", "hello", "hey", "namaste", "नमस्ते", "नमस्कार", "प्रणाम"])):
        return {"extracted_profile": profile, "query_intent": "GENERAL_GREETING", "preferred_language": resolved_lang}

    # 4. Deterministic Multi-lingual Out-of-Domain & GK Interceptor (English + Hindi + Hinglish)
    off_topic_indicators = [
        # English
        "python", "javascript", "java", "c++", "html", "css", "code", "coding", "program", "function", "algorithm",
        "cricket", "football", "ipl", "messi", "ronaldo", "virat", "dhoni", "match", "score", "tennis",
        "recipe", "cake", "biryani", "pizza", "burger", "cook", "cooking", "food",
        "movie", "actor", "actress", "song", "lyrics", "sing", "dance",
        "weather", "temperature", "capital of", "president of", "prime minister", "pm of", "cm of",
        "chief minister", "who is", "who's", "who was", "whom is", "what is the capital", "where is", "when did",
        "tell me a joke", "joke", "story", "riddle", "narendra modi", "modi", "rahul gandhi", "history of", "calculate", "solve",
        "how does", "what is the speed", "distance between", "meaning of", "tell me about",
        # Hindi & Hinglish
        "कौन है", "कौन हैं", "किसने बनाया", "क्या है", "कहाँ है", "कहा है", "कब हुआ", "कैसे बनता है", "कैसे बनाएं",
        "मौसम कैसा है", "मौसम का हाल", "क्रिकेट", "स्कोर", "मैच", "प्रधानमंत्री कौन", "मुख्यमंत्री कौन", "राष्ट्रपति कौन",
        "राजधानी क्या", "मोदी जी कौन", "राहुल गांधी", "फिल्म", "सिनेमा", "गाना सुनाओ", "चुटकुला सुनाओ", "कहानी सुनाओ",
        "कविता सुनाओ", "कोड लिखो", "गणित हल करो", "ताजमहल", "भारत की राजधानी", "अमेरिका के राष्ट्रपति",
        "kaun hai", "kaun he", "kaha hai", "kahan hai", "weather kaisa hai", "match kiska hai", "score kya hai",
        "modi kaun hai", "pm kaun hai", "cm kaun hai", "joke sunao", "gana sunao", "kahani sunao", "code likho"
    ]
    
    specific_scheme_indicators = [
        "pm kisan", "pm-kisan", "mudra", "ayushman", "pmfby", "fasal bima", "kcc", "kisan credit",
        "surya ghar", "awas", "pmay", "pension", "scholarship", "sukanya", "ladli", "vishwakarma",
        "किसान सम्मान", "आयुष्मान", "मुद्रा लोन", "फसल बीमा", "सूर्य घर", "आवास योजना", "पेंशन योजना", "सुकन्या समृद्धि"
    ]

    is_asking_specific_scheme = any(s in lowered_q for s in specific_scheme_indicators)
    is_off_topic_query = any(o in lowered_q for o in off_topic_indicators)

    if is_off_topic_query and not is_asking_specific_scheme:
        return {"extracted_profile": profile, "query_intent": "OFF_TOPIC", "preferred_language": resolved_lang}

    # 5. Extract Demographic Attributes via NLP & LLM
    nlp_fields = extract_demographics_from_text(query)
    for k, v in nlp_fields.items():
        if v is not None:
            profile[k] = v

    intent_data = await llm_extract_profile(query)
    for key, val in intent_data.items():
        if not key.startswith("_") and val is not None:
            if key not in profile or profile[key] is None:
                profile[key] = val

    # 6. Welfare Domain & Minimum Criteria Gatekeeper
    intent = "SCHEME_QUERY"
    has_min_profile = any([
        profile.get("age") is not None,
        profile.get("annual_income") is not None,
        profile.get("land_size_hectares") is not None,
        profile.get("caste_category") is not None,
        profile.get("gender") is not None,
        profile.get("has_student") is True,
        profile.get("is_farmer") is True,
        profile.get("is_senior") is True,
        profile.get("is_business") is True,
    ])
    in_domain = is_in_welfare_domain(query)

    if not in_domain and not has_min_profile and not is_asking_specific_scheme:
        intent = "OFF_TOPIC"
    elif not has_min_profile and not is_asking_specific_scheme:
        intent = "INSUFFICIENT_INFORMATION"

    logger.info(
        f"[AGENT extract_profile] Intent: {intent} | Language: {resolved_lang} | Profile: {profile}"
    )

    return {
        "extracted_profile": profile,
        "query_intent": intent,
        "preferred_language": resolved_lang,
    }
