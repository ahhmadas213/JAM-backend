# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import HttpUrl, field_validator, Field
from typing import List

class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "JAM (Just A Minute)"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Server configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = False  # Default to False for safety
    WORKERS_COUNT: int = 1

    # Database
    DATABASE_URL: str  # No default; must be set
    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # JWT and Authentication settings
    SECRET_KEY: str  # No default - must be set in .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_CONFIG: dict = Field(
        default={
            "httponly": True,
            "secure": True,
            "samesite": "lax",
            "max_age": 604800  # 7 days
        },
        description="Cookie configuration settings"
    )
    
    # CORS
    BACKEND_CORS_ORIGINS: List[HttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @field_validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Use one of {valid_levels}.")
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()