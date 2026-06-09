"""
Give Space — Pairing Screen
Handles the 4-digit code pairing workflow:
- Mobile B generates and displays a code
- Mobile A enters the code to connect
"""

import socket
import threading
import logging
from typing import Optional

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRectangleFlatButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout

from src.network.pairing import generate_pairing_code, verify_pairing_code, PairingManager

logger = logging.getLogger("GiveSpace.Pairing")


class PairingScreen(MDScreen):
    """
    Pairing screen with two modes:
    1. Mobile A: Shows a text field for entering Mobile B's 4-digit code
    2. Mobile B: Generates and displays a 4-digit code for Mobile A to enter

    The pairing workflow:
    1. Mobile B generates a code and displays it + its IP
    2. Mobile A enters the code and Mobile B's IP
    3. Mobile B verifies the code and confirms pairing
    4. Both devices save the pairing info
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._role: Optional[str] = None
        self._current_code: Optional[str] = None
        self._pairing_manager = PairingManager()
        self._dialog: Optional[MDDialog] = None
        self._local_ip: Optional[str] = None

    def on_enter(self):
        """Called when screen becomes active. Determine role and setup UI."""
        app = MDApp.get_running_app()
        if app:
            self._role = app.get_role()
            self._local_ip = self._get_local_ip()

        if self._role == "mobile_b":
            self._setup_as_server()
        else:
            self._setup_as_client()

    def _get_local_ip(self) -> str:
        """Get the local IP address of this device."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.0)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "127.0.0.1"

    def _setup_as_server(self):
        """Mobile B: Generate code and display it."""
        self._current_code = generate_pairing_code()
        app = MDApp.get_running_app()

        if app:
            # Update the server display labels
            server_code_label = self.ids.get("server_code_label")
            if server_code_label:
                server_code_label.text = self._current_code

            server_ip_label = self.ids.get("server_ip_label")
            if server_ip_label:
                server_ip_label.text = f"Your IP: {self._local_ip}"

            # Hide client-side UI, show server-side
            client_box = self.ids.get("client_box")
            server_box = self.ids.get("server_box")
            if client_box:
                client_box.opacity = 0
                client_box.disabled = True
            if server_box:
                server_box.opacity = 1
                server_box.disabled = False

    def _setup_as_client(self):
        """Mobile A: Show code entry UI."""
        app = MDApp.get_running_app()

        if app:
            client_box = self.ids.get("client_box")
            server_box = self.ids.get("server_box")
            if client_box:
                client_box.opacity = 1
                client_box.disabled = False
            if server_box:
                server_box.opacity = 0
                server_box.disabled = True

    def submit_pairing_code(self):
        """
        Mobile A: Validate the entered code and IP, then attempt connection.
        """
        code_input = self.ids.get("code_input")
        ip_input = self.ids.get("ip_input")
        code = code_input.text.strip() if code_input else ""
        ip = ip_input.text.strip() if ip_input else ""

        if not code or len(code) != 4 or not code.isdigit():
            self._show_error("Please enter a valid 4-digit code.")
            return

        if not ip:
            self._show_error("Please enter the server IP address.")
            return

        # Connect on background thread
        threading.Thread(
            target=self._attempt_pairing,
            args=(code, ip),
            daemon=True,
        ).start()

    def _attempt_pairing(self, code: str, ip: str):
        """
        Background: Connect to server and attempt pairing.
        For now, we perform a direct TCP test to verify the server is reachable.
        The actual pairing verification happens between the two devices.
        """
        try:
            # Quick connectivity test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect((ip, 9876))
            sock.close()

            # Save paired device
            self._pairing_manager.add_paired_device(
                device_name=f"MobileB@{ip}",
                device_ip=ip,
                role="mobile_b",
            )

            app = MDApp.get_running_app()
            if app:
                app.set_paired_ip(ip)
                Clock.schedule_once(
                    lambda dt: app.switch_screen("home"), 0
                )

        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            error_msg = f"Connection failed: {e}"
            logger.error(error_msg)
            Clock.schedule_once(lambda dt: self._show_error(error_msg), 0)

    def regenerate_code(self):
        """Mobile B: Generate a new pairing code."""
        self._current_code = generate_pairing_code()
        server_code_label = self.ids.get("server_code_label")
        if server_code_label:
            server_code_label.text = self._current_code

    def _show_error(self, message: str):
        """Display an error dialog."""
        if self._dialog:
            self._dialog.dismiss()

        self._dialog = MDDialog(
            title="Pairing Error",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self._dialog.dismiss() if self._dialog else None,
                )
            ],
        )
        self._dialog.open()

    def skip_pairing(self):
        """Skip pairing and go directly to the home screen (for testing)."""
        app = MDApp.get_running_app()
        if app:
            Clock.schedule_once(lambda dt: app.switch_screen("home"), 0)