"""
Give Space — Storage Manager
Handles quota enforcement, file CRUD operations, and space tracking
for the allocated storage on Mobile B.
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger("GiveSpace.Storage")

METADATA_FILE = ".givspace_meta.json"


class StorageManager:
    """
    Manages the allocated storage space for remote devices.
    Tracks quota usage and provides file operations within the quota.
    """

    def __init__(self, storage_path: str, allocated_bytes: int = 0):
        self._storage_path = storage_path
        self._allocated_bytes = allocated_bytes
        os.makedirs(self._storage_path, exist_ok=True)

    @property
    def storage_path(self) -> str:
        return self._storage_path

    @property
    def allocated_bytes(self) -> int:
        return self._allocated_bytes

    @allocated_bytes.setter
    def allocated_bytes(self, value: int):
        self._allocated_bytes = max(0, value)

    def get_used_bytes(self) -> int:
        """Calculate total bytes used by files in the allocated space."""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(self._storage_path):
                # Skip metadata file
                if METADATA_FILE in filenames:
                    filenames = [f for f in filenames if f != METADATA_FILE]
                for f in filenames:
                    try:
                        fp = os.path.join(dirpath, f)
                        total += os.path.getsize(fp)
                    except OSError:
                        continue
        except OSError:
            pass
        return total

    def get_available_bytes(self) -> int:
        """Get remaining bytes in the allocated space."""
        return max(0, self._allocated_bytes - self.get_used_bytes())

    def get_stats(self) -> dict:
        """Return full storage statistics."""
        used = self.get_used_bytes()
        return {
            "allocated": self._allocated_bytes,
            "used": used,
            "available": self.get_available_bytes(),
            "usage_percent": (
                (used / self._allocated_bytes * 100)
                if self._allocated_bytes > 0
                else 0.0
            ),
            "storage_path": self._storage_path,
        }

    def has_space_for(self, bytes_needed: int) -> bool:
        """Check if there's enough space for a file of the given size."""
        return bytes_needed <= self.get_available_bytes()

    def format_bytes(self, byte_count: int) -> str:
        """Human-readable byte formatting."""
        if byte_count < 1024:
            return f"{byte_count} B"
        elif byte_count < 1024**2:
            return f"{byte_count / 1024:.1f} KB"
        elif byte_count < 1024**3:
            return f"{byte_count / 1024**2:.1f} MB"
        else:
            return f"{byte_count / 1024**3:.2f} GB"

    def resolve_path(self, relative_path: str) -> str:
        """
        Resolve a relative path within the storage root safely.
        Raises PermissionError on path traversal attempt.
        """
        base = os.path.realpath(self._storage_path)
        requested = os.path.realpath(
            os.path.join(self._storage_path, relative_path.lstrip("/"))
        )
        if not requested.startswith(base + os.sep) and requested != base:
            raise PermissionError("Path traversal detected")
        return requested

    def save_user_preferences(self, prefs: dict):
        """Save user preferences to internal metadata store."""
        meta_path = os.path.join(self._storage_path, METADATA_FILE)
        try:
            existing = {}
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    existing = json.load(f)
            existing.update(prefs)
            with open(meta_path, "w") as f:
                json.dump(existing, f, indent=2)
        except IOError:
            pass

    def load_user_preferences(self) -> dict:
        """Load user preferences from internal metadata store."""
        meta_path = os.path.join(self._storage_path, METADATA_FILE)
        try:
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return {}

    def get_folder_size(self, folder_path: str) -> int:
        """Get total size of all files in a specific folder within storage."""
        target = self.resolve_path(folder_path)
        if not os.path.exists(target):
            return 0
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(target):
                for f in filenames:
                    try:
                        total += os.path.getsize(os.path.join(dirpath, f))
                    except OSError:
                        continue
        except OSError:
            pass
        return total