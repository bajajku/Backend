"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Local testing mode - skips cloud dependencies
    local_mode: bool = False

    # LLM Provider: "openrouter" or "google"
    llm_provider: str = "openrouter"

    # API Keys
    openrouter_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    gcs_bucket_name: str = "doc-to-3d-models"

    # Optional - GCS credentials path
    google_application_credentials: Optional[str] = None

    # Local models path (used when local_mode=True)
    local_models_path: str = "local_models"

    # Optional with defaults
    max_file_size_mb: int = 50
    allowed_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    # LLM settings
    llm_model: str = "google/gemini-3-flash-preview"  # OpenRouter model format
    llm_temperature: float = 0.7
    llm_max_tokens: int = 16000  # Max output tokens (HTML generation needs ~8-12k)

    # TTS settings
    elevenlabs_voice_id: str = "EXAVITQu4vr4xnSDxMaL"  # Rachel voice

    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        """Return list of allowed CORS origins."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
