"""Test suite verifying Web-native message endpoints and Didit identity workflows."""

import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_web_message_text_flow() -> None:
    """Test POST /webhook/web/message endpoint successfully processes user text query."""
    response = client.post(
        "/webhook/web/message",
        data={
            "phone": "919999999999",
            "message_type": "text",
            "text": "Tell me about farmer support schemes",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "reply_text" in data
    assert len(data["reply_text"]) > 0


def test_web_message_audio_flow() -> None:
    """Test POST /webhook/web/message endpoint handles audio voice notes."""
    fake_audio_file = io.BytesIO(b"MOCK_OGG_AUDIO_BYTES_TEST")
    response = client.post(
        "/webhook/web/message",
        data={
            "phone": "919999999999",
            "message_type": "audio",
        },
        files={"file": ("test_voice.ogg", fake_audio_file, "audio/ogg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "reply_text" in data


def test_didit_id_scan_flow() -> None:
    """Test POST /webhook/didit/scan endpoint processes Didit ID card scans."""
    fake_image_file = io.BytesIO(b"MOCK_AADHAAR_IMAGE_BYTES")
    response = client.post(
        "/webhook/didit/scan",
        data={"phone": "919999999999"},
        files={"file": ("aadhaar_test.jpg", fake_image_file, "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("success", "unreadable")
    assert "reply_text" in data


def test_didit_oauth_session_and_verify() -> None:
    """Test 1-Click Didit OAuth session generation and token verification callback."""
    # 1. Create OAuth session
    session_res = client.post(
        "/webhook/didit/oauth/session",
        data={"phone": "919999999999"},
    )
    assert session_res.status_code == 200
    session_data = session_res.json()
    assert session_data["status"] == "success"
    assert "session_url" in session_data

    # 2. Verify token callback
    verify_res = client.get("/webhook/didit/oauth/mock_verify?phone=919999999999")
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["status"] == "success"
    assert "1-Click Didit Verified Profile" in verify_data["reply_text"]


def test_diagnostics_session_management() -> None:
    """Test GET and DELETE session diagnostic endpoints."""
    # Get session state
    get_res = client.get("/webhook/diagnostics/session/919999999999")
    assert get_res.status_code == 200

    # Delete session state
    del_res = client.delete("/webhook/diagnostics/session/919999999999")
    assert del_res.status_code == 200
    assert del_res.json() == {"status": "cleared"}
