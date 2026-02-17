"""Session management for uploaded Spotify data.

In serverless deployments, application state is not shared across instances.
This module provides session-based state management using secure cookies to
track which user's data should be loaded.
"""

import logging
import os
import secrets
import sys
from pathlib import Path

from itsdangerous import BadSignature, URLSafeSerializer

logger = logging.getLogger(__name__)

# Secret key for signing session cookies
# IMPORTANT: In production/serverless environments, SESSION_SECRET_KEY MUST be set
# as an environment variable to ensure consistency across all instances.
# Without this, different instances will have different keys, causing
# session cookies to be invalid across instances.
SECRET_KEY = os.environ.get("SESSION_SECRET_KEY")
if not SECRET_KEY:
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        logger.error(
            "SESSION_SECRET_KEY environment variable is required in serverless deployments!"
        )
        sys.exit(1)
    else:
        # Local development fallback
        SECRET_KEY = secrets.token_urlsafe(32)
        logger.warning(
            "Using randomly generated SESSION_SECRET_KEY. Set SESSION_SECRET_KEY "
            "environment variable for production use."
        )

# Session serializer for secure cookie signing
serializer = URLSafeSerializer(SECRET_KEY)


class SessionManager:
    """Manages user sessions and their associated data directories."""

    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def create_session(self, data_dir: Path, extract_root: Path | None = None) -> str:
        """Create a new session and associate it with a data directory.

        Args:
            data_dir: Directory containing the Spotify JSON files.
            extract_root: Top-level temp directory to clean up (defaults to data_dir).

        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)
        self._sessions[session_id] = {
            "data_dir": data_dir,
            "extract_root": extract_root or data_dir,
        }
        logger.info("Created session %s for data directory %s", session_id, data_dir)
        return session_id

    def get_session_data(self, session_id: str) -> dict | None:
        """Get the session data for a given session ID.

        Args:
            session_id: The session identifier

        Returns:
            Session data dictionary or None if not found
        """
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its associated data.

        Args:
            session_id: The session identifier

        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self._sessions:
            logger.info("Deleting session %s", session_id)
            del self._sessions[session_id]
            return True
        return False

    def get_all_session_ids(self) -> list[str]:
        """Get all active session IDs.

        Returns:
            List of session IDs
        """
        return list(self._sessions.keys())

    def cleanup_all_sessions(self):
        """Clean up all sessions. Called during server shutdown."""
        logger.info("Cleaning up all sessions")
        self._sessions.clear()


# Global session manager instance
session_manager = SessionManager()


def sign_session_id(session_id: str) -> str:
    """Sign a session ID for secure cookie storage.

    Args:
        session_id: The session identifier

    Returns:
        Signed session token
    """
    return serializer.dumps(session_id)


def verify_session_id(signed_token: str) -> str | None:
    """Verify and extract session ID from a signed token.

    Args:
        signed_token: The signed session token

    Returns:
        Session ID if valid, None otherwise
    """
    try:
        return serializer.loads(signed_token)
    except BadSignature:
        logger.warning("Invalid session token signature")
        return None
