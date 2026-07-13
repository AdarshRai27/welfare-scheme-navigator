"""WhatsApp Cloud API Webhook route handler."""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.core.session import SessionManager
from app.services.bhashini import BhashiniService
from app.services.ocr import OCRService
from app.services.whatsapp import WhatsAppService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook")

# Initialize WhatsApp, Bhashini, OCR, and Session managers using global settings
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

                if msg_type == "text":
                    text_body = message.get("text", {}).get("body", "")
                    logger.info(
                        f"Received text from {user_phone}: {text_body}"
                    )
                    await whatsapp_service.send_text_message(
                        to_phone=user_phone,
                        text=f"Mock Echo: {text_body}",
                    )
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

                    await whatsapp_service.send_text_message(
                        to_phone=user_phone,
                        text=f"Mock Echo: Transcribed voice note to: '{transcription}' (English: '{english_query}')",
                    )
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

                    await whatsapp_service.send_text_message(
                        to_phone=user_phone,
                        text=f"Mock Echo: Extracted {doc_type} fields: {extracted_fields}",
                    )
                else:
                    logger.info(
                        f"Received unsupported message type '{msg_type}' from {user_phone}"
                    )

                # Persist updated session state back to store
                await session_manager.save_session(user_phone, session)

    return {"status": "accepted"}
