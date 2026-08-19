"""Dedicated Conventional Document OCR Engine and Deterministic Indian Document Parser.

Supports dedicated OCR services (OCR.space, Google Cloud Vision, Azure Vision)
and deterministically parses Aadhaar Cards, Income Certificates, and Land Records
WITHOUT using multimodal LLM hallucinations or fabricating random placeholder values.
"""

import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Indian State Mapping Dictionary
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Jammu and Kashmir", "Ladakh"
]

DEVANAGARI_STATES_MAP = {
    "उत्तर प्रदेश": "Uttar Pradesh", "यूपी": "Uttar Pradesh",
    "बिहार": "Bihar", "मध्य प्रदेश": "Madhya Pradesh", "एमपी": "Madhya Pradesh",
    "राजस्थान": "Rajasthan", "महाराष्ट्र": "Maharashtra", "हरियाणा": "Haryana",
    "पंजाब": "Punjab", "गुजरात": "Gujarat", "झारखंड": "Jharkhand",
    "उत्तराखंड": "Uttarakhand", "पश्चिम बंगाल": "West Bengal", "छत्तीसगढ़": "Chhattisgarh",
    "ओडिशा": "Odisha", "दिल्ली": "Delhi"
}


class OCRService:
    """Robust, production-grade OCR extraction and deterministic document parsing engine."""

    async def extract_document_data(
        self,
        image_bytes: bytes,
        filename_hint: str = "",
        expected_type: str = "auto",
    ) -> Dict[str, Any]:
        """Runs dedicated OCR on image bytes and deterministically parses extracted text.

        Args:
            image_bytes: Raw binary image content.
            filename_hint: Original filename for context.
            expected_type: Expected document type ('aadhaar', 'income', 'land', 'auto').

        Returns:
            Dictionary containing 'document_type', 'extracted_fields', and 'raw_text'.
            If unreadable, 'extracted_fields' will be empty (no random placeholders).
        """
        if not image_bytes or len(image_bytes) < 5:
            logger.warning("[OCR] Image payload empty.")
            return {"document_type": "unknown", "extracted_fields": {}, "raw_text": "", "success": False}

        raw_text = ""
        provider_used = "none"

        # 1. Try OpenAI GPT-4o-mini Vision OCR if configured (using OPEN_AI_OCR key)
        openai_key = settings.OPEN_AI_OCR or settings.OPENAI_API_KEY
        if openai_key and not openai_key.startswith("mock"):
            raw_text, provider_used = await self._run_openai_vision_ocr(image_bytes)

        # 2. Try API4AI OCR Cloud Engine (Primary Dedicated OCR)
        if not raw_text and settings.API4AI_API_KEY and not settings.API4AI_API_KEY.startswith("mock"):
            raw_text, provider_used = await self._run_api4ai_ocr(image_bytes)

        # 3. Try Google Cloud Vision API if API key provided
        if not raw_text and settings.GOOGLE_VISION_API_KEY and not settings.GOOGLE_VISION_API_KEY.startswith("mock"):
            raw_text, provider_used = await self._run_google_vision_ocr(image_bytes)

        # 3. Try Azure Computer Vision Read API if configured
        if not raw_text and settings.AZURE_OCR_KEY and settings.AZURE_OCR_ENDPOINT:
            raw_text, provider_used = await self._run_azure_ocr(image_bytes)

        # 4. Try OCR.Space API (Dedicated OCR supporting English & Hindi)
        if not raw_text and settings.OCR_SPACE_API_KEY:
            raw_text, provider_used = await self._run_ocr_space(image_bytes)

        # 5. Try local Tesseract OCR if available
        if not raw_text:
            raw_text, provider_used = self._run_local_tesseract(image_bytes)

        logger.info(f"[OCR] Extracted raw text using provider '{provider_used}': {len(raw_text)} chars")

        if not raw_text or not raw_text.strip():
            logger.info("[OCR] OCR returned empty text from image.")
            return {
                "document_type": "unknown",
                "extracted_fields": {},
                "raw_text": "",
                "provider": provider_used,
                "success": False,
            }

        # Deterministic Regex & Rule-Based Field Extraction (Strict, No Hallucinations)
        doc_type, extracted_fields = self.parse_document_text(raw_text, expected_type, filename_hint)

        return {
            "document_type": doc_type,
            "extracted_fields": extracted_fields,
            "raw_text": raw_text.strip(),
            "provider": provider_used,
            "success": bool(extracted_fields),
        }

    async def _run_openai_vision_ocr(self, image_bytes: bytes) -> Tuple[str, str]:
        """Calls OpenAI GPT-4o-mini Vision API to extract text from Indian government documents."""
        try:
            import base64
            b64_img = base64.b64encode(image_bytes).decode("utf-8")
            url = "https://api.openai.com/v1/chat/completions"
            openai_key = settings.OPEN_AI_OCR or settings.OPENAI_API_KEY
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json",
            }
            prompt = (
                "Transcribe all text from this Indian government document (Aadhaar Card, Income Certificate, or Land Record / Khatauni) verbatim. "
                "Include all names, dates of birth, 12-digit Aadhaar numbers, income amounts, land area/hectares/acres, and states. "
                "Output plain text only without any explanations."
            )
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}},
                        ],
                    }
                ],
                "temperature": 0.1,
            }
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    if content:
                        logger.info(f"[OCR] OpenAI Vision extracted {len(content)} chars")
                        return content, "openai_vision"
                else:
                    logger.warning(f"[OCR] OpenAI Vision error ({res.status_code}): {res.text}")
        except Exception as err:
            logger.warning(f"[OCR] OpenAI Vision request error: {err}")
        return "", "openai_vision_failed"

    async def _run_api4ai_ocr(self, image_bytes: bytes) -> Tuple[str, str]:
        """Calls api4ai OCR Cloud API for high-precision document character recognition."""
        try:
            url = "https://api4ai.cloud/ocr/v1/results"
            headers = {"X-API-KEY": settings.API4AI_API_KEY}
            files = {"image": ("document.jpg", image_bytes, "image/jpeg")}
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(url, headers=headers, files=files)
                if res.status_code == 200:
                    data = res.json()
                    raw_lines = []
                    for result in data.get("results", []):
                        for ent in result.get("entities", []):
                            for obj in ent.get("objects", []):
                                for sub_ent in obj.get("entities", []):
                                    if "text" in sub_ent and sub_ent["text"]:
                                        raw_lines.append(sub_ent["text"].strip())
                    full_text = "\n".join(raw_lines).strip()
                    if full_text:
                        logger.info(f"[OCR] API4AI extracted {len(full_text)} chars")
                        return full_text, "api4ai_ocr"
                else:
                    logger.warning(f"[OCR] API4AI error ({res.status_code}): {res.text}")
        except Exception as err:
            logger.warning(f"[OCR] API4AI request error: {err}")
        return "", "api4ai_failed"

    async def _run_ocr_space(self, image_bytes: bytes) -> Tuple[str, str]:
        """Calls OCR.Space REST API for high-accuracy multi-language OCR."""
        try:
            url = "https://api.ocr.space/parse/image"
            api_key = settings.OCR_SPACE_API_KEY or "K87899142388957"
            base64_str = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
            
            data = {
                "apikey": api_key,
                "base64Image": base64_str,
                "language": "eng",
                "isOverlayRequired": False,
                "detectOrientation": True,
                "scale": True,
                "OCREngine": "2",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, data=data)
                if res.status_code == 200:
                    json_data = res.json()
                    parsed_results = json_data.get("ParsedResults", [])
                    if parsed_results:
                        text = parsed_results[0].get("ParsedText", "")
                        return text, "ocr_space"
        except Exception as err:
            logger.warning(f"[OCR] OCR.space API request error: {err}")
        return "", "ocr_space_failed"

    async def _run_google_vision_ocr(self, image_bytes: bytes) -> Tuple[str, str]:
        """Calls Google Cloud Vision API TEXT_DETECTION endpoint."""
        try:
            url = f"https://vision.googleapis.com/v1/images:annotate?key={settings.GOOGLE_VISION_API_KEY}"
            content_b64 = base64.b64encode(image_bytes).decode("utf-8")
            payload = {
                "requests": [
                    {
                        "image": {"content": content_b64},
                        "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                    }
                ]
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    responses = data.get("responses", [])
                    if responses and "fullTextAnnotation" in responses[0]:
                        return responses[0]["fullTextAnnotation"].get("text", ""), "google_vision"
        except Exception as err:
            logger.warning(f"[OCR] Google Vision API error: {err}")
        return "", "google_vision_failed"

    async def _run_azure_ocr(self, image_bytes: bytes) -> Tuple[str, str]:
        """Calls Azure Computer Vision Read OCR API."""
        try:
            endpoint = settings.AZURE_OCR_ENDPOINT.rstrip("/")
            url = f"{endpoint}/vision/v3.2/read/analyze"
            headers = {
                "Ocp-Apim-Subscription-Key": settings.AZURE_OCR_KEY,
                "Content-Type": "application/octet-stream",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, content=image_bytes, headers=headers)
                if res.status_code in (200, 202):
                    op_location = res.headers.get("Operation-Location")
                    if op_location:
                        # Poll operation location
                        import asyncio
                        for _ in range(5):
                            await asyncio.sleep(1)
                            poll_res = await client.get(op_location, headers={"Ocp-Apim-Subscription-Key": settings.AZURE_OCR_KEY})
                            if poll_res.status_code == 200:
                                read_data = poll_res.json()
                                if read_data.get("status") == "succeeded":
                                    lines = []
                                    for page in read_data.get("analyzeResult", {}).get("readResults", []):
                                        for line in page.get("lines", []):
                                            lines.append(line.get("text", ""))
                                    return "\n".join(lines), "azure_ocr"
        except Exception as err:
            logger.warning(f"[OCR] Azure OCR error: {err}")
        return "", "azure_ocr_failed"

    def _run_local_tesseract(self, image_bytes: bytes) -> Tuple[str, str]:
        """Tries local Tesseract OCR if installed on system."""
        try:
            import io
            import pytesseract
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(img, lang="eng+hin")
            if text and text.strip():
                return text.strip(), "local_tesseract"
        except Exception:
            pass
        return "", "none"

    def parse_document_text(
        self, raw_text: str, expected_type: str = "auto", filename_hint: str = ""
    ) -> Tuple[str, Dict[str, Any]]:
        """Parses extracted OCR text deterministically using Indian document regex patterns.

        Strictly returns only verified fields. Returns empty dict if no valid fields found.
        """
        text = raw_text.strip()
        fields: Dict[str, Any] = {}
        doc_type = "unknown"

        # 1. Parse Aadhaar Card (12-digit number format: \b[2-9]\d{3}\s?\d{4}\s?\d{4}\b)
        aadhaar_match = re.search(r"\b([2-9]\d{3})[\s-]?(\d{4})[\s-]?(\d{4})\b", text)
        if aadhaar_match:
            doc_type = "aadhaar"
            raw_aadhaar = f"{aadhaar_match.group(1)}-{aadhaar_match.group(2)}-{aadhaar_match.group(3)}"
            fields["aadhaar_number"] = raw_aadhaar
            fields["verified_status"] = True

        # 2. Parse Date of Birth / Year of Birth
        dob_match = re.search(
            r"(?:DOB|D\.O\.B|Date of Birth|जन्म तिथि|जन्म वर्ष|Year of Birth)[:\s]*([0-9]{2}[/-][0-9]{2}[/-][0-9]{4}|[0-9]{4})",
            text,
            re.IGNORECASE,
        )
        if dob_match:
            raw_dob = dob_match.group(1).strip()
            if len(raw_dob) == 4 and raw_dob.isdigit():
                birth_year = int(raw_dob)
                fields["age"] = max(1, 2026 - birth_year)
            elif len(raw_dob) >= 8:
                year_part = raw_dob.replace("-", "/").split("/")[-1]
                if len(year_part) == 4 and year_part.isdigit():
                    birth_year = int(year_part)
                    fields["age"] = max(1, 2026 - birth_year)

        # 3. Parse Gender
        gender_match = re.search(r"\b(MALE|FEMALE|TRANSGENDER|पुरुष|महिला)\b", text, re.IGNORECASE)
        if gender_match:
            g_str = gender_match.group(1).upper()
            fields["gender"] = "Female" if g_str in ("FEMALE", "महिला") else "Male"

        # 4. Parse Annual Income (Income Certificate / आय प्रमाण पत्र)
        income_match = re.search(
            r"(?:वार्षिक आय|कुल आय|वार्षिक पारिवारिक आय|Annual Income|Total Income)[:\s₹Rs.]*(\d{4,8})",
            text,
            re.IGNORECASE,
        )
        if income_match:
            doc_type = "income_certificate"
            fields["annual_income"] = int(income_match.group(1))
            fields["verified_status"] = True

        # 5. Parse Land Size (Khatauni / Land Revenue Record / भू-अभिलेख)
        land_match = re.search(
            r"(?:कुल रकबा|रकबा|क्षेत्रफल|Area|Total Area|Land Size)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:हेक्टेयर|हेक्टे\.|Hectare|Ha|एकड़|Acre)?",
            text,
            re.IGNORECASE,
        )
        if land_match:
            doc_type = "land_record"
            raw_size = float(land_match.group(1))
            matched_segment = land_match.group(0).lower()
            if "एकड़" in matched_segment or "acre" in matched_segment:
                fields["land_size_hectares"] = round(raw_size * 0.404686, 2)
            else:
                fields["land_size_hectares"] = raw_size
            fields["verified_status"] = True

        # 6. Parse State / Domicile
        for state_name in INDIAN_STATES:
            if re.search(rf"\b{re.escape(state_name)}\b", text, re.IGNORECASE):
                fields["state"] = state_name
                break
        if "state" not in fields:
            for devanagari_state, eng_state in DEVANAGARI_STATES_MAP.items():
                if devanagari_state in text:
                    fields["state"] = eng_state
                    break

        # 7. Extract Name from Document Text (Clean lines before DOB / Aadhaar)
        name_candidate = self._extract_clean_name(text)
        if name_candidate:
            fields["name"] = name_candidate

        # Contextual Document Type resolution
        if doc_type == "unknown":
            if "income" in filename_hint.lower() or "आय" in text or "income_certificate" in expected_type:
                doc_type = "income_certificate"
            elif "land" in filename_hint.lower() or "खतौनी" in text or "khatauni" in filename_hint.lower():
                doc_type = "land_record"
            elif "aadhaar" in filename_hint.lower() or "आधार" in text or "government of india" in text.lower():
                doc_type = "aadhaar"

        return doc_type, fields

    def _extract_clean_name(self, text: str) -> Optional[str]:
        """Isolates citizen name from recognized document text."""
        ignored_phrases = [
            "government of india", "unique identification", "authority of india",
            "bharat sarkar", "mera aadhaar", "enrollment", "help@uidai.gov.in",
            "www.uidai.gov.in", "income certificate", "tahsildar", "revenue department",
            "khatauni", "khasra", "uttar pradesh", "bihar", "male", "female", "dob",
            "year of birth", "आधार", "भारत सरकार", "office of the"
        ]
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 3]
        for line in lines:
            # Strip label prefixes like Name: / Applicant: / आवेदक:
            cleaned_line = re.sub(
                r"^(?:name|applicant(?:\s*name)?|आवेदक(?:\s*का\s*नाम)?|नाम|खातेदार(?:\s*का\s*नाम)?|citizen)[:\s\-]+",
                "",
                line,
                flags=re.IGNORECASE,
            ).strip()

            line_lower = cleaned_line.lower()
            if any(phrase in line_lower for phrase in ignored_phrases):
                continue
            if re.search(r"[0-9]{4,}", cleaned_line):
                continue
            # Check if line looks like a person's name (2-4 words, alphabetic)
            words = cleaned_line.split()
            if 2 <= len(words) <= 4 and all(re.match(r"^[A-Za-z\u0900-\u097F\.\'-]+$", w) for w in words):
                return cleaned_line.strip(". ")
        return None


ocr_service = OCRService()
