"""
Dummy authentication for testing.

Only active when ``enable_dummy_auth`` is ``True`` in the application
settings. Never enable this in production -- it bypasses all authentication.

This module contains only dummy auth logic. Route registration is handled
in ``main.py``, keeping framework wiring separate from authentication logic.
"""

import json
import logging
import uuid
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from config import Settings
from models import Session, User
from session.middleware import set_session_cookie
from session.store import AbstractSessionStore

__all__ = ["DummyAuth"]

logger = logging.getLogger(__name__)


def _load_users_from_file(users_file: Path) -> dict[str, User]:
    """
    Loads dummy users from a JSON file.

    Returns an empty dict (with a warning) if the file is missing or malformed,
    so the server still starts cleanly without dummy users available.
    """
    try:
        raw_entries: list[dict[str, str]] = json.loads(users_file.read_text(encoding="utf-8"))
        return {entry["id"]: User(**entry) for entry in raw_entries}
    except (OSError, ValueError, KeyError):
        logger.warning("Could not load dummy users from %s -- dummy login unavailable.", users_file)
        return {}


class DummyAuth:
    """
    Provides instant sign-in as a pre-defined test user.

    Exposes two async handler methods -- ``handle_login`` and ``handle_list``
    -- which are registered as routes in ``main.py``. This class contains only
    dummy auth logic; it has no knowledge of URL paths or FastAPI's routing API.

    Users are loaded from the file path given in ``settings.dummy_users_file``.
    """

    def __init__(
        self,
        store: AbstractSessionStore,
        settings: Settings,
        templates: Jinja2Templates,
    ) -> None:
        self._store: AbstractSessionStore = store
        self._settings: Settings = settings
        self._enabled: bool = settings.enable_dummy_auth
        self._templates: Jinja2Templates = templates
        self._users: dict[str, User] = (
            _load_users_from_file(settings.dummy_users_file) if self._enabled else {}
        )
        if self._enabled:
            logger.info(
                "Dummy auth enabled -- %d user(s) available: %s.",
                len(self._users),
                ", ".join(self._users),
            )

    @property
    def enabled(self) -> bool:
        """True when dummy auth is active."""
        return self._enabled

    async def handle_login(self, request: Request) -> Response:
        """Signs in immediately as the test user matching ``?id=<id>``."""
        if not self._enabled:
            return HTMLResponse(
                "Dummy auth is not enabled. Set ENABLE_DUMMY_AUTH=true.",
                status_code=403,
            )

        user_id: str = request.query_params.get("id", "")
        user: User | None = self._users.get(user_id)

        if user is None:
            available_ids: str = ", ".join(self._users)
            return HTMLResponse(
                f"Unknown test user id \"{user_id}\". Available: {available_ids}",
                status_code=404,
            )

        session: Session = Session(id=str(uuid.uuid4()), user=user)
        self._store.save(session)
        logger.info("Dummy sign-in as %s (%s).", user.name, user.id)

        redirect_response: RedirectResponse = RedirectResponse("/", status_code=302)
        set_session_cookie(redirect_response, session.id, self._settings)
        return redirect_response

    async def handle_list(self, request: Request) -> Response:
        """Returns an HTML page listing all available test users."""
        if not self._enabled:
            return HTMLResponse("Dummy auth is not enabled.", status_code=403)

        return self._templates.TemplateResponse(
            request,
            "dummy_list.html",
            {"users": list(self._users.values())},
        )
