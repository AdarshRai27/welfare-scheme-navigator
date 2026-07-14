"""Tests verifying the frontend diagnostic endpoints."""

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
