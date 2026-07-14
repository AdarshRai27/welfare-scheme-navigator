"""Integration test suite verifying Phase 4 Response Delivery and Form Auto-fill pipelines."""

import os
import uuid
import pytest
from fastapi.testclient import TestClient

from app.api.webhook import session_manager
from app.db.vector_store import VectorStore
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_end_to_end_delivery_and_form_filling() -> None:
    """Validate end-to-end pipeline: Webhook -> Agent -> Form Filler -> Static download links."""
    # Reset databases and static cache
    VectorStore._in_memory_schemes.clear()
    store = VectorStore(is_mock=True)

    # Ingest a PM-Kisan mock scheme
    pm_kisan = {
        "id": uuid.uuid4(),
        "name": "PM-Kisan Samman Nidhi",
        "issuing_body": "Central",
        "category": "Agriculture",
        "description": "Direct benefit transfer scheme for farmers",
        "eligibility_rules": {
            "land_size_limit": 2.0,
        },
        "source_url": "https://pmkisan.gov.in",
    }
    await store.add_scheme(pm_kisan)

    # Setup session profile parameters for user
    user_phone = "919900887766"
    await session_manager.clear_session(user_phone)
    await session_manager.save_session(
        user_phone,
        {
            "whatsapp_id": user_phone,
            "preferred_language": "en",
            "extracted_profile": {
                "name": "Arjun Singh",
                "aadhaar_number": "9999-8888-7777",
                "land_size_hectares": 1.2,
                "state": "Uttar Pradesh",
            },
        },
    )

    # Post an agricultural enquiry text query to trigger RAG
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
                                    "from": user_phone,
                                    "id": "wamid.text_enquiry",
                                    "timestamp": "1700000030",
                                    "text": {"body": "Farmer crop support schemes"},
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

    # Verify that the pre-filled JSON form file was created in static folder
    expected_filename = "pm_kisan_samman_nidhi_filled.json"
    static_filepath = os.path.join("backend/static/forms", expected_filename)
    assert os.path.exists(static_filepath)

    # Verify that we can download the file via FastAPI static mounting
    download_res = client.get(f"/static/forms/{expected_filename}")
    assert download_res.status_code == 200
    form_data = download_res.json()

    # Confirm correct user data was auto-filled in the form schema
    assert form_data["scheme_name"] == "PM-Kisan Samman Nidhi"
    assert form_data["applicant_name"] == "Arjun Singh"
    assert form_data["identity_aadhaar"] == "9999-8888-7777"
    assert form_data["landholdings_hectares"] == 1.2
    assert form_data["state_residence"] == "Uttar Pradesh"
