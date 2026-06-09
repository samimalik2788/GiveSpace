"""
Give Space — Home Screen
- Mobile A: File manager interface for browsing remote storage
- Mobile B: Server dashboard showing connected clients and storage stats
"""

import logging
import os
from typing import Optional

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRectangleFlatButton, MDFloatingActionButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.switch import MDSwitch
from kivymd.uix.toolbar import MDTopAppBar

from src.network.client import FileClient
from src.encryption.crypto import FileCipher

logger = logging.getLogger("GiveSpace.Home")


class HomeScreen(MDScreen):
    """
    Main screen that adapts to the device role:
    - Mobile A: Full file manager with remote storage browsing
    - Mobile B: Server status dashboard
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._role: Optional[str] = None
        self._client: Optional[FileClient] = None
        self._cipher = FileCipher()
        self._current_path = "/"
        self._hide_mode = False
        self._dialog: Optional[MDDialog] = None
        self._file_cache: list[dict] = []

    def on_enter(self):
        """Setup UI based on role when screen becomes active."""
        app = MDApp.get_running_app()
        if app:
            self._role = app.get_role()

        if self._role == "mobile_b":
            self._setup_server_dashboard()
        else:
            self._setup_file_manager()

    def _setup_server_dashboard(self):
        """Mobile B: Show server status and connected clients."""
        # Hide file manager widgets, show server dashboard
        fm_box = self.ids.get("file_manager_box")
        dash_box = self.ids.get("dashboard_box")
        if fm_box:
            fm_box.opacity = 0
            fm_box.disabled = True
        if dash_box:
            dash_box.opacity = 1
            dash_box.disabled = False

        # Update server status
        app = MDApp.get_running_app()
        if app:
            server = app.get_server()
            if server:
                status_label = self.ids.get("server_status_label")
                if status_label:
                    status_label.text = (
                        "Server: Running" if server.is_running() else "Server: Stopped"
                    )
                port_label = self.ids.get("server_port_label")
                if port_label:
                    port_label.text = f"Port: {server.port}"

                # Update storage stats
                self._update_server_stats()

    def _update_server_stats(self):
        """Refresh storage statistics display for Mobile B."""
        app = MDApp.get_running_app()
        if app:
            storage = app.get_storage_manager()
            if storage:
                stats = storage.get_stats()
                # Update memory display labels
                memory_title = self.ids.get("memory_title")
                if memory_title:
                    memory_title.text = "Storage Allocation"

                allocated_label = self.ids.get("allocated_label")
                if allocated_label:
                    allocated_label.text = f"Allocated: {storage.format_bytes(stats['allocated'])}"

                used_label = self.ids.get("used_label")
                if used_label:
                    used_label.text = f"Used: {storage.format_bytes(stats['used'])}"

                available_label = self.ids.get("available_label")
                if available_label:
                    available_label.text = f"Available: {storage.format_bytes(stats['available'])}"

    def _setup_file_manager(self):
        """Mobile A: Show file manager for remote storage."""
        fm_box = self.ids.get("file_manager_box")
        dash_box = self.ids.get("dashboard_box")
        if fm_box:
            fm_box.opacity = 1
            fm_box.disabled = False
        if dash_box:
            dash_box.opacity = 0
            dash_box.disabled = True

        # Update toolbar title
        toolbar = self.ids.get("file_toolbar")
        if toolbar:
            toolbar.title = f"Give Space — {self._current_path}"

        # Connect to server if not connected
        app = MDApp.get_running_app()
        if app and not self._client:
            paired_ip = app.get_paired_ip()
            if paired_ip:
                self._client = FileClient()
                self._client.set_on_response(self._on_server_response)
                self._client.set_on_error(self._on_server_error)
                self._client.set_on_storage_update(self._on_storage_update)
                self._client.set_on_disconnected(self._on_disconnected)

                def connect_async():
                    self._client.connect(paired_ip)
                    Clock.schedule_once(lambda dt: self._refresh_file_list(), 0.5)

                import threading
                threading.Thread(target=connect_async, daemon=True).start()

        self._refresh_file_list()

    def _refresh_file_list(self):
        """Request directory listing from remote server."""
        if self._client and self._client.is_connected:
            self._client.list_directory(self._current_path)

    def _on_server_response(self, msg: dict):
        """Handle responses from the remote server."""
        msg_type = msg.get("type", "")
        payload = msg.get("payload", {})

        if msg_type.endswith("list_dir_resp"):
            entries = payload.get("entries", [])
            self._file_cache = entries
            Clock.schedule_once(lambda dt: self._populate_file_list(entries), 0)

    def _populate_file_list(self, entries: list[dict]):
        """Populate the file list UI with entries from server."""
        file_list = self.ids.get("file_list")
        if not file_list:
            return

        file_list.clear_widgets()

        # Add ".." for navigation
        if self._current_path != "/":
            item = OneLineIconListItem(text="..")
            icon = IconLeftWidget(icon="folder-upload")
            item.add_widget(icon)
            item.bind(on_release=lambda x: self._navigate_up())
            file_list.add_widget(item)

        for entry in entries:
            name = entry.get("name", "unknown")
            is_dir = entry.get("is_dir", False)
            size = entry.get("size", 0)

            icon_name = "folder" if is_dir else "file-outline"
            size_str = f"  [{self._format_size(size)}]" if not is_dir else ""

            item = OneLineIconListItem(text=f"{name}{size_str}")
            icon = IconLeftWidget(icon=icon_name)
            item.add_widget(icon)

            if is_dir:
                item.bind(
                    on_release=lambda x, n=name: self._navigate_into(n)
                )
            else:
                item.bind(on_release=lambda x, n=name: self._on_file_tap(n))

            file_list.add_widget(item)

    def _navigate_into(self, dir_name: str):
        """Navigate into a subdirectory."""
        if self._current_path == "/":
            self._current_path = f"/{dir_name}"
        else:
            self._current_path = f"{self._current_path}/{dir_name}"

        toolbar = self.ids.get("file_toolbar")
        if toolbar:
            toolbar.title = f"Give Space — {self._current_path}"
        self._refresh_file_list()

    def _navigate_up(self):
        """Navigate to parent directory."""
        if self._current_path == "/":
            return
        parent = os.path.dirname(self._current_path)
        self._current_path = parent if parent else "/"

        toolbar = self.ids.get("file_toolbar")
        if toolbar:
            toolbar.title = f"Give Space — {self._current_path}"
        self._refresh_file_list()

    def _on_file_tap(self, filename: str):
        """Handle tap on a file — show options dialog."""
        self._dialog = MDDialog(
            title=filename,
            text="Choose an action:",
            buttons=[
                MDRectangleFlatButton(
                    text="Download",
                    on_release=lambda x: self._download_file(filename),
                ),
                MDRectangleFlatButton(
                    text="Delete",
                    on_release=lambda x: self._delete_file(filename),
                ),
                MDRectangleFlatButton(
                    text="Cancel",
                    on_release=lambda x: self._dialog.dismiss() if self._dialog else None,
                ),
            ],
        )
        self._dialog.open()

    def _download_file(self, filename: str):
        """Download a file from remote storage."""
        if self._dialog:
            self._dialog.dismiss()

        remote_path = (
            f"{self._current_path}/{filename}"
            if self._current_path != "/"
            else f"/{filename}"
        )
        if self._client:
            self._client.download_file(remote_path)

    def _delete_file(self, filename: str):
        """Delete a file from remote storage."""
        if self._dialog:
            self._dialog.dismiss()

        remote_path = (
            f"{self._current_path}/{filename}"
            if self._current_path != "/"
            else f"/{filename}"
        )
        if self._client:
            self._client.delete_file(remote_path)
            Clock.schedule_once(lambda dt: self._refresh_file_list(), 0.3)

    def _on_server_error(self, error_msg: str):
        """Handle server errors."""
        logger.error("Server error: %s", error_msg)
        Clock.schedule_once(lambda dt: self._show_error(error_msg), 0)

    def _on_storage_update(self, stats: dict):
        """Handle real-time storage updates from server."""
        Clock.schedule_once(lambda dt: self._update_memory_display(stats), 0)

    def _update_memory_display(self, stats: dict):
        """Update the memory/usage display with fresh stats."""
        allocated = stats.get("allocated", 0)
        used = stats.get("used", 0)
        available = stats.get("available", 0)

        # Update memory labels if they exist
        memory_used = self.ids.get("memory_used")
        memory_available = self.ids.get("memory_available")
        if memory_used:
            memory_used.text = f"Used: {self._format_size(used)}"
        if memory_available:
            memory_available.text = f"Free: {self._format_size(available)}"

    def _on_disconnected(self, reason: str):
        """Handle disconnection."""
        logger.warning("Disconnected: %s", reason)
        self._show_error(f"Disconnected: {reason}")

    def toggle_hide_mode(self, switch_instance, active: bool):
        """Toggle Hide/Unhide mode for data privacy."""
        self._hide_mode = active
        status_label = self.ids.get("hide_status")
        if status_label:
            status_label.text = "🔒 Hidden" if active else "👁️ Visible"
            status_label.theme_text_color = "Custom"
            status_label.text_color = (
                (0.0, 0.7, 0.0, 1.0) if active else (0.5, 0.5, 0.5, 1.0)
            )

    def upload_file_dialog(self):
        """Show a dialog to upload a file to remote storage."""
        self._dialog = MDDialog(
            title="Upload File",
            type="custom",
            content_cls=MDBoxLayout(
                MDTextField(id="upload_path", hint_text="Local file path"),
                MDTextField(id="remote_name", hint_text="Remote filename"),
                orientation="vertical",
                spacing=dp(12),
                size_hint_y=None,
                height=dp(120),
            ),
            buttons=[
                MDRectangleFlatButton(
                    text="Upload",
                    on_release=lambda x: self._do_upload(),
                ),
                MDRectangleFlatButton(
                    text="Cancel",
                    on_release=lambda x: self._dialog.dismiss() if self._dialog else None,
                ),
            ],
        )
        self._dialog.open()

    def _do_upload(self):
        """Execute the file upload."""
        if not self._dialog:
            return

        content = self._dialog.content_cls
        local_path = content.ids.get("upload_path", {}).text if hasattr(content, "ids") else ""
        remote_name = content.ids.get("remote_name", {}).text if hasattr(content, "ids") else ""

        self._dialog.dismiss()

        if not local_path or not remote_name:
            self._show_error("Please fill in both fields.")
            return

        remote_path = (
            f"{self._current_path}/{remote_name}"
            if self._current_path != "/"
            else f"/{remote_name}"
        )

        # If hide mode is active, encrypt before upload
        if self._hide_mode and self._cipher.is_available:
            encrypted_path = local_path + ".encrypted"
            if self._cipher.encrypt_file(local_path, encrypted_path):
                local_path = encrypted_path
                remote_path += ".hidden"
            else:
                self._show_error("Encryption failed.")
                return

        if self._client:
            success = self._client.upload_file(local_path, remote_path)
            if success:
                Clock.schedule_once(lambda dt: self._refresh_file_list(), 0.3)

            # Clean up temp encrypted file
            if self._hide_mode and os.path.exists(local_path) and local_path.endswith(".encrypted"):
                try:
                    os.remove(local_path)
                except OSError:
                    pass

    def _show_error(self, message: str):
        """Show an error dialog."""
        if self._dialog:
            self._dialog.dismiss()

        self._dialog = MDDialog(
            title="Error",
            text=message,
            buttons=[
                MDRectangleFlatButton(
                    text="OK",
                    on_release=lambda x: self._dialog.dismiss() if self._dialog else None,
                ),
            ],
        )
        self._dialog.open()

    @staticmethod
    def _format_size(byte_count: int) -> str:
        """Format byte count to human-readable string."""
        if byte_count < 1024:
            return f"{byte_count} B"
        elif byte_count < 1024**2:
            return f"{byte_count / 1024:.1f} KB"
        elif byte_count < 1024**3:
            return f"{byte_count / 1024**2:.1f} MB"
        else:
            return f"{byte_count / 1024**3:.2f} GB"