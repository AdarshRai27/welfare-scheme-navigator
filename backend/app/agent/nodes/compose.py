"""Graph node generating the final formatted user response text."""

import logging
from typing import Any, Dict

from app.services.llm import llm_compose_response

logger = logging.getLogger(__name__)


async def compose_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Composes final checklist response formatted in user's language with strict guardrails.

    Args:
        state: Shared graph state dictionary.

    Returns:
        State updates containing composed reply_text.
    """
    profile = state.get("extracted_profile", {})
    eligible = state.get("eligible_schemes", [])
    suggested = state.get("suggested_schemes", [])
    query = state.get("user_query", "")
    intent = state.get("query_intent", "SCHEME_QUERY")
    language = state.get("preferred_language", "hi")

    # Guardrail 1: Off-Topic Non-Welfare Query Refusal
    if intent == "OFF_TOPIC":
        if language == "hi":
            reply = "क्षमा करें! मैं केवल भारत सरकार और राज्य सरकारों की कल्याणकारी योजनाओं (जैसे पेंशन, किसान लाभ, बिजनेस लोन, छात्रवृत्ति, स्वास्थ्य बीमा) से संबंधित प्रश्नों के उत्तर देने के लिए तैयार किया गया हूँ। कृपया सरकारी योजनाओं से संबंधित प्रश्न पूछें।"
        elif language == "hinglish":
            reply = "Kshama karein! Main sirf Indian government welfare schemes (jaise pension, kisan labh, business loan, scholarship, health insurance) se related questions ke answers dene ke liye designed hoon. Kripya government schemes se related question poochein."
        else:
            reply = "I apologize, but I am specifically designed to assist exclusively with Indian government welfare schemes, benefits, and eligibility criteria (such as pensions, farmer subsidies, business loans, health insurance, and scholarships). Please ask a question related to government schemes."
        return {"reply_text": reply}

    # Guardrail 2: Insufficient Information / Missing Minimum Requirements
    if intent == "INSUFFICIENT_INFORMATION":
        if language == "hi":
            reply = (
                "क्षमा करें! आपके प्रश्न में आवश्यक विवरण उपलब्ध न होने के कारण मैं आपकी पात्रता की जांच नहीं कर पा रहा हूँ।\n\n"
                "आपके लिए उपयुक्त सरकारी योजनाएं खोजने हेतु कृपया निम्नलिखित जानकारी प्रदान करें:\n"
                "• **आपकी आयु (उम्र) या जन्म वर्ष**\n"
                "• **आपका राज्य / निवास स्थान**\n"
                "• **आपकी श्रेणी / पेशा** (उदा: किसान, छात्र, वरिष्ठ नागरिक, महिला या छोटा व्यापारी)\n"
                "• **वार्षिक पारिवारिक आय** (उदा: ₹1.5 लाख)\n"
                "• **भूमि का रकबा** (एकड़ या हेक्टेयर में, यदि आप किसान हैं)\n\n"
                "अथवा आप अपने आधार कार्ड, आय प्रमाण पत्र या खतौनी की फ़ोटो अपलोड कर सकते हैं।"
            )
        elif language == "hinglish":
            reply = (
                "Kshama karein! Aapke question me zaroori details na hone ke karan main aapki eligibility check nahi kar pa raha hoon.\n\n"
                "Sahi schemes dhoondhne ke liye kripya ye information provide karein:\n"
                "• **Aapki Age ya Birth Year**\n"
                "• **State / Domicile**\n"
                "• **Category / Occupation** (jaise Farmer, Student, Senior Citizen, Women ya Small Business)\n"
                "• **Annual Family Income** (e.g. ₹1.5 Lakh)\n"
                "• **Land Size** (Acres ya Hectares me, agar aap kisan hain)\n\n"
                "Ya phir aap apna Aadhaar card ya Income certificate scan karein."
            )
        else:
            reply = (
                "I apologize, but I am unable to determine your eligibility yet as your query lacks the necessary citizen details.\n\n"
                "To help you find the right government welfare schemes, please provide:\n"
                "• **Your Age or Date of Birth**\n"
                "• **State of Residence / Domicile**\n"
                "• **Category / Occupation** (e.g., Farmer, Student, Senior Citizen, Small Business, or Woman)\n"
                "• **Annual Family Income** (e.g. ₹1.5 Lakh)\n"
                "• **Landholding Size** (in Acres or Hectares, if a farmer)\n\n"
                "Alternatively, you can upload a photo of your Aadhaar Card, Income Certificate, or Land Record."
            )
        return {"reply_text": reply}

    # Guardrail 3: No Scheme Eligibility in Database
    if not eligible and not suggested and intent == "SCHEME_QUERY":
        if language == "hi":
            reply = "वर्तमान में आप हमारे डेटाबेस की किसी योजना के लिए पात्र नहीं हैं, लेकिन हम लगातार नई योजनाएं जोड़ रहे हैं। कृपया जल्द ही पुनः संपर्क करें!"
        elif language == "hinglish":
            reply = "Aap hamare current database ki kisi scheme ke liye eligible nahi hain, lekin hum actively new schemes add kar rahe hain. Kripya jald hi dubara visit karein!"
        else:
            reply = "You are not eligible for any schemes in our current database, but we are expanding our database as we speak. Please visit again soon!"
        return {"reply_text": reply}

    # Guardrail 4: Meta Language Command Response
    if intent == "META_LANGUAGE_COMMAND":
        if language == "hi":
            return {"reply_text": "नमस्ते! मैंने उत्तर देने की भाषा बदलकर हिंदी कर दी है। आप किस सरकारी योजना या सहायता के बारे में जानना चाहते हैं?"}
        elif language == "hinglish":
            return {"reply_text": "Namaste! Maine response language badalkar Hinglish kar di hai. Aap kis sarkari yojana ke baare me janna chahte hain?"}
        else:
            return {"reply_text": "Hello! I have updated my response language to English. What government welfare scheme or benefit are you looking for today?"}

    # Guardrail 5: General Greeting Response
    if intent == "GENERAL_GREETING":
        if language == "hi":
            return {"reply_text": "नमस्ते! मैं आपका सरकारी सहायक हूँ। 🙏\n\n• मैं आपको 125+ से अधिक केंद्रीय और राज्य सरकार की कल्याणकारी योजनाओं (जैसे पीएम-किसान, मुद्रा लोन, वृद्धावस्था पेंशन, आयुष्मान भारत, छात्रवृत्ति) की पात्रता जांचने और आवेदन करने में सहायता कर सकता हूँ।\n• आप अपना प्रश्न पूछें (जैसे: 'मुझे दुकान के लिए लोन चाहिए' या 'किसान योजनाएं'), या अपने दस्तावेज की फोटो स्कैन करें।"}
        elif language == "hinglish":
            return {"reply_text": "Namaste! Main aapka Sarkari Sahayak hoon. 🙏\n\n• Main aapko 125+ Central aur State government welfare schemes (jaise PM-Kisan, Mudra Loan, Senior Pension, Ayushman Bharat, Scholarship) me eligibility check karne aur apply karne me help kar sakta hoon.\n• Aap apna question poochein ya Didit ID scan karein."}
        else:
            return {"reply_text": "Hello! I am Sarkari Sahayak, your AI counselor for Indian government welfare schemes. 🙏\n\n• I can help you discover and check eligibility for over 125 central and state welfare schemes (such as PM-Kisan, Mudra Loans, Senior Pension, Ayushman Bharat, and Student Scholarships).\n• How can I assist you today?"}

    # Generate response via LLM / template composition
    reply_text = await llm_compose_response(
        profile=profile,
        eligible=eligible,
        suggested=suggested,
        query=query,
        intent=intent,
        language=language,
    )

    logger.info("[AGENT compose_response] Composed markdown message.")
    return {"reply_text": reply_text}
