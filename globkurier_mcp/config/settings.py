from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # GlobKurier API
    globkurier_api_base_url: str = "https://api.globkurier.pl"
    globkurier_portal_base_url: str = "https://www.globkurier.pl"
    globkurier_default_language: Literal["pl", "en"] = "pl"

    # MCP Server
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 9000
    mcp_transport: Literal["http", "sse", "stdio"] = "stdio"
    # Stateless HTTP: each request is independent, no SSE stream required.
    # Required when running behind a reverse proxy (nginx) that does not support
    # long-lived SSE connections. Safe to enable because all tools are request-response.
    mcp_stateless_http: bool = False

    # HTTP Client
    http_timeout: float = 10.0

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file_path: str | None = None  # If None, only console logging
    log_file_max_bytes: int = 10_485_760  # 10MB
    log_file_backup_count: int = 5
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_requests: bool = True  # Log HTTP requests/responses

    # Cache
    cache_countries_ttl_seconds: int = 604800  # 7 days in seconds (7 * 24 * 60 * 60)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
