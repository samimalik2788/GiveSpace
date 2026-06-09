"""
Give Space — Role Selection Screen
User chooses whether this device is Mobile A (client) or Mobile B (server).
"""

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRectangleFlatButton


class RoleScreen(MDScreen):
    """
    Screen where the user selects their device role.
    - Mobile A: Client that uses remote storage
    - Mobile B: Server that provides storage
    """

    def select_role_a(self):
        """This device will be Mobile A (storage consumer)."""
        app = MDApp.get_running_app()
        if app:
            app.set_role("mobile_a")
            app.switch_screen("pairing")

    def select_role_b(self):
        """This device will be Mobile B (storage provider)."""
        app = MDApp.get_running_app()
        if app:
            app.set_role("mobile_b")
            app.switch_screen("settings")