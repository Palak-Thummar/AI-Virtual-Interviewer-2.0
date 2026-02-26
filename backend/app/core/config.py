"""
Application configuration and settings.
Handles environment variables and app-wide constants.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
from openai import OpenAI

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # App settings
    APP_NAME: str = "AI Virtual Interviewer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "ai_interviewer"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenRouter API
    OPENROUTER_API_KEY: str = ""
    # OpenRouter Model name (configurable)
    OPENROUTER_MODEL_NAME: str = "nvidia/nemotron-3-nano-30b-a3b:free"
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: list = ["pdf", "docx"]
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173"
    ]


def get_available_models_formatted() -> str:
    """
    Get list of available OpenRouter models as a formatted string.
    """
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY
        )
        models = client.models.list()
        model_names = [m.id for m in models.data[:10]]  # Show first 10
        if model_names:
            return ', '.join(model_names)
        return "No models found"
    except Exception as e:
        return f"Could not list models: {str(e)}"


settings = Settings()
