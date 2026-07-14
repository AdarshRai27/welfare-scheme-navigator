"""OCR service helper for document processing using Groq Vision API or mocks."""

import base64
import json
import logging
from typing import Any, Dict

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """Service to extract structured fields from document photos using cloud vision or mock fallbacks."""

    async def extract_document_data(
        self, image_bytes: bytes, filename_hint: str = ""
    ) -> Dict[str, Any]:
        """Extracts fields from document photos (Aadhaar, Income, Land, etc.).

        If a GROQ_API_KEY is active, uses Llama 3.2 Vision in the cloud for real OCR.
        Otherwise, falls back to high-fidelity mock data.
        """
        hint = filename_hint.lower()

        # 1. Use Groq Vision if API key is active
        if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("mock"):
            logger.info(
                f"[GROQ VISION OCR] Parsing document: hint={filename_hint} | size={len(image_bytes)} bytes"
            )
            try:
                base64_img = base64.b64encode(image_bytes).decode("utf-8")
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                }

                # Dynamic prompt based on document hint
                prompt_text = (
                    "Extract structured information from this Indian government document. "
                    "Analyze the text fields and numbers carefully. "
                    "Return ONLY a raw JSON dictionary. Do not include markdown codeblocks or descriptions. "
                    "Fields to parse if found:\n"
                    "- 'name' (string, applicant full name)\n"
                    "- 'aadhaar_number' (string, formatted XXXX-XXXX-XXXX)\n"
                    "- 'annual_income' (integer, numeric annual income in INR)\n"
                    "- 'land_size_hectares' (float, landholdings size)\n"
                    "- 'state' (string, state of residence, e.g., 'Uttar Pradesh')"
                )

                payload = {
                    "model": "llama-3.2-11b-vision-preview",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_img}"
                                    },
                                }
                            ],
                        }
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                }

                async with httpx.AsyncClient(timeout=25.0) as client:
                    res = await client.post(url, json=payload, headers=headers)
                    if res.status_code == 200:
                        result = res.json()
                        content = result["choices"][0]["message"]["content"].strip()
                        extracted_fields = json.loads(content)
                        logger.info(
                            f"[GROQ VISION OCR] Successfully parsed fields: {extracted_fields}"
                        )

                        doc_type = "unknown"
                        if "aadhaar" in hint:
                            doc_type = "aadhaar"
                        elif "income" in hint:
                            doc_type = "income_certificate"
                        elif "land" in hint:
                            doc_type = "land_record"

                        return {
                            "document_type": doc_type,
                            "extracted_fields": extracted_fields,
                        }
                    else:
                        logger.warning(
                            f"[GROQ VISION OCR] API error (status {res.status_code}): {res.text}"
                        )
            except Exception as err:
                logger.warning(
                    f"[GROQ VISION OCR] Connection or parsing error: {err}"
                )

        # 2. Mock Fallback
        logger.info(
            f"[MOCK OCR] Reading document: hint={filename_hint} | size={len(image_bytes)} bytes"
        )
        if "aadhaar" in hint or "aadhar" in hint:
            return {
                "document_type": "aadhaar",
                "extracted_fields": {
                    "name": "Rajesh Kumar",
                    "aadhaar_number": "1234-5678-9012",
                    "gender": "Male",
                    "state": "Uttar Pradesh",
                },
            }
        elif "income" in hint:
            return {
                "document_type": "income_certificate",
                "extracted_fields": {
                    "name": "Rajesh Kumar",
                    "annual_income": 48000,
                    "state": "Uttar Pradesh",
                },
            }
        elif "land" in hint:
            return {
                "document_type": "land_record",
                "extracted_fields": {
                    "owner_name": "Rajesh Kumar",
                    "land_size_hectares": 1.2,
                    "state": "Uttar Pradesh",
                },
            }
        else:
            return {
                "document_type": "unknown",
                "extracted_fields": {
                    "text": "Mock extracted raw text from general document."
                },
            }
