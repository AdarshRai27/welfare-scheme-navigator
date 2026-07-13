"""Session management module utilizing Redis with an in-memory fallback."""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages multi-turn user conversation states."""

    def __init__(self, redis_url: str) -> None:
        """Initialize Redis connection or configure fallback.

        Args:
            redis_url: Connection string for Redis service.
        """
        self.redis_url: str = redis_url
        self.client: Optional[Any] = None
        self._in_memory_db: Dict[str, str] = {}

        try:
            import redis

            self.client = redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            logger.info("Connected to Redis server successfully.")
        except Exception as err:
            logger.warning(
                f"Redis connection failed: {err}. Falling back to thread-local in-memory store."
            )
            self.client = None

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieve the persisted state data dictionary for a user.

        Args:
            session_id: Unique identifier for the user session.

        Returns:
            Dictionary representing session context or empty dict.
        """
        if self.client:
            try:
                raw_data = self.client.get(f"session:{session_id}")
                if raw_data:
                    return json.loads(raw_data)
            except Exception as err:
                logger.error(f"Failed to read session {session_id} from Redis: {err}")

        # Fallback path
        serialized = self._in_memory_db.get(session_id)
        if serialized:
            return json.loads(serialized)
        return {}

    async def save_session(
        self, session_id: str, state: Dict[str, Any], expiry_seconds: int = 3600
    ) -> None:
        """Persist or update state data dictionary for a user.

        Args:
            session_id: Unique identifier for the user session.
            state: Context data to persist.
            expiry_seconds: Session duration threshold.
        """
        serialized = json.dumps(state)
        if self.client:
            try:
                self.client.setex(
                    f"session:{session_id}", expiry_seconds, serialized
                )
                return
            except Exception as err:
                logger.error(f"Failed to write session {session_id} to Redis: {err}")

        # Fallback path
        self._in_memory_db[session_id] = serialized

    async def clear_session(self, session_id: str) -> None:
        """Purge and erase user state data from the store (Privacy Option A).

        Args:
            session_id: Unique identifier for the user session.
        """
        if self.client:
            try:
                self.client.delete(f"session:{session_id}")
                return
            except Exception as err:
                logger.error(f"Failed to delete session {session_id} from Redis: {err}")

        # Fallback path
        self._in_memory_db.pop(session_id, None)
