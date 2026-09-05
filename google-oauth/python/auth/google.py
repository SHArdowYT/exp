"""
Google OAuth2 authentication.

Implements the authorisation code flow with PKCE (S256) as required
by Google for web applications. Pending PKCE state is stored in memory
between the login redirect and the callback.

This module contains only OAuth2 logic. Route registration is handled
in ``main.py``, keeping framework wiring separate from authentication logic.
"""

import asyncio
import hashlib
import logging
import secrets
import uuid
from base64 import urlsafe_b64encode
from typing import Any

import httpx
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from google_auth_oauthlib.flow import Flow

from config import Settings
from models import Session, User
from session.middleware import clear_session_cookie, get_session, set_session_cookie
from session.store import AbstractSessionStore

__all__ = ["GoogleAuth"]

logger = logging.getLogger(__name__)

_GOOGLE_SCOPES: list[str] = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v2/userinfo"

_FlowConfig = dict[str, dict[str, str | list[str]]]


def _pkce_challenge(verifier: str) -> str:
    """Returns the S256 PKCE code challenge for a given plain verifier."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _build_flow(callback_url: str, client_id: str, client_secret: str) -> Flow:
    """Constructs a google-auth-oauthlib Flow for the web application type."""
    config: _FlowConfig = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [callback_url],
        }
    }
    return Flow.from_client_config(config, scopes=_GOOGLE_SCOPES, redirect_uri=callback_url)


def _user_from_userinfo(userinfo: dict[str, Any]) -> User:
    """Constructs a ``User`` from a Google userinfo response dict."""
    return User(
        id=str(userinfo.get("id") or uuid.uuid4()),
        email=str(userinfo.get("email", "")),
        name=str(userinfo.get("name", "")),
        picture=str(userinfo.get("picture", "")),
    )


class GoogleAuth:
    """
    Handles the Google OAuth2 sign-in flow.

    Exposes three async handler methods -- ``handle_login``, ``handle_callback``,
    and ``handle_logout`` -- which are registered as routes in ``main.py``.
    This class contains only OAuth2 logic; it has no knowledge of URL paths
    or FastAPI's routing API.

    Thread safety: ``_pending`` is mutated only within the async event loop
    (uvicorn is single-threaded by default), so no locking is needed. For
    multi-worker deployments, move pending state to a shared store (e.g. Redis)
    keyed by state token.
    """

    def __init__(self, store: AbstractSessionStore, settings: Settings) -> None:
        self._store: AbstractSessionStore = store
        self._settings: Settings = settings
        self._callback_url: str = f"{settings.base_url}/auth/callback"
        # Maps OAuth2 state token -> PKCE code verifier.
        # Bounded to settings.pkce_max_pending entries to prevent unbounded growth.
        self._pending: dict[str, str] = {}

    async def handle_login(self) -> Response:
        """Redirects the browser to Google's OAuth2 consent screen."""
        verifier: str = secrets.token_urlsafe(64)
        challenge: str = _pkce_challenge(verifier)
        state: str = secrets.token_urlsafe(16)

        while len(self._pending) >= self._settings.pkce_max_pending:
            self._pending.pop(next(iter(self._pending)))
        self._pending[state] = verifier

        flow: Flow = _build_flow(
            self._callback_url,
            self._settings.google_client_id,
            self._settings.google_client_secret,
        )
        authorisation_url: str
        authorisation_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="select_account",
            state=state,
            code_challenge=challenge,
            code_challenge_method="S256",
        )
        logger.info("Redirecting to Google login (state=%s).", state[:8])
        return RedirectResponse(authorisation_url)

    async def handle_callback(self, request: Request) -> Response:
        """
        Handles the redirect back from Google.

        Exchanges the authorisation code for an access token, fetches the
        user's profile, creates a session, and redirects to the home page.
        """
        authorisation_code: str | None = request.query_params.get("code")
        state: str = request.query_params.get("state", "")

        if not authorisation_code:
            logger.warning("OAuth2 callback missing code parameter.")
            return HTMLResponse("Missing OAuth2 code.", status_code=400)

        verifier: str | None = self._pending.pop(state, None)
        if verifier is None:
            logger.warning("OAuth2 callback: unknown or expired state=%s.", state[:8])
            return HTMLResponse(
                "Invalid or expired OAuth2 state. Please try signing in again.",
                status_code=400,
            )

        try:
            flow: Flow = _build_flow(
                self._callback_url,
                self._settings.google_client_id,
                self._settings.google_client_secret,
            )
            # flow.fetch_token is synchronous -- run in a thread to avoid blocking the event loop.
            await asyncio.to_thread(
                flow.fetch_token,
                code=authorisation_code,
                code_verifier=verifier,
            )
            access_token: str = str(flow.credentials.token)

            async with httpx.AsyncClient() as http_client:
                userinfo_response: httpx.Response = await http_client.get(
                    _USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=self._settings.userinfo_timeout_seconds,
                )
            userinfo_response.raise_for_status()
            userinfo: dict[str, Any] = userinfo_response.json()

            session: Session = Session(id=str(uuid.uuid4()), user=_user_from_userinfo(userinfo))
            self._store.save(session)

            redirect_response: RedirectResponse = RedirectResponse("/", status_code=302)
            set_session_cookie(redirect_response, session.id, self._settings)
            return redirect_response

        except (httpx.HTTPError, ValueError, KeyError):
            logger.exception("OAuth2 callback failed.")
            return HTMLResponse("Authentication failed.", status_code=500)

    async def handle_logout(self, request: Request) -> Response:
        """Deletes the current session and redirects to the home page."""
        session: Session | None = get_session(request, self._store, self._settings)
        if session:
            self._store.delete(session.id)
        redirect_response: RedirectResponse = RedirectResponse("/", status_code=302)
        clear_session_cookie(redirect_response, self._settings)
        return redirect_response
