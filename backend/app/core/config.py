"""Application configuration."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "orbit-console-ryan-vo"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    secret_key: str = Field(default="dev-secret-change-in-production-32-chars-minimum", min_length=32)
    host: str = "127.0.0.1"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./orbit.db"

    # Security
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OIDC / Keycloak
    oidc_issuer_url: str = "http://localhost:8080/realms/orbit"
    oidc_client_id: str = "orbit-console"
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = "http://localhost:3000/callback"
    oidc_scopes: str = "openid profile email roles"

    # LLM
    llm_api_key: str = ""
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"

    # Telemetry
    metrics_enabled: bool = True
    otel_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "orbit-console"

    # Frontend URL for CORS
    frontend_url: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()