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

    # 5. Extract Caste Category
    if "sc" in lowered or "scheduled caste" in lowered:
        res["caste_category"] = "SC"
    elif "st" in lowered or "scheduled tribe" in lowered:
        res["caste_category"] = "ST"
    elif "obc" in lowered or "other backward" in lowered:
        res["caste_category"] = "OBC"
    elif "general" in lowered or "gen" in lowered:
        res["caste_category"] = "General"

    # 6. Extract Gender
    if any(g in lowered for g in ["female", "woman", "women", "mahila", "aurat", "lady", "girl"]):
        res["gender"] = "Female"
    elif any(g in lowered for g in ["male", "man", "purush", "boy"]):
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

    # 2. Classify Intent, Language, and additional parameters via LLM
    intent_data = await llm_extract_profile(query)
    
    intent = intent_data.get("_intent", "SCHEME_QUERY")
    detected_lang = intent_data.get("_language")
    
    # Accurate language resolution
    is_hindi_script = any(2304 <= ord(c) <= 2431 for c in query)
    words = query.lower().split()
    hinglish_keywords = {"chahiye", "yojana", "mera", "meri", "karna", "krna", "liya", "liye", "kaise", "batao", "bataiye", "ko", "dukan", "kisan", "kheti", "me", "mein", "bolo", "hai", "shuru", "milega", "padhai"}
    is_hinglish_text = any(w in hinglish_keywords for w in words)
    
    if is_hindi_script:
        resolved_lang = "hi"
    elif is_hinglish_text:
        resolved_lang = "hinglish"
    elif detected_lang in ("en", "hi", "hinglish"):
        resolved_lang = detected_lang
    else:
        resolved_lang = current_lang

    # Merge LLM fields if they are not None and not already extracted with high precision
    for key, val in intent_data.items():
        if not key.startswith("_") and val is not None:
            if key not in profile or profile[key] is None:
                profile[key] = val

    logger.info(
        f"[AGENT extract_profile] Intent: {intent} | Language: {resolved_lang} | Profile: {profile}"
    )

    return {
        "extracted_profile": profile,
        "query_intent": intent,
        "preferred_language": resolved_lang,
    }
