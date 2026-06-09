"""
Give Space — Splash Screen
Displays "M.S.U" centered on the screen upon app startup.
Auto-transitions to the Role Selection screen after 2.5 seconds.
"""

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel


class SplashScreen(MDScreen):
    """
    Initial splash screen showing "M.S.U" branding.
    Transitions to role selection after a short delay.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._scheduled = None

    def on_enter(self):
        """Called when the screen is entered. Start the transition timer."""
        self._scheduled = Clock.schedule_once(self._go_to_next, 2.5)

    def on_leave(self):
        """Clean up the timer if we leave early."""
        if self._scheduled:
            self._scheduled.cancel()
            self._scheduled = None

    def _go_to_next(self, dt):
        """Transition to the role selection screen."""
        app = MDApp.get_running_app()
        if app:
            app.switch_screen("role")