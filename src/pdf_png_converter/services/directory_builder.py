"""Ensures output directories exist before PNG files are written."""

from pathlib import Path


class DirectoryBuilder:
    """Creates directories on demand, including all missing intermediate parents."""

    def ensure_directory_exists(self, directory: Path) -> None:
        """Create directory and all parents if they do not exist (idempotent)."""
        directory.mkdir(parents=True, exist_ok=True)
