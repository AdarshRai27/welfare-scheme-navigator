"""Web-native Civic AI and Didit Verification Webhook route handler."""

import base64
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import PlainTextResponse

from app.agent.graph import run_agent
from app.core.config import settings
from app.core.session import SessionManager
from app.services.bhashini import BhashiniService
from app.services.ocr import OCRService
from app.services.didit import DiditService
from app.services.pdf_filler import FormFillerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook")

# Initialize managers and services
session_manager = SessionManager(redis_url=settings.REDIS_URL)
bhashini_service = BhashiniService(
    api_key=settings.BHASHINI_API_KEY,
    user_id=settings.BHASHINI_USER_ID,
    pipeline_id=settings.BHASHINI_PIPELINE_ID,
)
ocr_service = OCRService()
didit_service = DiditService()
form_filler_service = FormFillerService()


@router.post("/diagnostics/seed")
async def seed_diagnostics_schemes() -> Dict[str, str]:
    """Seeds the in-memory/fallback database store with default test schemes."""
    from app.db.vector_store import VectorStore

    store = VectorStore()
    # Reset existing records first
    store._in_memory_schemes.clear()

    # Seed agricultural scheme
    await store.add_scheme(
        {
            "name": "PM-Kisan Samman Nidhi",
            "issuing_body": "Central",
            "category": "Agriculture",
            "description": "Financial support for landowning farmers across India",
            "eligibility_rules": {
                "land_size_limit": 2.0,
            },
            "source_url": "https://pmkisan.gov.in",
        }
    )

    # Seed state pension scheme
    await store.add_scheme(
        {
            "name": "UP Senior Pension Scheme",
            "issuing_body": "State",
            "state": "Uttar Pradesh",
            "category": "Pension",
            "description": "Old age pension support for citizens in UP",
            "eligibility_rules": {
                "min_age": 60,
                "income_limit": 46080,
            },
        }
    )

    logger.info("[DIAGNOSTICS] Seeded mock schemes successfully.")
    return {"status": "seeded"}


@router.get("/diagnostics/session/{phone}")
async def get_session_diagnostics(phone: str) -> Dict[str, Any]:
    """Diagnostic endpoint to retrieve current session details."""
    state = await session_manager.get_session(phone)
    return state or {}


@router.delete("/diagnostics/session/{phone}")
async def delete_session_diagnostics(phone: str) -> Dict[str, str]:
    """Diagnostic endpoint to clear user session state."""
    await session_manager.clear_session(phone)
    return {"status": "cleared"}


@router.post("/web/message")
async def handle_web_message(
    phone: str = Form(...),
    message_type: str = Form(...),  # "text", "audio", "aadhaar", "income"
    text: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
) -> Dict[str, Any]:
    """Processes real-time user text, audio, or document uploads from the Web UI."""
    # 1. Load active session
    session = await session_manager.get_session(phone)
    if not session:
        session = {
            "whatsapp_id": phone,
            "preferred_language": language or "en",
            "extracted_profile": {},
        }
    elif language:
        session["preferred_language"] = language

    active_lang = language or session.get("preferred_language", "en")
    reply_text = ""
    result = {}

    # 2. Process based on message type
    if message_type == "text" and text:
        # Run agent directly on typed text with explicit language context
        result = await run_agent(text, session.get("extracted_profile", {}), language=active_lang)
        # Update session
        session["extracted_profile"] = result.get("extracted_profile", {})
        session["eligible_schemes"] = result.get("eligible_schemes", [])
        session["suggested_schemes"] = result.get("suggested_schemes", [])
        session["preferred_language"] = result.get("preferred_language", active_lang)
        await session_manager.save_session(phone, session)
        reply_text = result.get("reply_text", "")

    elif message_type in ("aadhaar", "income") and file:
        file_bytes = await file.read()
        # Trigger local OCR directly on uploaded file bytes
        ocr_result = await ocr_service.extract_document_data(
            file_bytes, filename_hint=message_type
        )
        extracted_fields = ocr_result.get("extracted_fields", {})
        session.setdefault("extracted_profile", {}).update(extracted_fields)
        await session_manager.save_session(phone, session)

        # Run agent on updated profile
        trigger_query = f"Extracted {message_type} parameters"
        result = await run_agent(trigger_query, session["extracted_profile"], language=active_lang)
        session["eligible_schemes"] = result.get("eligible_schemes", [])
        session["suggested_schemes"] = result.get("suggested_schemes", [])
        await session_manager.save_session(phone, session)
        reply_text = result.get("reply_text", "")

    elif message_type == "audio" and file:
        file_bytes = await file.read()
        base64_audio = base64.b64encode(file_bytes).decode("utf-8")
        # Run speech-to-text
        transcription = await bhashini_service.speech_to_text(base64_audio, "hi")
        # Run translation
        english_query = await bhashini_service.translate_text(
            transcription, "hi", "en"
        )

        # Run agent
        result = await run_agent(
            english_query, session.setdefault("extracted_profile", {}), language=active_lang
        )
        session["extracted_profile"] = result.get("extracted_profile", {})
        session["eligible_schemes"] = result.get("eligible_schemes", [])
        session["suggested_schemes"] = result.get("suggested_schemes", [])
        await session_manager.save_session(phone, session)

        reply_text = (
            f"🎤 **Transcription:** {transcription}\n\n"
            f"{result.get('reply_text', '')}"
        )

    # Generate pre-filled forms if eligible schemes exist
    profile = session.get("extracted_profile", {})
    eligible = session.get("eligible_schemes", [])
    for scheme in eligible:
        scheme_name = scheme.get("name")
        if scheme_name and "PM-Kisan" in scheme_name:
            form_filler_service.fill_form("PM-Kisan Samman Nidhi", profile)
        elif scheme_name and "Pension" in scheme_name:
            form_filler_service.fill_form("UP Senior Pension Scheme", profile)

    return {
        "status": "success",
        "reply_text": reply_text,
        "session": session,
    }


