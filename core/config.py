"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/invoice_reconciliation"

    # AI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    ai_enabled: bool = False

    # Application
    debug: bool = True
    log_level: str = "INFO"

    # Idempotency
    idempotency_key_header: str = "X-Idempotency-Key"


settings = Settings()

