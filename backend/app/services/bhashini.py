"""Service handling audio speech-to-text, text-to-speech, and translation using Groq and local gTTS."""

import base64
import logging
import os
import tempfile
import uuid
from typing import Any, Dict

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class BhashiniService:
    """Service to handle speech-to-text (ASR), translation (NMT), and text-to-speech (TTS) pipelines."""

    def __init__(
        self, api_key: str, user_id: str, pipeline_id: str
    ) -> None:
        """Initialize service parameters.

        Args:
            api_key: User's API key.
            user_id: User's account ID.
            pipeline_id: Configured pipeline layout identifier.
        """
        self.api_key: str = api_key
        self.user_id: str = user_id
        self.pipeline_id: str = pipeline_id

    async def speech_to_text(
        self, audio_content_base64: str, source_language: str
    ) -> str:
        """Transcribe base64 audio bytes to text using Groq Whisper.

        Args:
            audio_content_base64: Base64-encoded audio bytes.
            source_language: Language code of input audio (e.g., 'hi', 'ta').

        Returns:
            Transcription string.
        """
        # 1. First attempt real Groq Whisper transcription if key is present
        if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("mock"):
            logger.info(
                f"[GROQ WHISPER] Transcribing audio with Whisper ASR in language: {source_language}"
            )
            try:
                audio_bytes = base64.b64decode(audio_content_base64)

                # Write to a temporary file for the multipart client upload
                with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_file_path = tmp_file.name

                url = "https://api.groq.com/openai/v1/audio/transcriptions"
                headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}

                # Setup files and model parameters
                with open(tmp_file_path, "rb") as f:
                    files = {"file": (os.path.basename(tmp_file_path), f, "audio/ogg")}
                    data = {
                        "model": "whisper-large-v3",
                        "language": source_language,
                    }
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        res = await client.post(url, headers=headers, files=files, data=data)

                # Clean up temporary file
                try:
                    os.unlink(tmp_file_path)
                except Exception:
                    pass

                if res.status_code == 200:
                    result = res.json()
                    transcription = result.get("text", "")
                    logger.info(f"[GROQ WHISPER] Transcription successful: '{transcription}'")
                    return transcription
                else:
                    logger.error(
                        f"[GROQ WHISPER] API returned error (status {res.status_code}): {res.text}"
                    )
            except Exception as err:
                logger.error(f"[GROQ WHISPER] Connection error during transcription: {err}")

        # 2. Mock Fallback
        logger.info(
            f"[MOCK ASR] Transcribing audio content of length {len(audio_content_base64)} in language: {source_language}"
        )
        return "मुझे पीएम किसान योजना के बारे में जानकारी चाहिए"

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        """Translate text using Groq LLM.

        Args:
            text: Text to translate.
            source_lang: Language code of origin.
            target_lang: Language code of destination.

        Returns:
            Translated text.
        """
        from app.services.llm import run_llm_completion

        if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("mock"):
            logger.info(f"[GROQ TRANSLATE] Translating '{text}' from {source_lang} -> {target_lang}")
            system_msg = (
                f"You are a translation assistant. Translate the following text from language code "
                f"'{source_lang}' to language code '{target_lang}'. Output ONLY the translated text, "
                "do not include extra context or explanations."
            )
            translation = await run_llm_completion(prompt=text, system_message=system_msg)
            if translation:
                logger.info(f"[GROQ TRANSLATE] Translation successful: '{translation}'")
                return translation.strip()

        # Fallback to Mock
        if target_lang == "en" and source_lang == "hi":
            return "I want information about the PM Kisan scheme"
        return text

    async def text_to_speech(self, text: str, language: str) -> str:
        """Synthesize text to speech using gTTS.

        Args:
            text: Content to synthesize.
            language: Target language of audio synthesis.

        Returns:
            A public URL path to the synthesized audio file.
        """
        logger.info(f"[gTTS] Synthesizing speech for: '{text}' in language: {language}")
        try:
            from gtts import gTTS

            # Ensure the static audio assets directory exists
            static_audio_dir = os.path.join("backend", "static", "audio")
            if not os.path.exists(static_audio_dir):
                os.makedirs(static_audio_dir, exist_ok=True)

            audio_filename = f"speech_{uuid.uuid4().hex}.mp3"
            output_path = os.path.join(static_audio_dir, audio_filename)

            # Map language codes to gTTS tags (hi -> hi, en -> en)
            tts = gTTS(text=text, lang=language)
            # Execute save in a threadpool to keep it non-blocking
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, tts.save, output_path)

            logger.info(f"[gTTS] Generated speech file at: {output_path}")
            return f"/static/audio/{audio_filename}"
        except Exception as err:
            logger.error(f"[gTTS] Failed to generate speech: {err}")

        # Fallback
        return f"http://mock-bhashini-tts.local/synthesized_speech_{language}.mp3"
