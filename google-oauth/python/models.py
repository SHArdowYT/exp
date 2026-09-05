"""
Domain models.

Pydantic models used throughout the application. All models are frozen
(immutable) to prevent accidental mutation after construction.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field

__all__ = ["Session", "User"]


def _utcnow() -> datetime:
    """Returns the current UTC time as a timezone-aware datetime."""
    return datetime.now(tz=UTC)


class User(BaseModel):
    """A signed-in user, populated from the Google userinfo endpoint."""

    model_config = {"frozen": True}

    id: str
    email: str
    name: str
    picture: str


class Session(BaseModel):
    """An authenticated session, keyed by a random UUID."""

    model_config = {"frozen": True}

    id: str
    user: User
    created_at: datetime = Field(default_factory=_utcnow)

