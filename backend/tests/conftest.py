"""Configuration module for pytest suite execution."""

import os
import sys

# Inject the parent directory into python search path for relative app module loading
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
)

# Populate test-specific dummy values into the OS environment before app import
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_navigator_db"
)
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["OLLAMA_HOST"] = "http://localhost:11434"
os.environ["OLLAMA_MODEL"] = "llama3.1:8b"
os.environ["WHATSAPP_ACCESS_TOKEN"] = "test_whatsapp_token"
os.environ["WHATSAPP_VERIFY_TOKEN"] = "test_whatsapp_verify_token"
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "test_whatsapp_phone_number_id"
os.environ["BHASHINI_API_KEY"] = "test_bhashini_key"
os.environ["BHASHINI_USER_ID"] = "test_bhashini_user"
os.environ["BHASHINI_SOURCE_LANG"] = "hi"
os.environ["BHASHINI_PIPELINE_ID"] = "test_bhashini_pipeline"
