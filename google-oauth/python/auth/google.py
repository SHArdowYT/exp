import logging
import os
import uuid
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from google_auth_oauthlib.flow import Flow

from session.middleware import clear_session_cookie, get_session, set_session_cookie
from session.store import SessionStore
from types_sha import Session, User

logger = logging.getLogger(__name__)

SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email",
          "https://www.googleapis.com/auth/userinfo.profile"]

USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleAuth:
    """Manages the Google OAuth2 sign-in flow."""

    def __init__(self, store: SessionStore, callback_url: str) -> None:
        self._store = store
        self._callback_url = callback_url
        self._client_id = os.environ["GOOGLE_CLIENT_ID"]
        self._client_secret = os.environ["GOOGLE_CLIENT_SECRET"]

    def handle_login(self, handler: BaseHTTPRequestHandler) -> None:
        """Redirects the user to Google's consent screen."""
        flow = self._make_flow()
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="select_account",
        )
        logger.info("Redirecting to Google login.")
        handler.send_response(302)
        handler.send_header("Location", auth_url)
        handler.end_headers()

    def handle_callback(self, handler: BaseHTTPRequestHandler) -> None:
        """Exchanges the OAuth2 code for a session."""
        parsed = urlparse(handler.path)
        params = parse_qs(parsed.query)
        code_list = params.get("code")

        if not code_list:
            logger.warning("OAuth2 callback missing code parameter.")
            handler.send_response(400)
            handler.end_headers()
            handler.wfile.write(b"Missing OAuth2 code.")
            return

        code = code_list[0]

        try:
            flow = self._make_flow()
            flow.fetch_token(code=code)
            token = flow.credentials.token

            resp = requests.get(USERINFO_URL, headers={"Authorization": f"Bearer {token}"}, timeout=10)
            resp.raise_for_status()
            info = resp.json()

            session = Session(
                id=str(uuid.uuid4()),
                user=User(
                    id=info.get("id", str(uuid.uuid4())),
                    email=info.get("email", ""),
                    name=info.get("name", ""),
                    picture=info.get("picture", ""),
                ),
            )
            self._store.set(session)

            handler.send_response(302)
            set_session_cookie(handler, session.id)
            handler.send_header("Location", "/")
            handler.end_headers()

        except Exception:
            logger.exception("OAuth2 callback failed.")
            handler.send_response(500)
            handler.end_headers()
            handler.wfile.write(b"Authentication failed.")

    def handle_logout(self, handler: BaseHTTPRequestHandler) -> None:
        """Clears the session and redirects to the home page."""
        session = get_session(handler, self._store)
        if session:
            self._store.delete(session.id)
        handler.send_response(302)
        clear_session_cookie(handler)
        handler.send_header("Location", "/")
        handler.end_headers()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _make_flow(self) -> Flow:
        return Flow.from_client_config(
            {
                "web": {
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self._callback_url],
                }
            },
            scopes=SCOPES,
            redirect_uri=self._callback_url,
        )
