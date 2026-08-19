"""Configuration module to load and validate environment variables."""
import os
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

    # Bhashini Speech API Credentials
    BHASHINI_API_KEY: str = "mock_key"
    BHASHINI_USER_ID: str = "mock_user"
    BHASHINI_SOURCE_LANG: str = "hi"
    BHASHINI_PIPELINE_ID: str = "mock_pipeline"

    # AI Model Keys (Loaded dynamically from environment variables or .env)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY")
    DIDIT_API_KEY: Optional[str] = os.getenv("DIDIT_API_KEY")
    DIDIT_CLIENT_ID: Optional[str] = os.getenv("DIDIT_CLIENT_ID")

    # Dedicated OCR Engine API Keys
    API4AI_API_KEY: Optional[str] = os.getenv("API4AI_API_KEY", "a4a-hrczgMEhktuNNCctwj4xC79acGEAKqAn")
    GOOGLE_VISION_API_KEY: Optional[str] = os.getenv("GOOGLE_VISION_API_KEY")
    OCR_SPACE_API_KEY: Optional[str] = os.getenv("OCR_SPACE_API_KEY")
    AZURE_OCR_KEY: Optional[str] = os.getenv("AZURE_OCR_KEY")
    AZURE_OCR_ENDPOINT: Optional[str] = os.getenv("AZURE_OCR_ENDPOINT")
    BHASHINI_OCR_KEY: Optional[str] = os.getenv("BHASHINI_OCR_KEY")

    # Configuration source preference (.env file support)
    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Globally shared settings instance loaded from environment
settings = Settings()
