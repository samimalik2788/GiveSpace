"""
Give Space — Memory Synchronization Module
Handles automatic memory updates when Mobile B connects to a network.
Uses network listeners to detect connectivity changes and sync stats.
"""

import os
import socket
import threading
import logging
from typing import Callable, Optional

from src.storage.manager import StorageManager

logger = logging.getLogger("GiveSpace.Sync")

POLL_INTERVAL = 10.0  # seconds between network state checks


class MemorySync:
    """
    Monitors network connectivity and triggers storage stats updates
    to paired Mobile A devices whenever the network state changes.
    """

    def __init__(self, storage_manager: StorageManager):
        self._storage = storage_manager
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_update: Optional[Callable[[dict], None]] = None
        self._last_network_state: Optional[bool] = None

    def set_on_update(self, callback: Callable[[dict], None]):
        """Set callback for when storage stats need to be sent."""
        self._on_update = callback

    def start(self):
        """Start monitoring for network changes."""
        if self._running:
            return
        self._running = True
        self._last_network_state = self._check_network()
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
        logger.info("MemorySync started")

    def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("MemorySync stopped")

    def sync_now(self):
        """Trigger an immediate storage stats update."""
        stats = self._storage.get_stats()
        if self._on_update:
            self._on_update(stats)
        return stats

    def _monitor(self):
        """Background loop that checks network state periodically."""
        while self._running:
            try:
                current_state = self._check_network()
                if current_state != self._last_network_state:
                    self._last_network_state = current_state
                    if current_state:
                        logger.info(
                            "Network became available — syncing storage stats"
                        )
                        self.sync_now()
                    else:
                        logger.info("Network became unavailable")
            except Exception:
                logger.exception("Error in sync monitor")

            # Sleep with early exit on stop
            for _ in range(int(POLL_INTERVAL * 2)):
                if not self._running:
                    return
                threading.Event().wait(0.5)

    @staticmethod
    def _check_network() -> bool:
        """
        Check if we have network connectivity.
        Uses a simple socket connection test.
        """
        try:
            # Try to resolve a common host — quick check
            socket.getaddrinfo("8.8.8.8", 53, socket.AF_INET)
            return True
        except OSError:
            return False

    @staticmethod
    def is_wifi_connected() -> bool:
        """
        Check if Wi-Fi is connected.
        On Android this would use Android APIs.
        On desktop, we fall back to checking if any network interface is up.
        """
        try:
            interfaces = socket.if_nameindex()
            return len(interfaces) > 1  # More than just loopback
        except (AttributeError, OSError):
            # Fallback on platforms without if_nameindex
            try:
                # Try connecting to a reliable host
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                result = sock.connect_ex(("8.8.8.8", 53))
                sock.close()
                return result == 0
            except OSError:
                return False