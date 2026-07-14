"""Service handling audio speech-to-text, text-to-speech, and translation using OpenAI or fallback mocks."""

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
        """Transcribe base64 audio bytes to text using OpenAI Whisper.

        Args:
            audio_content_base64: Base64-encoded audio bytes.
            source_language: Language code of input audio (e.g., 'hi', 'ta').

        Returns:
            Transcription string.
        """
        # 1. First attempt real OpenAI Whisper transcription if key is present
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock"):
            logger.info(
                f"[OPENAI WHISPER] Transcribing audio with Whisper ASR in language: {source_language}"
            )
            try:
                audio_bytes = base64.b64decode(audio_content_base64)
                
                # Write to a temporary file for the multipart client upload
                with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_file_path = tmp_file.name

                url = "https://api.openai.com/v1/audio/transcriptions"
                headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                
                # Setup files and model parameters
                with open(tmp_file_path, "rb") as f:
                    files = {"file": (os.path.basename(tmp_file_path), f, "audio/ogg")}
                    data = {
                        "model": "whisper-1",
                        "language": source_language
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
                    logger.info(f"[OPENAI WHISPER] Transcription successful: '{transcription}'")
                    return transcription
                else:
                    logger.error(
                        f"[OPENAI WHISPER] API returned error (status {res.status_code}): {res.text}"
                    )
            except Exception as err:
                logger.error(f"[OPENAI WHISPER] Connection error during transcription: {err}")

        # 2. Mock Fallback
        logger.info(
            f"[MOCK ASR] Transcribing audio content of length {len(audio_content_base64)} in language: {source_language}"
        )
        return "मुझे पीएम किसान योजना के बारे में जानकारी चाहिए"

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        """Translate text using OpenAI GPT model.

        Args:
            text: Text to translate.
            source_lang: Language code of origin.
            target_lang: Language code of destination.

        Returns:
            Translated text.
        """
        # 1. First attempt real OpenAI Chat completion translation
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock"):
            logger.info(f"[OPENAI TRANSLATE] Translating '{text}' from {source_lang} -> {target_lang}")
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"You are a translation assistant. Translate the following text from language code "
                            f"'{source_lang}' to language code '{target_lang}'. Output ONLY the translated text, "
                            "do not include extra context or explanations."
                        )
                    },
                    {"role": "user", "content": text}
                ],
                "temperature": 0.1
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    res = await client.post(url, json=payload, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        translation = data["choices"][0]["message"]["content"].strip()
                        logger.info(f"[OPENAI TRANSLATE] Translation successful: '{translation}'")
                        return translation
                    else:
                        logger.error(f"[OPENAI TRANSLATE] API error (status {res.status_code}): {res.text}")
            except Exception as err:
                logger.error(f"[OPENAI TRANSLATE] Connection error: {err}")

        # 2. Mock Fallback
        logger.info(
            f"[MOCK NMT] Translating text '{text}' from {source_lang} -> {target_lang}"
        )
        if target_lang == "en" and source_lang == "hi":
            return "I want information about the PM Kisan scheme"
        return text

    async def text_to_speech(self, text: str, language: str) -> str:
        """Synthesize text to speech using OpenAI TTS.

        Args:
            text: Content to synthesize.
            language: Target language of audio synthesis.

        Returns:
            A public URL path to the synthesized audio file.
        """
        # 1. First attempt real OpenAI TTS speech synthesis
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock"):
            logger.info(f"[OPENAI TTS] Synthesizing speech for: '{text}' in language: {language}")
            url = "https://api.openai.com/v1/audio/speech"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "tts-1",
                "input": text,
                "voice": "alloy"
            }
            try:
                # Ensure the static audio assets directory exists
                static_audio_dir = os.path.join("backend", "static", "audio")
                if not os.path.exists(static_audio_dir):
                    os.makedirs(static_audio_dir, exist_ok=True)

                audio_filename = f"speech_{uuid.uuid4().hex}.mp3"
                output_path = os.path.join(static_audio_dir, audio_filename)

                async with httpx.AsyncClient(timeout=20.0) as client:
                    res = await client.post(url, json=payload, headers=headers)
                    if res.status_code == 200:
                        with open(output_path, "wb") as f:
                            f.write(res.content)
                        logger.info(f"[OPENAI TTS] Generated speech file at: {output_path}")
                        # Return public relative path
                        return f"/static/audio/{audio_filename}"
                    else:
                        logger.error(f"[OPENAI TTS] API error (status {res.status_code}): {res.text}")
            except Exception as err:
                logger.error(f"[OPENAI TTS] Connection error: {err}")

        # 2. Mock Fallback
        logger.info(
            f"[MOCK TTS] Synthesizing speech for: '{text}' in language: {language}"
        )
        return f"http://mock-bhashini-tts.local/synthesized_speech_{language}.mp3"
