"""Test suite verifying config loader loads expected test configurations."""

from app.core.config import settings


def test_settings_load() -> None:
    """Validate that environment settings load variables set in conftest."""
    assert (
        settings.DATABASE_URL
        == "postgresql+asyncpg://postgres:postgres@localhost:5432/test_navigator_db"
    )
    assert settings.REDIS_URL == "redis://localhost:6379/1"
    assert settings.OLLAMA_MODEL == "llama3.1:8b"
    assert settings.WHATSAPP_VERIFY_TOKEN == "test_whatsapp_verify_token"
    assert settings.BHASHINI_SOURCE_LANG == "hi"
