# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl, field_validator
from typing import List, Dict, Any


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "JAM (Just A Minute)"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    FRONTEND_URL: str = "http://localhost:3000"

    # Server configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = True  # Default to False for safety
    WORKERS_COUNT: int = 1

    # Database
    DATABASE_URL: str

    @field_validator("DATABASE_URL", mode="before")
    def validate_database_url(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # JWT and Authentication settings
    SECRET_KEY: str
    # google
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_CLIENT_ID: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    COOKIE_CONFIG: Dict[str, Any] = {
        "httponly": True,
        "secure": False,  # Set to True in production (HTTPS)
        "samesite": "lax",
        "max_age": 604800,  # 7 days in seconds
        "path": "/",
        "domain": "localhost",  # Change in production!
    }

    # CORS
    BACKEND_CORS_ORIGINS: List[HttpUrl] = [
        "http://localhost:3000",  # Your Next.js app
        "http://localhost:8000",  # Your FastAPI backend (for direct testing)
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("LOG_LEVEL", mode="before")
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Use one of {valid_levels}.")
        return v.upper()

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
