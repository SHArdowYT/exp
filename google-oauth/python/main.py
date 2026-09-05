"""
Application entry point.

This module is responsible for:
  - Creating the FastAPI application
  - Wiring all routes (the only place URL paths are defined)
  - Mounting static files
  - Managing shared resource lifetimes via the lifespan context

No business logic lives here. Route handlers are thin callables that
delegate immediately to the appropriate domain class.

Run with:
    uvicorn main:app --host localhost --port 3000 --reload
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from auth.dummy import DummyAuth
from auth.google import GoogleAuth
from config import Settings, get_settings
from session.middleware import get_session
from session.store import AbstractSessionStore, JsonSessionStore

__all__ = ["app"]

_BASE_DIR: Path = Path(__file__).parent

logging.basicConfig(
    level=logging.getLevelName(get_settings().log_level),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class AppState:
    """
    Typed container for application-level shared resources.

    Stored on ``app.state`` so route handlers can access shared resources
    without relying on untyped ``Any`` attribute access.
    """

    settings: Settings
    session_store: AbstractSessionStore
    templates: Jinja2Templates
    google_auth: GoogleAuth
    dummy_auth: DummyAuth


@asynccontextmanager
async def _lifespan(fastapi_app: FastAPI) -> AsyncIterator[None]:
    """
    Initialises shared resources on startup and tears them down on shutdown.

    This is the single place where all domain objects are constructed and
    wired together. The rest of the application receives them via ``app.state``.
    """
    settings: Settings = get_settings()
    templates: Jinja2Templates = Jinja2Templates(directory=_BASE_DIR / "templates")
    session_store: AbstractSessionStore = JsonSessionStore(
        session_file=settings.session_file,
        ttl_seconds=settings.session_ttl_seconds,
    )
    google_auth: GoogleAuth = GoogleAuth(store=session_store, settings=settings)
    dummy_auth: DummyAuth = DummyAuth(store=session_store, settings=settings, templates=templates)

    fastapi_app.state.app_state = AppState(
        settings=settings,
        session_store=session_store,
        templates=templates,
        google_auth=google_auth,
        dummy_auth=dummy_auth,
    )

    logger.info("Server running at %s", settings.base_url)
    if settings.enable_dummy_auth:
        logger.info("Test user list: %s/auth/dummy/list", settings.base_url)

    yield

    logger.info("Shutting down.")


def _get_state(request: Request) -> AppState:
    """Returns the typed ``AppState`` from the request's app instance."""
    return request.app.state.app_state  # type: ignore[no-any-return]


app: FastAPI = FastAPI(lifespan=_lifespan, title="Google OAuth2 Sign-in")
app.mount("/static", StaticFiles(directory=_BASE_DIR / "static"), name="static")


# ------------------------------------------------------------------
# Routes -- this is the only place URL paths are defined
# ------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """
    Home page.

    Renders the signed-in profile view if a valid session cookie is present,
    otherwise renders the sign-in prompt.
    """
    state: AppState = _get_state(request)
    session = get_session(request, state.session_store, state.settings)

    if session:
        return state.templates.TemplateResponse(
            request,
            "home_signed_in.html",
            {"user": session.user},
        )
    return state.templates.TemplateResponse(request, "home_signed_out.html")


@app.get("/auth/login", response_class=HTMLResponse)
async def auth_login(request: Request) -> HTMLResponse:
    """Delegates to ``GoogleAuth.handle_login``."""
    state: AppState = _get_state(request)
    return await state.google_auth.handle_login()  # type: ignore[return-value]


@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(request: Request) -> HTMLResponse:
    """Delegates to ``GoogleAuth.handle_callback``."""
    state: AppState = _get_state(request)
    return await state.google_auth.handle_callback(request)  # type: ignore[return-value]


@app.get("/auth/logout", response_class=HTMLResponse)
async def auth_logout(request: Request) -> HTMLResponse:
    """Delegates to ``GoogleAuth.handle_logout``."""
    state: AppState = _get_state(request)
    return await state.google_auth.handle_logout(request)  # type: ignore[return-value]


@app.get("/auth/dummy", response_class=HTMLResponse)
async def auth_dummy_login(request: Request) -> HTMLResponse:
    """Delegates to ``DummyAuth.handle_login``."""
    state: AppState = _get_state(request)
    return await state.dummy_auth.handle_login(request)  # type: ignore[return-value]


@app.get("/auth/dummy/list", response_class=HTMLResponse)
async def auth_dummy_list(request: Request) -> HTMLResponse:
    """Delegates to ``DummyAuth.handle_list``."""
    state: AppState = _get_state(request)
    return await state.dummy_auth.handle_list(request)  # type: ignore[return-value]
