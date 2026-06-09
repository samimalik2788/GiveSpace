"""
Give Space — Main Application
KivyMD application class with screen management and global state.
"""

import os
import sys
import logging
from typing import Optional

from kivy.core.window import Window
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivy.lang import Builder

# Screen imports
from src.screens.splash_screen import SplashScreen
from src.screens.role_screen import RoleScreen
from src.screens.pairing_screen import PairingScreen
from src.screens.home_screen import HomeScreen
from src.screens.settings_screen import SettingsScreen

# Core services
from src.network.server import FileServer
from src.network.client import FileClient
from src.network.pairing import PairingManager
from src.storage.manager import StorageManager
from src.storage.sync import MemorySync

logger = logging.getLogger("GiveSpace.App")


class GiveSpaceApp(MDApp):
    """
    Main application class.
    Manages:
    - Screen navigation
    - Global device role (mobile_a / mobile_b)
    - Server instance (Mobile B)
    - Storage manager
    - Memory sync
    - Pairing state
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._role: Optional[str] = None  # "mobile_a" or "mobile_b"
        self._paired_ip: Optional[str] = None
        self._server: Optional[FileServer] = None
        self._storage_manager: Optional[StorageManager] = None
        self._memory_sync: Optional[MemorySync] = None
        self._pairing_manager = PairingManager()
        self._screen_manager: Optional[MDScreenManager] = None

    def build(self):
        """Build the application UI."""
        # Configure window for desktop testing
        if platform not in ("android", "ios"):
            Window.size = (400, 720)

        # Set theme
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.accent_palette = "Blue"
        self.theme_cls.material_style = "M3"
        self.theme_cls.primary_hue = "700"

        # Build the screen manager
        self._screen_manager = MDScreenManager()

        # Load KV files
        self._load_kv_files()

        # Create and add all screens
        self._screen_manager.add_widget(SplashScreen(name="splash"))
        self._screen_manager.add_widget(RoleScreen(name="role"))
        self._screen_manager.add_widget(PairingScreen(name="pairing"))
        self._screen_manager.add_widget(HomeScreen(name="home"))
        self._screen_manager.add_widget(SettingsScreen(name="settings"))

        return self._screen_manager

    def _load_kv_files(self):
        """Load all KV language UI definition files."""
        kv_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kv")
        kv_files = [
            "splash.kv",
            "role.kv",
            "pairing.kv",
            "home.kv",
            "settings.kv",
        ]

        for kv_file in kv_files:
            path = os.path.join(kv_dir, kv_file)
            if os.path.exists(path):
                Builder.load_file(path)
                logger.debug("Loaded KV: %s", kv_file)
            else:
                logger.warning("KV file not found: %s", path)

    def set_role(self, role: str):
        """Set the device role (mobile_a or mobile_b)."""
        if role not in ("mobile_a", "mobile_b"):
            raise ValueError(f"Invalid role: {role}")
        self._role = role
        logger.info("Device role set to: %s", role)

        # Initialize role-specific components
        if role == "mobile_b":
            data_dir = self.user_data_dir if hasattr(self, "user_data_dir") else "."
            storage_path = os.path.join(data_dir, "GiveSpace_Storage")
            self._storage_manager = StorageManager(storage_path)

    def get_role(self) -> Optional[str]:
        """Get the current device role."""
        return self._role

    def set_paired_ip(self, ip: str):
        """Store the IP of the paired device."""
        self._paired_ip = ip
        logger.info("Paired with IP: %s", ip)

    def get_paired_ip(self) -> Optional[str]:
        """Get the paired device IP."""
        return self._paired_ip

    def set_server(self, server: FileServer):
        """Set the active file server instance (Mobile B)."""
        self._server = server

    def get_server(self) -> Optional[FileServer]:
        """Get the active file server instance."""
        return self._server

    def get_storage_manager(self) -> Optional[StorageManager]:
        """Get the storage manager instance."""
        return self._storage_manager

    def set_memory_sync(self, sync: MemorySync):
        """Set the memory sync instance."""
        self._memory_sync = sync

    def get_memory_sync(self) -> Optional[MemorySync]:
        """Get the memory sync instance."""
        return self._memory_sync

    def switch_screen(self, screen_name: str):
        """Switch to a different screen by name."""
        if self._screen_manager and self._screen_manager.has_screen(screen_name):
            self._screen_manager.current = screen_name
            logger.debug("Switched to screen: %s", screen_name)
        else:
            logger.warning("Screen not found: %s", screen_name)

    def on_start(self):
        """Called after the app has started."""
        logger.info("GiveSpace app started (role: %s)", self._role)

    def on_stop(self):
        """Cleanup when the app is closing."""
        logger.info("Shutting down GiveSpace...")

        if self._server:
            self._server.stop()
        if self._memory_sync:
            self._memory_sync.stop()

        logger.info("GiveSpace shutdown complete")


if __name__ == "__main__":
    GiveSpaceApp().run()