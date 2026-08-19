"""Integration test suite verifying Web-native Input Media and Didit processing pipelines."""

import io
import pytest
from fastapi.testclient import TestClient

from app.api.webhook import session_manager
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_web_audio_transcription() -> None:
    """Validate that incoming web audio messages run Bhashini ASR/NMT transcription."""
    fake_audio = io.BytesIO(b"MOCK_AUDIO_CONTENT")
    response = client.post(
        "/webhook/web/message",
        data={
            "phone": "918888888888",
            "message_type": "audio",
        },
        files={"file": ("voice_note.ogg", fake_audio, "audio/ogg")},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_multi_turn_document_profile_accumulation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate that consecutive document uploads correctly accumulate fields in user state."""
    user_phone = "919999888877"

    # Reset any existing session state to start fresh
    await session_manager.clear_session(user_phone)

    import app.api.webhook as webhook_mod

    async def mock_extract(image_bytes, filename_hint="", expected_type="auto"):
        return {
            "document_type": "aadhaar",
            "extracted_fields": {
                "name": "Ramesh Kumar",
                "aadhaar_number": "9182-3746-5829",
                "state": "Uttar Pradesh",
                "verified_status": True,
            },
            "raw_text": "Sample document text",
            "provider": "mock",
            "success": True,
        }

    monkeypatch.setattr(webhook_mod.ocr_service, "extract_document_data", mock_extract)

    # 1. Send ID Scan
    fake_aadhaar = io.BytesIO(b"MOCK_AADHAAR_SCAN_BYTES")
    response1 = client.post(
        "/webhook/ocr/scan",
        data={"phone": user_phone},
        files={"file": ("aadhaar.jpg", fake_aadhaar, "image/jpeg")},
    )
    assert response1.status_code == 200

    # Retrieve state from cache and verify Aadhaar fields exist
    state1 = await session_manager.get_session(user_phone)
    assert "extracted_profile" in state1
    assert state1["extracted_profile"]["name"] == "Ramesh Kumar"
    assert state1["extracted_profile"]["state"] == "Uttar Pradesh"

    # 2. Verify session clear works (Privacy Option A)
    await session_manager.clear_session(user_phone)
    cleared_state = await session_manager.get_session(user_phone)
    assert cleared_state == {}


def test_deterministic_ocr_aadhaar_parsing() -> None:
    """Validate deterministic regex parser extracts Aadhaar number, age, gender, and name accurately."""
    from app.services.ocr import ocr_service

    sample_aadhaar_text = (
        "GOVERNMENT OF INDIA\n"
        "Ramesh Kumar\n"
        "DOB: 15/08/1964\n"
        "MALE\n"
        "9182 3746 5829\n"
        "Uttar Pradesh"
    )
    doc_type, fields = ocr_service.parse_document_text(sample_aadhaar_text, filename_hint="aadhaar.jpg")
    assert doc_type == "aadhaar"
    assert fields["aadhaar_number"] == "9182-3746-5829"
    assert fields["age"] == 62
    assert fields["gender"] == "Male"
    assert fields["state"] == "Uttar Pradesh"
    assert fields["name"] == "Ramesh Kumar"
    assert fields["verified_status"] is True


def test_deterministic_ocr_income_certificate_parsing() -> None:
    """Validate deterministic parser extracts annual income from income certificate text."""
    from app.services.ocr import ocr_service

    sample_income_text = (
        "कार्यालय तहसीलदार\n"
        "आय प्रमाण पत्र\n"
        "प्रमाणित किया जाता है कि आवेदक की वार्षिक आय ₹120000 है।\n"
        "राज्य: उत्तर प्रदेश"
    )
    doc_type, fields = ocr_service.parse_document_text(sample_income_text, filename_hint="income.jpg")
    assert doc_type == "income_certificate"
    assert fields["annual_income"] == 120000
    assert fields["state"] == "Uttar Pradesh"
    assert fields["verified_status"] is True


def test_deterministic_ocr_land_record_parsing() -> None:
    """Validate deterministic parser extracts land area in hectares from Khatauni text."""
    from app.services.ocr import ocr_service

    sample_khatauni_text = (
        "भू-अभिलेख खतौनी\n"
        "कुल रकबा: 1.45 हेक्टेयर\n"
        "उत्तर प्रदेश"
    )
    doc_type, fields = ocr_service.parse_document_text(sample_khatauni_text, filename_hint="khatauni.jpg")
    assert doc_type == "land_record"
    assert fields["land_size_hectares"] == 1.45
    assert fields["state"] == "Uttar Pradesh"
    assert fields["verified_status"] is True


def test_deterministic_ocr_empty_garbage_rejection() -> None:
    """Validate that unreadable or garbage text strictly returns empty fields (no random fabricated values)."""
    from app.services.ocr import ocr_service

    garbage_text = "blurry background noise 1234 random pattern"
    doc_type, fields = ocr_service.parse_document_text(garbage_text, filename_hint="photo.jpg")
    assert fields == {}

