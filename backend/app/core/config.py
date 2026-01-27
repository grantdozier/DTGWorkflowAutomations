from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "DTG Workflow Automations"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/dtg_workflows"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # AI APIs
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Google Cloud Document AI (optional)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_PROJECT_ID: Optional[str] = None
    GOOGLE_LOCATION: str = "us"
    GOOGLE_PROCESSOR_ID: Optional[str] = None

    # Document Parsing Strategy Toggles
    ENABLE_OPENAI_PARSING: bool = True
    ENABLE_DOCUMENT_AI_PARSING: bool = False
    ENABLE_CLAUDE_PARSING: bool = True
    ENABLE_TESSERACT_PARSING: bool = True

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # Email Service
    EMAIL_SERVICE: str = "sendgrid"  # sendgrid or smtp
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "quotes@yourdomain.com"
    SENDGRID_FROM_NAME: str = "DTG Workflow Automations"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
