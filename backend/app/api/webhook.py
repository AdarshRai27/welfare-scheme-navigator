"""WhatsApp Cloud API Webhook route handler."""

import base64
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import PlainTextResponse

from app.agent.graph import run_agent
from app.core.config import settings
from app.core.session import SessionManager
from app.services.bhashini import BhashiniService
from app.services.ocr import OCRService
from app.services.pdf_filler import FormFillerService
from app.services.whatsapp import WhatsAppService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook")

# Initialize managers and services
whatsapp_service = WhatsAppService(
    token=settings.WHATSAPP_ACCESS_TOKEN,
    phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
)
session_manager = SessionManager(redis_url=settings.REDIS_URL)
bhashini_service = BhashiniService(
    api_key=settings.BHASHINI_API_KEY,
    user_id=settings.BHASHINI_USER_ID,
    pipeline_id=settings.BHASHINI_PIPELINE_ID,
)
ocr_service = OCRService()
form_filler_service = FormFillerService()


@router.get("/whatsapp", response_class=PlainTextResponse)
async def verify_webhook(
    mode: Optional[str] = Query(None, alias="hub.mode"),
    verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    challenge: Optional[str] = Query(None, alias="hub.challenge"),
) -> str:
    """Handles the verification handshake sent by Meta.

    Args:
        mode: Handshake subscribe operation name.
        verify_token: Security token matching configuration.
        challenge: Numeric validation token to echo.

    Returns:
        The hub.challenge string if handshake verifies successfully.
    """
    if mode == "subscribe" and verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook signature verification handshake succeeded.")
        if challenge is not None:
            return challenge
        return ""
    logger.warning("WhatsApp webhook handshake failed due to token mismatch.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/whatsapp")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(
        None, alias="X-Hub-Signature-256"
    ),
) -> Dict[str, str]:
    """Receives and logs incoming events from Meta Cloud API.

    Echoes messages back to verify pipeline communication.

    Args:
        request: FastAPI HTTP Request context.
        x_hub_signature_256: Payload validation signature header.

    Returns:
        Status confirmation dictionary.
    """
    body = await request.body()
    signature = x_hub_signature_256 or ""

    # Verify Meta request signature
    if not whatsapp_service.verify_webhook_signature(body, signature):
        logger.warning("Rejected webhook payload: Invalid X-Hub-Signature-256")
        raise HTTPException(
            status_code=403, detail="Signature validation failed"
        )

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    logger.debug(f"Received WhatsApp webhook body: {data}")

    # Safely parse the nested message elements from Meta JSON layout
    entries = data.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            for message in messages:
                user_phone = message.get("from")
                msg_type = message.get("type")

                if not user_phone:
                    continue

                # Retrieve or initialize the multi-turn session state
                session = await session_manager.get_session(user_phone)
                if not session:
                    session = {
                        "whatsapp_id": user_phone,
                        "preferred_language": "hi",
                        "extracted_profile": {},
                    }

                # Process incoming input types
                query_for_agent = ""
                doc_type = ""

                if msg_type == "text":
                    text_body = message.get("text", {}).get("body", "")
                    logger.info(
                        f"Received text from {user_phone}: {text_body}"
                    )
                    query_for_agent = text_body
                elif msg_type == "audio":
                    audio_id = message.get("audio", {}).get("id", "")
                    logger.info(
                        f"Received audio from {user_phone}: ID {audio_id}"
                    )

                    # 1. Download voice message audio bytes
                    audio_bytes = await whatsapp_service.download_media(audio_id)

                    # 2. Transcribe voice message utilizing Bhashini ASR
                    source_lang = session.get("preferred_language", "hi")
                    transcription = await bhashini_service.speech_to_text(
                        audio_content_base64=audio_bytes.decode(
                            "utf-8", errors="ignore"
                        ),
                        source_language=source_lang,
                    )

                    # 3. Translate transcription using Bhashini NMT
                    english_query = await bhashini_service.translate_text(
                        text=transcription,
                        source_lang=source_lang,
                        target_lang="en",
                    )
                    query_for_agent = english_query
                elif msg_type == "image":
                    image_id = message.get("image", {}).get("id", "")
                    logger.info(
                        f"Received image from {user_phone}: ID {image_id}"
                    )

                    # 1. Download document attachment image bytes
                    image_bytes = await whatsapp_service.download_media(image_id)

                    # 2. Run OCR text extraction via Tesseract/Qwen2-VL
                    ocr_result = await ocr_service.extract_document_data(
                        image_bytes=image_bytes,
                        filename_hint=image_id,
                    )
                    doc_type = ocr_result.get("document_type", "unknown")
                    extracted_fields = ocr_result.get("extracted_fields", {})

                    # 3. Merge newly extracted data into the profile (Option A retention)
                    session["extracted_profile"].update(extracted_fields)
                    query_for_agent = f"Extracted {doc_type} parameters"
                else:
                    logger.info(
                        f"Received unsupported message type '{msg_type}' from {user_phone}"
                    )
                    continue

                # Run LangGraph reasoning workflow agent
                result = await run_agent(
                    user_query=query_for_agent,
                    extracted_profile=session["extracted_profile"],
                    language=session.get("preferred_language", "hi"),
                )

                # Sync extracted fields back to user session profile
                session["extracted_profile"].update(
                    result.get("extracted_profile", {})
                )

                agent_reply = result.get("reply_text", "")

                # If eligible schemes exist, prepare pre-filled form JSON attachments
                eligible = result.get("eligible_schemes", [])
                if eligible:
                    form_links = []
                    for s in eligible:
                        form_meta = form_filler_service.fill_form(
                            s["name"], session["extracted_profile"]
                        )
                        form_links.append(
                            f"📄 Pre-filled Form ({s['name']}): {form_meta['download_url']}"
                        )
                    if form_links:
                        if session.get("preferred_language") == "hi":
                            agent_reply += (
                                "\n\n📥 **आवेदन पत्र (पूर्व-भरे हुए) डाउनलोड करें:**\n"
                                + "\n".join(form_links)
                            )
                        else:
                            agent_reply += (
                                "\n\n📥 **Download Pre-filled Application Forms:**\n"
                                + "\n".join(form_links)
                            )

                # Send back the compiled formatted checklist/response
                await whatsapp_service.send_text_message(
                    to_phone=user_phone,
                    text=agent_reply,
                )

                # Persist updated session state back to store
                await session_manager.save_session(user_phone, session)

    return {"status": "accepted"}


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
    file: Optional[UploadFile] = File(None),
) -> Dict[str, Any]:
    """Processes real-time user text, audio, or document uploads from the Web UI."""
    # 1. Load active session
    session = await session_manager.get_session(phone)
    if not session:
        session = {
            "whatsapp_id": phone,
            "preferred_language": "hi",
            "extracted_profile": {},
        }

    reply_text = ""
    result = {}

    # 2. Process based on message type
    if message_type == "text" and text:
        # Run agent directly on typed text
        result = await run_agent(text, session.get("extracted_profile", {}))
        # Update session
        session["extracted_profile"] = result.get("extracted_profile", {})
        session["eligible_schemes"] = result.get("eligible_schemes", [])
        session["suggested_schemes"] = result.get("suggested_schemes", [])
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
        result = await run_agent(trigger_query, session["extracted_profile"])
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
            english_query, session.setdefault("extracted_profile", {})
        )
        session["extracted_profile"] = result.get("extracted_profile", {})
        session["eligible_schemes"] = result.get("eligible_schemes", [])
        session["suggested_schemes"] = result.get("suggested_schemes", [])
        await session_manager.save_session(phone, session)

        reply_text = (
            f"🎤 **Transcription (Hindi):** {transcription}\n\n"
            f"{result.get('reply_text', '')}"
        )
    # Generate pre-filled forms if eligible schemes exist
    profile = session.get("extracted_profile", {})
    eligible = session.get("eligible_schemes", [])
    for scheme in eligible:
        scheme_name = scheme.get("name")
        if scheme_name == "PM-Kisan Samman Nidhi":
            form_filler_service.fill_form("PM-Kisan Samman Nidhi", profile)
        elif scheme_name == "UP Senior Pension Scheme":
            form_filler_service.fill_form("UP Senior Pension Scheme", profile)

    return {
        "status": "success",
        "reply_text": reply_text,
        "session": session,
    }



