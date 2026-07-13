"""WhatsApp Cloud API mock service helper."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Mock service to handle WhatsApp Cloud API interactions."""

    def __init__(self, token: str, phone_number_id: str) -> None:
        """Initialize mock WhatsApp client settings.

        Args:
            token: Meta API access token.
            phone_number_id: Meta platform phone ID.
        """
        self.token: str = token
        self.phone_number_id: str = phone_number_id

    async def send_text_message(self, to_phone: str, text: str) -> Dict[str, Any]:
        """Mock sending a plain text message to a user.

        Args:
            to_phone: Recipient phone number.
            text: Text content of the message.

        Returns:
            Mock API response dictionary.
        """
        logger.info(f"[MOCK WHATSAPP] Outbox -> to={to_phone} | text={text}")
        return {
            "messaging_product": "whatsapp",
            "contacts": [{"input": to_phone, "wa_id": to_phone}],
            "messages": [{"id": f"mock_wamid_txt_{to_phone}"}],
        }

    async def send_audio_message(
        self, to_phone: str, audio_url_or_id: str
    ) -> Dict[str, Any]:
        """Mock sending an audio message to a user.

        Args:
            to_phone: Recipient phone number.
            audio_url_or_id: Media URL or media ID.

        Returns:
            Mock API response dictionary.
        """
        logger.info(
            f"[MOCK WHATSAPP] Outbox -> to={to_phone} | audio_id={audio_url_or_id}"
        )
        return {
            "messaging_product": "whatsapp",
            "contacts": [{"input": to_phone, "wa_id": to_phone}],
            "messages": [{"id": f"mock_wamid_aud_{to_phone}"}],
        }

    def verify_webhook_signature(
        self, payload_bytes: bytes, signature_header: str
    ) -> bool:
        """Mock signature verification. Always returns True in development/test.

        Args:
            payload_bytes: Raw HTTP request body.
            signature_header: Meta's X-Hub-Signature-256 header.

        Returns:
            Boolean validation result.
        """
        logger.debug(
            f"Verifying webhook signature: header={signature_header} (MOCK: always True)"
        )
        return True

    async def download_media(self, media_id: str) -> bytes:
        """Mock media download from Meta Cloud API.

        Args:
            media_id: Meta platform media node identifier.

        Returns:
            Raw binary bytes of the media file.
        """
        logger.info(f"[MOCK WHATSAPP] Downloading media content: id={media_id}")
        if "audio" in media_id.lower():
            return b"MOCK_AUDIO_BYTES_BASE64_FORMAT_DATA"
        return b"MOCK_IMAGE_BYTES_PNG_FORMAT_DATA"

