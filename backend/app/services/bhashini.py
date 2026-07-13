"""Bhashini AI mock service helper."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BhashiniService:
    """Mock service to handle Bhashini ASR, TTS, and translation pipeline."""

    def __init__(
        self, api_key: str, user_id: str, pipeline_id: str
    ) -> None:
        """Initialize mock Bhashini client parameters.

        Args:
            api_key: User's Bhashini API key.
            user_id: User's Bhashini account ID.
            pipeline_id: Configured pipeline layout identifier.
        """
        self.api_key: str = api_key
        self.user_id: str = user_id
        self.pipeline_id: str = pipeline_id

    async def speech_to_text(
        self, audio_content_base64: str, source_language: str
    ) -> str:
        """Mock transcribing audio bytes to text.

        Args:
            audio_content_base64: Base64-encoded audio bytes.
            source_language: Language code of input audio (e.g., 'hi', 'ta').

        Returns:
            Mocked transcription string.
        """
        logger.info(
            f"[MOCK BHASHINI ASR] Transcribing audio content of length {len(audio_content_base64)} in language: {source_language}"
        )
        return "मुझे पीएम किसान योजना के बारे में जानकारी चाहिए"  # Mock Hindi speech input

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        """Mock translation of text.

        Args:
            text: Text to translate.
            source_lang: Language code of origin.
            target_lang: Language code of destination.

        Returns:
            Mock translated text.
        """
        logger.info(
            f"[MOCK BHASHINI NMT] Translating text '{text}' from {source_lang} -> {target_lang}"
        )
        # For simplicity, if targeting English, return a mock translation
        if target_lang == "en" and source_lang == "hi":
            return "I want information about the PM Kisan scheme"
        return text

    async def text_to_speech(self, text: str, language: str) -> str:
        """Mock synthesizing speech from text.

        Args:
            text: Content to synthesize.
            language: Target language of audio synthesis.

        Returns:
            A mock URL to the synthesized audio file.
        """
        logger.info(
            f"[MOCK BHASHINI TTS] Synthesizing speech for: '{text}' in language: {language}"
        )
        return f"http://mock-bhashini-tts.local/synthesized_speech_{language}.mp3"
