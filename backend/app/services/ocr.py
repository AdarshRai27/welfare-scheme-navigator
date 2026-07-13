"""OCR mock service helper for Tesseract and Qwen2-VL processing."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class OCRService:
    """Mock service to extract structured fields from document photos."""

    async def extract_document_data(
        self, image_bytes: bytes, filename_hint: str = ""
    ) -> Dict[str, Any]:
        """Mock extracting fields from document photos (Aadhaar, Income, Land, etc.).

        Args:
            image_bytes: Raw binary content of the photo.
            filename_hint: Filename or identifier indicating document type.

        Returns:
            Dictionary containing document type and extracted structured fields.
        """
        logger.info(
            f"[MOCK OCR] Reading document: hint={filename_hint} | size={len(image_bytes)} bytes"
        )
        hint = filename_hint.lower()

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
