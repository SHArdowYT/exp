import json
import logging
import os
from time import time
from typing import Optional

from types_sha import Session, User

logger = logging.getLogger(__name__)

SESSION_FILE = "sessions.json"
SESSION_TTL = 7 * 24 * 60 * 60  # 7 days in seconds


class SessionStore:
    """
    Stores sessions in memory and flushes to disk on every write
    so sessions survive restarts.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._load()

    def get(self, session_id: str) -> Optional[Session]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if time() - session.created_at > SESSION_TTL:
            logger.info("Session %s expired, removing.", session_id[:8])
            self.delete(session_id)
            return None
        return session

    def set(self, session: Session) -> None:
        self._sessions[session.id] = session
        logger.info("Session created for user %s (%s).", session.user.name, session.id[:8])
        self._flush()

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        logger.info("Session %s deleted.", session_id[:8])
        self._flush()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not os.path.exists(SESSION_FILE):
            return
        try:
            with open(SESSION_FILE, encoding="utf-8") as f:
                raw: list[dict] = json.load(f)
            loaded = expired = 0
            for entry in raw:
                user = User(**entry["user"])
                session = Session(
                    id=entry["id"],
                    user=user,
                    created_at=entry["created_at"],
                )
                if time() - session.created_at <= SESSION_TTL:
                    self._sessions[session.id] = session
                    loaded += 1
                else:
                    expired += 1
            logger.info("Loaded %d session(s), discarded %d expired.", loaded, expired)
        except Exception:
            logger.exception("Failed to load sessions from disk.")

    def _flush(self) -> None:
        try:
            data = [
                {
                    "id": s.id,
                    "created_at": s.created_at,
                    "user": {
                        "id": s.user.id,
                        "email": s.user.email,
                        "name": s.user.name,
                        "picture": s.user.picture,
                    },
                }
                for s in self._sessions.values()
            ]
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            logger.exception("Failed to flush sessions to disk.")
