"""
Session storage.

Provides an abstract base class and a concrete in-memory implementation
that flushes to a JSON file on every write. Swap in a different backend
(e.g. Redis, Postgres) by subclassing ``AbstractSessionStore``.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

from models import Session

__all__ = ["AbstractSessionStore", "JsonSessionStore"]

logger = logging.getLogger(__name__)


def _is_expired(session: Session, ttl_seconds: int) -> bool:
    """Returns True if the session is older than ``ttl_seconds``."""
    age: float = (datetime.now(tz=UTC) - session.created_at).total_seconds()
    return age > ttl_seconds


class AbstractSessionStore(ABC):
    """
    Interface for session storage backends.

    Consumers depend on this type, not on ``JsonSessionStore``, so that
    the backend can be swapped without touching any other code.
    """

    @abstractmethod
    def get(self, session_id: str) -> Session | None:
        """Returns the session for the given ID, or None if absent or expired."""

    @abstractmethod
    def save(self, session: Session) -> None:
        """Persists a session."""

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """Removes a session by ID. No-ops if the ID is not present."""


class JsonSessionStore(AbstractSessionStore):
    """
    In-memory session store backed by a JSON file.

    Sessions are kept in a ``dict`` at runtime and written to ``session_file``
    on every mutation so they survive process restarts. Expired sessions are
    pruned on startup and on access.
    """

    def __init__(self, session_file: Path, ttl_seconds: int) -> None:
        self._session_file: Path = session_file
        self._ttl_seconds: int = ttl_seconds
        self._sessions: dict[str, Session] = {}
        self._load()

    def get(self, session_id: str) -> Session | None:
        session: Session | None = self._sessions.get(session_id)
        if session is None:
            return None
        if _is_expired(session, self._ttl_seconds):
            logger.info("Session %s expired -- removing.", session_id[:8])
            self.delete(session_id)
            return None
        return session

    def save(self, session: Session) -> None:
        self._sessions[session.id] = session
        logger.info("Session created for %s (%s).", session.user.name, session.id[:8])
        self._flush()

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        logger.info("Session %s deleted.", session_id[:8])
        self._flush()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._session_file.exists():
            return
        try:
            raw_entries: list[dict[str, object]] = json.loads(self._session_file.read_text(encoding="utf-8"))
            loaded: int = 0
            expired: int = 0
            for raw_entry in raw_entries:
                session: Session = Session.model_validate(raw_entry)
                if _is_expired(session, self._ttl_seconds):
                    expired += 1
                else:
                    self._sessions[session.id] = session
                    loaded += 1
            logger.info("Loaded %d session(s), discarded %d expired.", loaded, expired)
        except (OSError, ValueError):
            logger.exception("Failed to load sessions from %s.", self._session_file)

    def _flush(self) -> None:
        try:
            serialised: list[dict[str, object]] = [
                json.loads(session.model_dump_json())
                for session in self._sessions.values()
            ]
            self._session_file.write_text(json.dumps(serialised, indent=4), encoding="utf-8")
        except OSError:
            logger.exception("Failed to flush sessions to %s.", self._session_file)
