"""Configuration module to load and validate environment variables."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validates and holds all application-wide configurations."""


    # Database & Redis Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///welfare.db"
    REDIS_URL: str = "redis://localhost:6379"

    # Ollama LLM Settings
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # WhatsApp API Webhook Credentials
    WHATSAPP_ACCESS_TOKEN: str = "mock_token"
    WHATSAPP_VERIFY_TOKEN: str = "mock_verify"
    WHATSAPP_PHONE_NUMBER_ID: str = "mock_phone"

    # Bhashini Speech API Credentials
    BHASHINI_API_KEY: str = "mock_key"
    BHASHINI_USER_ID: str = "mock_user"
    BHASHINI_SOURCE_LANG: str = "hi"
    BHASHINI_PIPELINE_ID: str = "mock_pipeline"
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Configuration source preference (.env file support)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Globally shared settings instance loaded from environment
settings = Settings()