@router.post("/ocr/scan")
@router.post("/didit/scan")
async def handle_ocr_scan(
    phone: str = Form("919999999999"),
    language: Optional[str] = Form(None),
    document_type: str = Form("auto"),
    file: Optional[UploadFile] = File(None),
) -> Dict[str, Any]:
    """Processes conventional document OCR for Aadhaar Cards, Income Certificates, and Land Records."""
    session = await session_manager.get_session(phone)
    if not session:
        session = {"whatsapp_id": phone, "preferred_language": language or "en", "extracted_profile": {}}
    elif language:
        session["preferred_language"] = language

    active_lang = language or session.get("preferred_language", "en")

    file_bytes = b"MOCK_DOCUMENT_BYTES"
    filename_hint = "aadhaar"
    if file:
        file_bytes = await file.read()
        filename_hint = file.filename or "aadhaar"

    # Run Conventional Document OCR Scan
    ocr_res = await ocr_service.extract_document_data(file_bytes, filename_hint, document_type)
    extracted_fields = ocr_res.get("extracted_fields", {})
    doc_type = ocr_res.get("document_type", "document")

    # Check if OCR extracted meaningful fields
    valid_fields = {k: v for k, v in extracted_fields.items() if v and v != "Not Extracted"}
    if not valid_fields:
        err_msg = (
            "⚠️ **दस्तावेज़ पढ़ने में असमर्थ:**\nआपके दस्तावेज़ की फोटो से विवरण स्पष्ट रूप से नहीं पढ़े जा सके। कृपया सुनिश्चित करें कि फोटो साफ़, धुंधली रहित और अच्छी रोशनी में ली गई हो, फिर पुनः प्रयास करें।"
            if active_lang == "hi"
            else "⚠️ **Document Scan Unreadable:**\nCould not clearly read details from your document photo. Please ensure the photo is well-lit, sharp, and not blurry, then try again."
        )
        return {
            "status": "unreadable",
            "provider": "conventional_ocr",
            "reply_text": err_msg,
            "session": session,
        }

    # Merge into Redis user profile session
    session.setdefault("extracted_profile", {}).update(valid_fields)
    await session_manager.save_session(phone, session)

    # Build clear verified document badge
    v_name = session["extracted_profile"].get("name", "Citizen")
    v_aadhaar = session["extracted_profile"].get("aadhaar_number")
    v_income = session["extracted_profile"].get("annual_income")
    v_land = session["extracted_profile"].get("land_size_hectares")
    v_state = session["extracted_profile"].get("state", "India")
    v_age = session["extracted_profile"].get("age")
    v_gender = session["extracted_profile"].get("gender")

    if doc_type == "income_certificate" or (v_income and "income" in filename_hint.lower()):
        badge_header = {
            "hi": f"📄 **आय प्रमाण पत्र सत्यापन:**\n• **नाम**: {v_name}\n• **सत्यापित वार्षिक आय**: ₹{v_income:,}\n• **राज्य**: {v_state}\n\n",
            "hinglish": f"📄 **Income Certificate Verified:**\n• **Name**: {v_name}\n• **Annual Income**: ₹{v_income:,}\n• **State**: {v_state}\n\n",
            "en": f"📄 **Income Certificate Verified:**\n• **Name**: {v_name}\n• **Annual Income**: ₹{v_income:,}\n• **State**: {v_state}\n\n",
        }.get(active_lang, f"📄 **Income Certificate Verified:**\n• **Name**: {v_name}\n• **Annual Income**: ₹{v_income:,}\n• **State**: {v_state}\n\n")
    elif doc_type == "land_record" or (v_land and ("land" in filename_hint.lower() or "khatauni" in filename_hint.lower())):
        badge_header = {
            "hi": f"🌾 **भू-अभिलेख (खतौनी) सत्यापन:**\n• **खातेदार का नाम**: {v_name}\n• **सत्यापित भूमि**: {v_land} हेक्टेयर\n• **राज्य**: {v_state}\n\n",
            "hinglish": f"🌾 **Land Record (Khatauni) Verified:**\n• **Owner Name**: {v_name}\n• **Landholding**: {v_land} Hectares\n• **State**: {v_state}\n\n",
            "en": f"🌾 **Land Record (Khatauni) Verified:**\n• **Owner Name**: {v_name}\n• **Landholding**: {v_land} Hectares\n• **State**: {v_state}\n\n",
        }.get(active_lang, f"🌾 **Land Record (Khatauni) Verified:**\n• **Owner Name**: {v_name}\n• **Landholding**: {v_land} Hectares\n• **State**: {v_state}\n\n")
    else:
        badge_header = {
            "hi": f"🪪 **पहचान पत्र (आधार) सत्यापन:**\n• **नाम**: {v_name}\n• **पहचान संख्या**: `{v_aadhaar or 'XXXX-XXXX-8921'}`\n• **राज्य**: {v_state}" + (f"\n• **आयु**: {v_age} वर्ष" if v_age else "") + "\n\n",
            "hinglish": f"🪪 **Identity Document Verified:**\n• **Name**: {v_name}\n• **ID Number**: `{v_aadhaar or 'XXXX-XXXX-8921'}`\n• **State**: {v_state}" + (f"\n• **Age**: {v_age} years" if v_age else "") + "\n\n",
            "en": f"🪪 **Identity Document Verified:**\n• **Name**: {v_name}\n• **ID Number**: `{v_aadhaar or 'XXXX-XXXX-8921'}`\n• **State**: {v_state}" + (f"\n• **Age**: {v_age} years old" if v_age else "") + "\n\n",
        }.get(active_lang, f"🪪 **Identity Document Verified:**\n• **Name**: {v_name}\n• **ID Number**: `{v_aadhaar or 'XXXX-XXXX-8921'}`\n• **State**: {v_state}\n\n")

    # Run LangGraph reasoning workflow with updated citizen profile
    age_clause = f", age {v_age}" if v_age else ""
    gender_clause = f", {v_gender}" if v_gender else ""
    semantic_query = (
        f"I am {v_name}{age_clause}{gender_clause} from {v_state}. "
        f"What government welfare schemes can I apply for with my verified profile?"
    )

    result = await run_agent(semantic_query, session["extracted_profile"], language=active_lang)

    session["eligible_schemes"] = result.get("eligible_schemes", [])
    session["suggested_schemes"] = result.get("suggested_schemes", [])
    await session_manager.save_session(phone, session)

    return {
        "status": "success",
        "provider": "conventional_ocr",
        "document_type": doc_type,
        "reply_text": f"{badge_header}{result.get('reply_text', '')}",
        "session": session,
    }


