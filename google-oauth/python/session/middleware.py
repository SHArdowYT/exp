import logging
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from typing import Optional

from session.store import SessionStore
from types_sha import Session

logger = logging.getLogger(__name__)

COOKIE_NAME = "session_id"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60


def parse_session_cookie(handler: BaseHTTPRequestHandler) -> Optional[str]:
    """Returns the session ID from the Cookie header, or None."""
    raw = handler.headers.get("Cookie", "")
    cookie: SimpleCookie = SimpleCookie()
    cookie.load(raw)
    morsel = cookie.get(COOKIE_NAME)
    return morsel.value if morsel else None


def get_session(handler: BaseHTTPRequestHandler, store: SessionStore) -> Optional[Session]:
    """Looks up and returns the current session, or None."""
    session_id = parse_session_cookie(handler)
    if not session_id:
        return None
    session = store.get(session_id)
    if session:
        logger.debug("Session resolved for user %s.", session.user.name)
    return session


def set_session_cookie(handler: BaseHTTPRequestHandler, session_id: str) -> None:
    handler.send_header(
        "Set-Cookie",
        f"{COOKIE_NAME}={session_id}; HttpOnly; SameSite=Lax; Path=/; Max-Age={COOKIE_MAX_AGE}",
    )


def clear_session_cookie(handler: BaseHTTPRequestHandler) -> None:
    handler.send_header(
        "Set-Cookie",
        f"{COOKIE_NAME}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0",
    )
