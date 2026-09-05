"""
Application configuration.

All settings are read from environment variables or a .env file.
Required variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) will cause
a startup error if absent.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "get_settings"]

_REPO_ROOT: Path = Path(__file__).parent.parent


class Settings(BaseSettings):
    """
    Validated application settings sourced from environment variables.

    Reads from a .env file in the same directory as this module if present.
    """

    google_client_id: str
    google_client_secret: str
    host: str = "localhost"
    port: int = 3000
    base_url: str = "http://localhost:3000"
    enable_dummy_auth: bool = False
    dummy_users_file: Path = _REPO_ROOT / "dummy_users.json"
    session_file: Path = Path("sessions.json")
    session_ttl_seconds: int = 7 * 24 * 60 * 60  # 7 days
    cookie_name: str = "session_id"
    pkce_max_pending: int = 256
    userinfo_timeout_seconds: float = 10.0
    log_level: str = "DEBUG"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns the cached application settings instance."""
    return Settings()  # type: ignore[call-arg]  # fields populated from env / .env file

