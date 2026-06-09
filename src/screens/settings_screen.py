"""
Give Space — Settings Screen
- Mobile B: Configure storage allocation, start/stop server
- Mobile A: View pairing info, privacy settings
"""

import logging
import os
from typing import Optional

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRectangleFlatButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import MDSlider
from kivymd.uix.switch import MDSwitch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.toolbar import MDTopAppBar

from src.network.server import FileServer
from src.storage.manager import StorageManager
from src.storage.sync import MemorySync
from src.network.pairing import PairingManager

logger = logging.getLogger("GiveSpace.Settings")

DEFAULT_STORAGE_PATH = "GiveSpace_Storage"
DEFAULT_ALLOCATED_MB = 1024  # 1 GB


class SettingsScreen(MDScreen):
    """
    Settings screen that adapts based on device role:
    - Mobile B: Storage allocation slider, server controls, sync toggle
    - Mobile A: Connected devices list, privacy settings
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._role: Optional[str] = None
        self._dialog: Optional[MDDialog] = None
        self._server: Optional[FileServer] = None
        self._storage_manager: Optional[StorageManager] = None
        self._memory_sync: Optional[MemorySync] = None
        self._pairing_manager = PairingManager()

    def on_enter(self):
        """Setup UI based on role."""
        app = MDApp.get_running_app()
        if app:
            self._role = app.get_role()

        if self._role == "mobile_b":
            self._setup_server_settings()
        else:
            self._setup_client_settings()

    def _setup_server_settings(self):
        """Mobile B: Show server configuration UI."""
        # Show server settings, hide client settings
        server_box = self.ids.get("server_settings_box")
        client_box = self.ids.get("client_settings_box")
        if server_box:
            server_box.opacity = 1
            server_box.disabled = False
        if client_box:
            client_box.opacity = 0
            client_box.disabled = True

        app = MDApp.get_running_app()
        if app:
            self._storage_manager = app.get_storage_manager()
            self._server = app.get_server()
            self._memory_sync = app.get_memory_sync()

            if self._storage_manager:
                self._update_storage_display()

    def _setup_client_settings(self):
        """Mobile A: Show client configuration UI."""
        server_box = self.ids.get("server_settings_box")
        client_box = self.ids.get("client_settings_box")
        if server_box:
            server_box.opacity = 0
            server_box.disabled = True
        if client_box:
            client_box.opacity = 1
            client_box.disabled = False

        # Show paired devices
        self._update_paired_devices()

    def _update_storage_display(self):
        """Update storage allocation display."""
        if not self._storage_manager:
            return

        stats = self._storage_manager.get_stats()
        slider = self.ids.get("storage_slider")
        if slider:
            # Slider value in MB
            slider.min = 128
            slider.max = 32768  # 32 GB max
            current_mb = stats["allocated"] // (1024 * 1024)
            slider.value = max(128, min(current_mb, 32768))

        self._update_storage_labels(stats["allocated"])

    def _update_storage_labels(self, allocated_bytes: int):
        """Update the storage amount labels."""
        allocated_mb = allocated_bytes // (1024 * 1024)
        value_label = self.ids.get("storage_value_label")
        if value_label:
            if allocated_mb >= 1024:
                value_label.text = f"{allocated_mb / 1024:.1f} GB"
            else:
                value_label.text = f"{allocated_mb} MB"

    def on_storage_slider_value(self, slider_instance, value: float):
        """Called when the storage slider value changes."""
        if self._storage_manager:
            allocated_bytes = int(value) * 1024 * 1024
            self._update_storage_labels(allocated_bytes)

    def apply_storage_allocation(self):
        """Apply the current slider value as the allocated storage."""
        slider = self.ids.get("storage_slider")
        if not slider or not self._storage_manager:
            return

        allocated_mb = int(slider.value)
        allocated_bytes = allocated_mb * 1024 * 1024
        self._storage_manager.allocated_bytes = allocated_bytes

        # Update server if running
        if self._server:
            self._server._allocated_bytes = allocated_bytes

        # Save preference
        self._storage_manager.save_user_preferences(
            {"allocated_mb": allocated_mb}
        )

        # Sync storage stats
        if self._memory_sync:
            self._memory_sync.sync_now()

        self._show_info(
            f"Storage allocation set to {allocated_mb} MB ({allocated_mb / 1024:.1f} GB)"
        )

    def toggle_server(self, switch_instance, active: bool):
        """Start or stop the file server."""
        app = MDApp.get_running_app()
        if not app:
            return

        if active:
            # Start server
            storage_path = os.path.join(
                app.user_data_dir if hasattr(app, "user_data_dir") else ".", 
                DEFAULT_STORAGE_PATH
            )
            allocated_mb = DEFAULT_ALLOCATED_MB

            # Load saved preferences
            if self._storage_manager:
                prefs = self._storage_manager.load_user_preferences()
                saved_mb = prefs.get("allocated_mb", DEFAULT_ALLOCATED_MB)
                allocated_mb = saved_mb

                # Update storage manager
                allocated_bytes = allocated_mb * 1024 * 1024
                self._storage_manager.allocated_bytes = allocated_bytes

            # Create and start server
            self._server = FileServer(
                storage_path=storage_path,
                allocated_bytes=allocated_bytes,
            )
            app.set_server(self._server)
            self._server.start()

            # Start memory sync
            self._memory_sync = MemorySync(self._storage_manager)
            self._memory_sync.set_on_update(
                lambda stats: self._server.send_storage_update()
            )
            self._memory_sync.start()
            app.set_memory_sync(self._memory_sync)

            status_label = self.ids.get("server_toggle_status")
            if status_label:
                status_label.text = "Server is RUNNING"
                status_label.theme_text_color = "Custom"
                status_label.text_color = (0.0, 0.7, 0.0, 1.0)

            self._show_info(f"Server started on port {self._server.port}")

        else:
            # Stop server
            if self._server:
                self._server.stop()
            if self._memory_sync:
                self._memory_sync.stop()

            status_label = self.ids.get("server_toggle_status")
            if status_label:
                status_label.text = "Server is STOPPED"
                status_label.theme_text_color = "Custom"
                status_label.text_color = (0.7, 0.0, 0.0, 1.0)

    def _update_paired_devices(self):
        """Update the list of paired devices for Mobile A."""
        paired_list = self.ids.get("paired_devices_list")
        if not paired_list:
            return

        paired_list.clear_widgets()
        devices = self._pairing_manager.get_paired_devices()

        if not devices:
            info_label = self.ids.get("paired_info_label")
            if info_label:
                info_label.text = "No paired devices yet. Go to Pairing screen."
            return

        for device in devices:
            device_name = device.get("device_name", "Unknown")
            device_ip = device.get("device_ip", "0.0.0.0")
            item_text = f"{device_name}\nIP: {device_ip}"

            btn = MDRectangleFlatButton(
                text=f"Unpair {device_ip}",
                size_hint_y=None,
                height=dp(48),
                on_release=lambda x, ip=device_ip: self._unpair_device(ip),
            )
            paired_list.add_widget(btn)

    def _unpair_device(self, device_ip: str):
        """Remove a paired device."""
        self._pairing_manager.remove_paired_device(device_ip)
        self._update_paired_devices()
        self._show_info(f"Device {device_ip} unpaired.")

    def navigate_to_pairing(self):
        """Navigate back to pairing screen."""
        app = MDApp.get_running_app()
        if app:
            app.switch_screen("pairing")

    def navigate_to_home(self):
        """Navigate to home screen."""
        app = MDApp.get_running_app()
        if app:
            app.switch_screen("home")

    def _show_info(self, message: str):
        """Show an information dialog."""
        if self._dialog:
            self._dialog.dismiss()

        self._dialog = MDDialog(
            title="Settings",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self._dialog.dismiss() if self._dialog else None,
                ),
            ],
        )
        self._dialog.open()