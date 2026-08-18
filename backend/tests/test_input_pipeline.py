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
async def test_multi_turn_document_profile_accumulation() -> None:
    """Validate that consecutive document uploads correctly accumulate fields in user state."""
    user_phone = "919999888877"

    # Reset any existing session state to start fresh
    await session_manager.clear_session(user_phone)

    # 1. Send Didit ID Scan
    fake_aadhaar = io.BytesIO(b"MOCK_AADHAAR_SCAN_BYTES")
    response1 = client.post(
        "/webhook/didit/scan",
        data={"phone": user_phone},
        files={"file": ("aadhaar.jpg", fake_aadhaar, "image/jpeg")},
    )
    assert response1.status_code == 200

    # Retrieve state from cache and verify Aadhaar fields exist
    state1 = await session_manager.get_session(user_phone)
    assert "extracted_profile" in state1
    assert "name" in state1["extracted_profile"]

    # 2. Send 1-Click Didit verification
    response2 = client.get(f"/webhook/didit/oauth/mock_verify?phone={user_phone}")
    assert response2.status_code == 200

    # Retrieve state from cache and verify fields merged
    state2 = await session_manager.get_session(user_phone)
    profile = state2["extracted_profile"]
    assert "name" in profile
    assert "state" in profile

    # 3. Verify session clear works (Privacy Option A)
    await session_manager.clear_session(user_phone)
    cleared_state = await session_manager.get_session(user_phone)
    assert cleared_state == {}
