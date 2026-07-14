"""Configuration module to load and validate environment variables."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validates and holds all application-wide configurations."""

    # Database & Redis Settings
    DATABASE_URL: str
    REDIS_URL: str

    # Ollama LLM Settings
    OLLAMA_HOST: str
    OLLAMA_MODEL: str

    # WhatsApp API Webhook Credentials
    WHATSAPP_ACCESS_TOKEN: str
    WHATSAPP_VERIFY_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str

    # Bhashini Speech API Credentials
    BHASHINI_API_KEY: str
    BHASHINI_USER_ID: str
    BHASHINI_SOURCE_LANG: str
    BHASHINI_PIPELINE_ID: str

    # Groq & OpenAI Cloud Credentials (Optional fallback)
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
