"""
Application configuration and settings.
Handles environment variables and app-wide constants.
"""

import json
import re
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List, Optional
from openai import OpenAI

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # App settings
    APP_NAME: str = "CareerIQ"
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
    CORS_ORIGINS: str = "https://ai-virtual-interviewer-2-0.vercel.app"
    CORS_ORIGIN_REGEX: Optional[str] = r"https://.*\.vercel\.app"
    DEV_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    def get_cors_origins(self) -> List[str]:
        raw = (self.CORS_ORIGINS or "").strip()
        normalized = []

        if not raw:
            normalized = []
        elif raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    for item in parsed:
                        origin = str(item).strip().strip('"\'').rstrip('/')
                        if origin:
                            normalized.append(origin)
            except json.JSONDecodeError:
                normalized = []
        else:
            for item in raw.split(","):
                origin = item.strip().strip('"\'').rstrip('/')
                if origin:
                    normalized.append(origin)

        # Always include local dev origins to prevent preflight 400 in local frontend testing
        normalized.extend(self.DEV_CORS_ORIGINS)

        # Return unique origins preserving insertion order
        return list(dict.fromkeys(normalized))

    def get_cors_origin_regex(self) -> str:
        configured = (self.CORS_ORIGIN_REGEX or "").strip().strip('"\'')
        local_fallback = r"^http://localhost(:\d+)?$|^http://127\.0\.0\.1(:\d+)?$"

        if configured:
            try:
                re.compile(configured)
                return rf"(?:{configured})|(?:{local_fallback})"
            except re.error:
                pass

        return rf"^https://.*\.vercel\.app$|{local_fallback}"


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
