"""
Session middleware helpers.

Cookie reading and writing for the session layer. These are thin helpers
over FastAPI's ``Request``/``Response`` objects; they do not constitute
middleware in the ASGI sense.

All cookie parameters (name, TTL) are sourced from ``Settings`` so they
can be adjusted without code changes.
"""

import logging

from fastapi import Request, Response

from config import Settings
from models import Session
from session.store import AbstractSessionStore

__all__ = ["clear_session_cookie", "get_session", "set_session_cookie"]

logger = logging.getLogger(__name__)


def get_session(request: Request, store: AbstractSessionStore, settings: Settings) -> Session | None:
    """
    Resolves the current session from the request cookie.

    Returns ``None`` if no cookie is present or the session has expired.
    """
    session_id: str | None = request.cookies.get(settings.cookie_name)
    if not session_id:
        return None
    session: Session | None = store.get(session_id)
    if session:
        logger.debug("Session resolved for %s.", session.user.name)
    return session


def set_session_cookie(response: Response, session_id: str, settings: Settings) -> None:
    """Writes the session cookie to the response."""
    response.set_cookie(
        key=settings.cookie_name,
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    """Removes the session cookie from the response."""
    response.delete_cookie(key=settings.cookie_name, httponly=True, samesite="lax")
