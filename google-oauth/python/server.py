"""
Entry point. Creates the HTTP server, wires routes, and starts listening.
"""

import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from auth.google import GoogleAuth
from auth.dummy import DummyAuth
from pages.home import home_page
from session.middleware import get_session
from session.store import SessionStore

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _check_env() -> None:
    missing = [k for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET") if not os.environ.get(k)]
    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)


def _load_env(path: str = ".env") -> None:
    """Loads key=value pairs from a .env file into os.environ."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def make_handler(store: SessionStore, auth: GoogleAuth, dummy: DummyAuth) -> type[BaseHTTPRequestHandler]:
    """Returns a request handler class closed over the store and auth objects."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            logger.info("GET %s", path)

            if path == "/":
                session = get_session(self, store)
                home_page(self, session.user if session else None)

            elif path == "/auth/login":
                auth.handle_login(self)

            elif path == "/auth/callback":
                auth.handle_callback(self)

            elif path == "/auth/logout":
                auth.handle_logout(self)

            elif path == "/auth/dummy":
                dummy.handle_login(self)

            elif path == "/auth/dummy/list":
                dummy.handle_list(self)

            else:
                logger.debug("404 for path: %s", path)
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found.")

        def log_message(self, format: str, *args: object) -> None:
            # Suppress the default BaseHTTPRequestHandler access log;
            # we use our own structured logging above.
            pass

    return Handler


def main() -> None:
    _load_env()
    _check_env()

    host = os.environ.get("HOST", "localhost")
    port = int(os.environ.get("PORT", "3000"))
    base_url = os.environ.get("BASE_URL", f"http://{host}:{port}")

    store = SessionStore()
    auth = GoogleAuth(store, callback_url=f"{base_url}/auth/callback")
    dummy = DummyAuth(store)
    handler_class = make_handler(store, auth, dummy)

    server = HTTPServer((host, port), handler_class)
    logger.info("Server running at %s", base_url)
    if dummy.enabled:
        logger.info("Dummy login list: %s/auth/dummy/list", base_url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
