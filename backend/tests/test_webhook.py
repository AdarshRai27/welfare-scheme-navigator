"""Test suite verifying WhatsApp webhook verification (GET) and reception (POST)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_webhook_verify_success() -> None:
    """Test verification handshake GET route with correct token and challenge."""
    response = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test_whatsapp_verify_token",
            "hub.challenge": "123456789_challenge_ok",
        },
    )
    assert response.status_code == 200
    assert response.text == "123456789_challenge_ok"


def test_webhook_verify_failure() -> None:
    """Test verification handshake GET route rejection with wrong token."""
    response = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "incorrect_verify_token",
            "hub.challenge": "challenge_failed",
        },
    )
    assert response.status_code == 403
    assert "Verification token mismatch" in response.text


def test_webhook_receive_text_message() -> None:
    """Test POST webhook endpoint successfully receives and parses text payload."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "entry_id_1",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "919999999999",
                                    "id": "wamid.1",
                                    "timestamp": "1700000000",
                                    "text": {"body": "Show me local schemes"},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    response = client.post("/webhook/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}


def test_webhook_receive_audio_message() -> None:
    """Test POST webhook endpoint successfully receives and parses audio payload."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "entry_id_1",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "919999999999",
                                    "id": "wamid.2",
                                    "timestamp": "1700000001",
                                    "audio": {
                                        "id": "audio_media_id_123",
                                        "mime_type": "audio/ogg",
                                    },
                                    "type": "audio",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    response = client.post("/webhook/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}


def test_webhook_receive_image_message() -> None:
    """Test POST webhook endpoint successfully receives and parses image payload."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "entry_id_1",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "919999999999",
                                    "id": "wamid.3",
                                    "timestamp": "1700000002",
                                    "image": {
                                        "id": "image_media_id_123",
                                        "mime_type": "image/jpeg",
                                    },
                                    "type": "image",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    response = client.post("/webhook/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}
