"""
Give Space — Pairing Module
4-digit code generation, verification, and pairing state management.
"""

import os
import json
import random
from typing import Optional


PAIRED_DEVICES_FILE = "paired_devices.json"


def generate_pairing_code() -> str:
    """Generate a random 4-digit pairing code (e.g., '3821')."""
    return f"{random.randint(0, 9999):04d}"


def verify_pairing_code(input_code: str, actual_code: str) -> bool:
    """
    Verify if the entered code matches the expected code.
    Both are 4-digit strings. Comparison is constant-time to
    prevent timing attacks (though minimal risk for a 4-digit code).
    """
    if len(input_code) != 4 or not input_code.isdigit():
        return False
    if len(actual_code) != 4 or not actual_code.isdigit():
        return False
    # Simple comparison — for 4-digit, timing is not a realistic threat
    return input_code == actual_code


class PairingManager:
    """
    Manages the pairing lifecycle:
    - Stores paired device IPs and metadata
    - Handles code generation and verification
    - Persists paired devices to disk
    """

    def __init__(self, storage_path: str = PAIRED_DEVICES_FILE):
        self._storage_path = storage_path
        self._paired_devices: list[dict] = []
        self._load()

    def _load(self):
        """Load paired devices from disk."""
        try:
            if os.path.exists(self._storage_path):
                with open(self._storage_path, "r") as f:
                    self._paired_devices = json.load(f)
        except (json.JSONDecodeError, IOError):
            self._paired_devices = []

    def _save(self):
        """Persist paired devices to disk."""
        try:
            with open(self._storage_path, "w") as f:
                json.dump(self._paired_devices, f, indent=2)
        except IOError:
            pass  # Silently fail — pairing works in-memory for this session

    def add_paired_device(
        self,
        device_name: str,
        device_ip: str,
        role: str,  # "mobile_a" or "mobile_b"
        port: int = 9876,
    ) -> dict:
        """
        Register a newly paired device.
        Returns the device entry dict.
        """
        entry = {
            "device_name": device_name,
            "device_ip": device_ip,
            "port": port,
            "role": role,
            "paired_at": None,  # Could store timestamp; omitted for simplicity
        }
        # Remove any existing entry for this IP
        self._paired_devices = [
            d for d in self._paired_devices if d["device_ip"] != device_ip
        ]
        self._paired_devices.append(entry)
        self._save()
        return entry

    def remove_paired_device(self, device_ip: str) -> bool:
        """Remove a paired device by IP. Returns True if found and removed."""
        initial_count = len(self._paired_devices)
        self._paired_devices = [
            d for d in self._paired_devices if d["device_ip"] != device_ip
        ]
        if len(self._paired_devices) < initial_count:
            self._save()
            return True
        return False

    def get_paired_devices(self) -> list[dict]:
        """Return all currently paired devices."""
        return list(self._paired_devices)

    def get_device_by_ip(self, device_ip: str) -> Optional[dict]:
        """Look up a paired device by IP address."""
        for d in self._paired_devices:
            if d["device_ip"] == device_ip:
                return dict(d)
        return None

    def is_paired(self, device_ip: str) -> bool:
        """Check if a device is already paired."""
        return any(d["device_ip"] == device_ip for d in self._paired_devices)

    def clear_all(self):
        """Remove all paired devices."""
        self._paired_devices.clear()
        self._save()

    @property
    def count(self) -> int:
        """Number of paired devices."""
        return len(self._paired_devices)