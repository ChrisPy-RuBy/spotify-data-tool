"""Application state management for uploaded Spotify data."""

import shutil
from pathlib import Path

from src.loaders import DataLoader


class AppState:
    """Mutable container for the currently loaded dataset."""

    def __init__(self):
        self.loader: DataLoader | None = None
        self._temp_dir: Path | None = None

    def load_from_directory(self, data_dir: Path, extract_root: Path | None = None):
        """Create a new DataLoader from an extracted data directory.

        Args:
            data_dir: Directory containing the Spotify JSON files.
            extract_root: Top-level temp directory to clean up (defaults to data_dir).
        """
        self._cleanup_temp()
        self._temp_dir = extract_root or data_dir
        self.loader = DataLoader(data_dir)

    def reset(self):
        """Clear the current dataset and clean up temporary files."""
        self._cleanup_temp()
        self.loader = None

    def _cleanup_temp(self):
        """Remove the temporary directory if it exists."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None

    @property
    def is_loaded(self) -> bool:
        return self.loader is not None
