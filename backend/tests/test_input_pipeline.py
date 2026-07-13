"""Integration test suite verifying the Phase 2 Input Media processing pipelines."""

import pytest
from fastapi.testclient import TestClient

from app.api.webhook import session_manager
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_webhook_audio_transcription() -> None:
    """Validate that incoming audio messages run mock downloads ASR/NMT transcription."""
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
                                    "from": "918888888888",
                                    "id": "wamid.audio_msg_test",
                                    "timestamp": "1700000010",
                                    "audio": {
                                        "id": "media_audio_id",
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


@pytest.mark.asyncio
async def test_multi_turn_document_profile_accumulation() -> None:
    """Validate that consecutive OCR document uploads correctly accumulate fields in user state."""
    user_phone = "919999888877"

    # Reset any existing session state to start fresh
    await session_manager.clear_session(user_phone)

    # 1. Send Aadhaar document photo
    payload_aadhaar = {
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
                                    "from": user_phone,
                                    "id": "wamid.img_aadhaar",
                                    "timestamp": "1700000020",
                                    "image": {
                                        "id": "media_image_aadhaar",
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
    response1 = client.post("/webhook/whatsapp", json=payload_aadhaar)
    assert response1.status_code == 200

    # Retrieve state from cache and verify Aadhaar fields exist
    state1 = await session_manager.get_session(user_phone)
    assert state1.get("whatsapp_id") == user_phone
    assert state1["extracted_profile"]["name"] == "Rajesh Kumar"
    assert "aadhaar_number" in state1["extracted_profile"]
    assert "annual_income" not in state1["extracted_profile"]

    # 2. Send Income Certificate document photo
    payload_income = {
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
                                    "from": user_phone,
                                    "id": "wamid.img_income",
                                    "timestamp": "1700000021",
                                    "image": {
                                        "id": "media_image_income",
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
    response2 = client.post("/webhook/whatsapp", json=payload_income)
    assert response2.status_code == 200

    # Retrieve state from cache and verify both Aadhaar and Income fields merged
    state2 = await session_manager.get_session(user_phone)
    profile = state2["extracted_profile"]
    assert profile["name"] == "Rajesh Kumar"
    assert profile["aadhaar_number"] == "1234-5678-9012"
    assert profile["annual_income"] == 48000

    # 3. Verify session clear works (Privacy Option A)
    await session_manager.clear_session(user_phone)
    cleared_state = await session_manager.get_session(user_phone)
    assert cleared_state == {}
