"""
Dummy authentication for testing.

Only active when ENABLE_DUMMY_AUTH=true in the environment.
Visit /auth/dummy?id=<user-id> to sign in as a dummy user, or
/auth/dummy/list to see all available users with sign-in links.
Users are defined in dummy_users.json at the project root.
"""

import json
import logging
import os
import uuid
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from session.middleware import set_session_cookie
from session.store import SessionStore
from types_sha import Session, User

logger = logging.getLogger(__name__)

DUMMY_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "dummy_users.json")


def _load_dummy_users() -> dict[str, User]:
    try:
        with open(DUMMY_FILE, encoding="utf-8") as f:
            raw: list[dict] = json.load(f)
        return {u["id"]: User(**u) for u in raw}
    except Exception:
        logger.warning("Could not load %s — dummy login disabled.", DUMMY_FILE)
        return {}


class DummyAuth:
    """Provides dummy sign-in for testing purposes."""

    def __init__(self, store: SessionStore) -> None:
        self._store = store
        self._enabled = os.environ.get("ENABLE_DUMMY_AUTH") == "true"
        self._users: dict[str, User] = _load_dummy_users() if self._enabled else {}
        if self._enabled:
            logger.info(
                "Dummy auth enabled with %d user(s): %s",
                len(self._users),
                ", ".join(self._users.keys()),
            )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def handle_login(self, handler: BaseHTTPRequestHandler) -> None:
        """Signs in as the dummy user matching ?id=<id>."""
        if not self._enabled:
            handler.send_response(403)
            handler.end_headers()
            handler.wfile.write(b"Dummy auth is not enabled. Set ENABLE_DUMMY_AUTH=true.")
            return

        params = parse_qs(urlparse(handler.path).query)
        id_list = params.get("id", [])
        user_id = id_list[0] if id_list else ""
        user = self._users.get(user_id)

        if not user:
            available = ", ".join(self._users.keys())
            msg = f'Unknown dummy user id "{user_id}". Available: {available}'.encode()
            handler.send_response(404)
            handler.end_headers()
            handler.wfile.write(msg)
            return

        session = Session(id=str(uuid.uuid4()), user=user)
        self._store.set(session)
        logger.info("Dummy sign-in as %s (%s).", user.name, user.id)

        handler.send_response(302)
        set_session_cookie(handler, session.id)
        handler.send_header("Location", "/")
        handler.end_headers()

    def handle_list(self, handler: BaseHTTPRequestHandler) -> None:
        """Returns an HTML page listing all available dummy users."""
        if not self._enabled:
            handler.send_response(403)
            handler.end_headers()
            handler.wfile.write(b"Dummy auth is not enabled.")
            return

        items = "".join(
            f"""
        <li>
          <img src="{u.picture}" width="36" height="36" alt="">
          <div>
            <strong>{u.name}</strong><br>
            <small>{u.email}</small>
          </div>
          <a href="/auth/dummy?id={u.id}">Sign in</a>
        </li>"""
            for u in self._users.values()
        )

        body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dummy Login</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: system-ui, sans-serif;
      background: #f5f5f5;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .card {{
      background: #fff;
      border-radius: 10px;
      padding: 2rem 2.5rem;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      max-width: 400px;
      width: 100%;
    }}
    h1 {{ font-size: 1.2rem; margin-bottom: 0.25rem; }}
    p {{ color: #888; font-size: 0.85rem; margin-bottom: 1.5rem; }}
    ul {{ list-style: none; display: flex; flex-direction: column; gap: 0.75rem; }}
    li {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.6rem 0.75rem;
      border: 1px solid #eee;
      border-radius: 8px;
    }}
    li img {{ border-radius: 50%; flex-shrink: 0; }}
    li div {{ flex: 1; }}
    li small {{ color: #888; }}
    li a {{
      padding: 0.35rem 0.85rem;
      background: #222;
      color: #fff;
      text-decoration: none;
      border-radius: 5px;
      font-size: 0.85rem;
      white-space: nowrap;
    }}
    li a:hover {{ background: #444; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Dummy Login</h1>
    <p>Testing only. Users are defined in dummy_users.json.</p>
    <ul>{items}</ul>
  </div>
</body>
</html>""".encode()

        handler.send_response(200)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
