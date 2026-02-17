"""Application state management for uploaded Spotify data.

This module provides session-aware state management for serverless deployments
where application state is not shared across instances.
"""

import logging
import shutil
from pathlib import Path

from src.loaders import DataLoader
from src.session import session_manager

logger = logging.getLogger(__name__)


class AppState:
    """Session-aware container for uploaded datasets.

    In serverless environments, each request may hit a different instance.
    This class uses session IDs to track which data belongs to which user.
    """

    def __init__(self):
        # Cache of loaded DataLoaders by session ID
        self._loader_cache: dict[str, DataLoader] = {}

    def get_loader(self, session_id: str | None) -> DataLoader | None:
        """Get the DataLoader for a given session.

        Args:
            session_id: The user's session identifier

        Returns:
            DataLoader instance or None if no data loaded for this session
        """
        if not session_id:
            return None

        # Check cache first
        if session_id in self._loader_cache:
            return self._loader_cache[session_id]

        # Load from session data
        session_data = session_manager.get_session_data(session_id)
        if not session_data:
            return None

        data_dir = session_data["data_dir"]
        if not data_dir.exists():
            logger.warning("Data directory %s no longer exists for session %s", data_dir, session_id)
            return None

        # Create and cache loader
        loader = DataLoader(data_dir)
        self._loader_cache[session_id] = loader
        logger.info("Loaded data from %s for session %s", data_dir, session_id)
        return loader

    def create_session(self, data_dir: Path, extract_root: Path | None = None) -> str:
        """Create a new session with uploaded data.

        Args:
            data_dir: Directory containing the Spotify JSON files.
            extract_root: Top-level temp directory to clean up (defaults to data_dir).

        Returns:
            New session ID
        """
        session_id = session_manager.create_session(data_dir, extract_root)
        # Pre-load into cache
        loader = DataLoader(data_dir)
        self._loader_cache[session_id] = loader
        logger.info("Created session %s with data from %s", session_id, data_dir)
        return session_id

    def delete_session(self, session_id: str):
        """Delete a session and clean up its data.

        Args:
            session_id: The session identifier
        """
        logger.info("Deleting session %s", session_id)

        # Get session data before deletion
        session_data = session_manager.get_session_data(session_id)

        # Remove from cache
        if session_id in self._loader_cache:
            del self._loader_cache[session_id]

        # Delete from session manager
        session_manager.delete_session(session_id)

        # Clean up temp directory
        if session_data:
            extract_root = session_data.get("extract_root")
            if extract_root and extract_root.exists():
                logger.info("Cleaning up temp directory %s", extract_root)
                shutil.rmtree(extract_root)

    def cleanup_all_sessions(self):
        """Clean up all sessions and their temporary files.

        Called during server shutdown.
        """
        logger.info("Cleaning up all sessions")

        # Clean up all temp directories
        for session_id in list(session_manager._sessions.keys()):
            session_data = session_manager.get_session_data(session_id)
            if session_data:
                extract_root = session_data.get("extract_root")
                if extract_root and extract_root.exists():
                    logger.info("Cleaning up temp directory %s", extract_root)
                    shutil.rmtree(extract_root)

        # Clear caches
        self._loader_cache.clear()
        session_manager.cleanup_all_sessions()

    @property
    def is_loaded(self) -> bool:
        """Check if any data is loaded (deprecated, use session-based checks)."""
        # For backward compatibility during migration
        return len(self._loader_cache) > 0