@router.post("/didit/oauth/session")
async def handle_didit_oauth_session(
    phone: str = Form("919999999999"),
) -> Dict[str, Any]:
    """Generates 1-click Didit OAuth2 verification session URL (Image-free flow)."""
    callback_url = f"https://welfare-scheme-navigator.onrender.com/webhook/didit/oauth/callback?phone={phone}"
    session_info = await didit_service.create_oauth_session(phone, callback_url)
    return {
        "status": "success",
        "flow": "oauth2_image_free",
        "session_url": session_info.get("url"),
        "session_id": session_info.get("session_id"),
    }


@router.get("/didit/oauth/mock_verify")
async def handle_didit_mock_oauth_verify(
    phone: str = Query("919999999999"),
    language: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Mock 1-click Didit OAuth token callback that updates Redis profile without images."""
    session = await session_manager.get_session(phone)
    if not session:
        session = {"whatsapp_id": phone, "preferred_language": language or "en", "extracted_profile": {}}
    elif language:
        session["preferred_language"] = language

    active_lang = language or session.get("preferred_language", "en")

    claims = await didit_service.verify_oauth_claims(f"didit_token_{phone}", session.get("extracted_profile"))
    session.setdefault("extracted_profile", {}).update(claims)
    await session_manager.save_session(phone, session)

    # Run agent on verified profile with embedded JSON claims
    trigger_query = f"Extracted didit_oauth parameters: {json.dumps(claims)}"
    result = await run_agent(trigger_query, session["extracted_profile"], language=active_lang)
    session["eligible_schemes"] = result.get("eligible_schemes", [])
    session["suggested_schemes"] = result.get("suggested_schemes", [])
    await session_manager.save_session(phone, session)

    badge_title = {
        "hi": "⚡ **1-क्लिक डिडिट सत्यापित पहचान:**",
        "hinglish": "⚡ **1-Click Didit Verified Profile:**",
        "en": "⚡ **1-Click Didit Verified Identity:**"
    }.get(active_lang, "⚡ **1-Click Didit Verified Identity:**")

    return {
        "status": "success",
        "flow": "didit_oauth2_verified",
        "reply_text": f"{badge_title}\n\n{result.get('reply_text', '')}",
        "session": session,
    }



