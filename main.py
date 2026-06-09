"""
Give Space — Main Entry Point
Mobile application that allows one device (Mobile A) to request and utilize
the storage space of another device (Mobile B) over a network.

Usage:
    python main.py          # Run the app
"""

import os
import sys
import logging

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

# Suppress verbose Kivy logs
logging.getLogger("kivy").setLevel(logging.WARNING)
logging.getLogger("kivy.factory").setLevel(logging.WARNING)

from src.app import GiveSpaceApp


def main():
    """Application entry point."""
    app = GiveSpaceApp()
    try:
        app.run()
    except KeyboardInterrupt:
        logging.info("Application terminated by user")
    except Exception as e:
        logging.exception("Application crashed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()