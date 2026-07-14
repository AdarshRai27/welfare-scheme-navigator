"""Tests verifying the frontend diagnostic and web messaging endpoints."""

import io
import pytest
from fastapi.testclient import TestClient

from app.api.webhook import session_manager
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_session_diagnostics_endpoints() -> None:
    """Validate that GET and DELETE diagnostics endpoints read/clear cache correctly."""
    user_phone = "919999999999"

    # 1. Initialize session with mock data
    mock_session = {
        "whatsapp_id": user_phone,
        "preferred_language": "hi",
        "extracted_profile": {"name": "Test Diagnostics User"},
    }
    await session_manager.save_session(user_phone, mock_session)

    # 2. Verify GET diagnostic endpoint retrieves it
    response_get = client.get(f"/webhook/diagnostics/session/{user_phone}")
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["whatsapp_id"] == user_phone
    assert data["extracted_profile"]["name"] == "Test Diagnostics User"

    # 3. Verify DELETE diagnostic endpoint clears it
    response_del = client.delete(f"/webhook/diagnostics/session/{user_phone}")
    assert response_del.status_code == 200
    assert response_del.json() == {"status": "cleared"}

    # 4. Verify GET returns empty dictionary now
    response_get_cleared = client.get(f"/webhook/diagnostics/session/{user_phone}")
    assert response_get_cleared.status_code == 200
    assert response_get_cleared.json() == {}


@pytest.mark.asyncio
async def test_web_message_endpoint() -> None:
    """Validate that POST /webhook/web/message processes text and image uploads successfully."""
    user_phone = "918888888888"

    # Clear previous state
    await session_manager.clear_session(user_phone)

    # 1. Test Text input message routing
    response_text = client.post(
        "/webhook/web/message",
        data={"phone": user_phone, "message_type": "text", "text": "Is PM Kisan available?"}
    )
    assert response_text.status_code == 200
    data_text = response_text.json()
    assert data_text["status"] == "success"
    assert "reply_text" in data_text
    assert "session" in data_text

    # 2. Test Image Upload (Aadhaar OCR simulation)
    fake_image_file = io.BytesIO(b"fake image bytes content for test")
    response_img = client.post(
        "/webhook/web/message",
        data={"phone": user_phone, "message_type": "aadhaar"},
        files={"file": ("aadhaar.jpg", fake_image_file, "image/jpeg")}
    )
    assert response_img.status_code == 200
    data_img = response_img.json()
    assert data_img["status"] == "success"
    # Extracted profile name should match Rajesh Kumar via mock Tesseract OCR
    assert data_img["session"]["extracted_profile"]["name"] == "Rajesh Kumar"
    assert data_img["session"]["extracted_profile"]["aadhaar_number"] == "1234-5678-9012"
