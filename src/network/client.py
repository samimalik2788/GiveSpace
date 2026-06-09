"""
Give Space — TCP Client (Mobile A)
Connects to Mobile B's FileServer and performs file operations.
Runs network operations on background threads.
"""

import os
import socket
import threading
import logging
from typing import Callable, Optional

from src.network.protocol import MessageProtocol, StreamDecoder

logger = logging.getLogger("GiveSpace.Client")

DEFAULT_PORT = 9876
BUFFER_SIZE = 65536
CONNECT_TIMEOUT = 5.0  # seconds


class FileClient:
    """
    Client that connects to a remote FileServer.
    Provides high-level methods for all file operations.
    Uses a callback pattern for asynchronous results.
    """

    def __init__(self):
        self._sock: Optional[socket.socket] = None
        self._decoder = StreamDecoder()
        self._lock = threading.Lock()
        self._connected = False
        self._server_ip: Optional[str] = None
        self._server_port: int = DEFAULT_PORT

        # Callbacks
        self._on_connected: Optional[Callable[[], None]] = None
        self._on_disconnected: Optional[Callable[[str], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
        self._on_response: Optional[Callable[[dict], None]] = None
        self._on_storage_update: Optional[Callable[[dict], None]] = None

        self._receive_thread: Optional[threading.Thread] = None
        self._running = False

    # --- Callback setters ---
    def set_on_connected(self, cb: Callable[[], None]):
        self._on_connected = cb

    def set_on_disconnected(self, cb: Callable[[str], None]):
        self._on_disconnected = cb

    def set_on_error(self, cb: Callable[[str], None]):
        self._on_error = cb

    def set_on_response(self, cb: Callable[[dict], None]):
        self._on_response = cb

    def set_on_storage_update(self, cb: Callable[[dict], None]):
        self._on_storage_update = cb

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def server_ip(self) -> Optional[str]:
        return self._server_ip

    def connect(self, host: str, port: int = DEFAULT_PORT) -> bool:
        """
        Connect to the remote server. Returns True on success.
        Starts a background receiver thread.
        """
        with self._lock:
            if self._connected:
                return True

            try:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.settimeout(CONNECT_TIMEOUT)
                self._sock.connect((host, port))
                self._sock.settimeout(None)  # Blocking mode for recv
                self._connected = True
                self._server_ip = host
                self._server_port = port
                self._decoder.reset()

                self._running = True
                self._receive_thread = threading.Thread(
                    target=self._receive_loop, daemon=True
                )
                self._receive_thread.start()

                logger.info("Connected to %s:%d", host, port)
                if self._on_connected:
                    self._on_connected()
                return True

            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                logger.error("Connection failed: %s", e)
                if self._on_error:
                    self._on_error(f"Connection failed: {e}")
                self._cleanup()
                return False

    def disconnect(self):
        """Disconnect from server."""
        self._running = False
        self._connected = False
        self._cleanup()
        if self._on_disconnected:
            self._on_disconnected("Disconnected")

    def _cleanup(self):
        """Close socket and clean up."""
        with self._lock:
            if self._sock:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None

    def _receive_loop(self):
        """Background thread that reads responses from server."""
        while self._running:
            try:
                if not self._sock:
                    break
                chunk = self._sock.recv(BUFFER_SIZE)
                if not chunk:
                    logger.info("Server closed connection")
                    self._connected = False
                    if self._on_disconnected:
                        self._on_disconnected("Server disconnected")
                    break
            except OSError:
                if self._running:
                    self._connected = False
                    if self._on_disconnected:
                        self._on_disconnected("Connection lost")
                break

            messages = self._decoder.feed(chunk)
            for msg in messages:
                self._dispatch(msg)

    def _dispatch(self, msg: dict):
        """Route incoming message to the appropriate callback."""
        msg_type = msg.get("type", "")
        payload = msg.get("payload", {})

        if msg_type == MessageProtocol.MSG_STORAGE_UPDATE:
            if self._on_storage_update:
                self._on_storage_update(payload)
        elif msg_type == MessageProtocol.MSG_ERROR:
            if self._on_error:
                self._on_error(payload.get("error", "Unknown error"))
        else:
            if self._on_response:
                self._on_response(msg)

    def _send_message(self, msg_type: str, payload: dict) -> bool:
        """Send a message to the server. Thread-safe."""
        with self._lock:
            if not self._sock or not self._connected:
                logger.warning("Cannot send — not connected")
                return False
            try:
                data = MessageProtocol.encode(msg_type, payload)
                self._sock.sendall(data)
                return True
            except OSError as e:
                logger.error("Send failed: %s", e)
                if self._on_error:
                    self._on_error(f"Send failed: {e}")
                return False

    # --- High-level API ---

    def list_directory(self, path: str = "/"):
        """Request directory listing."""
        self._send_message(MessageProtocol.MSG_LIST_DIR, {"path": path})

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a local file to the remote storage.
        Returns True if the file was read successfully.
        The actual upload result comes via callback.
        """
        try:
            with open(local_path, "rb") as f:
                data = f.read()
            payload = {
                "path": remote_path,
                "size": len(data),
                "data": data.hex(),
            }
            return self._send_message(MessageProtocol.MSG_UPLOAD_FILE, payload)
        except IOError as e:
            if self._on_error:
                self._on_error(f"Failed to read local file: {e}")
            return False

    def download_file(self, remote_path: str) -> bool:
        """Request a file download from remote. Result comes via callback."""
        return self._send_message(
            MessageProtocol.MSG_DOWNLOAD_FILE, {"path": remote_path}
        )

    def delete_file(self, remote_path: str) -> bool:
        """Request deletion of a remote file/directory."""
        return self._send_message(
            MessageProtocol.MSG_DELETE_FILE, {"path": remote_path}
        )

    def get_stats(self):
        """Request storage statistics."""
        return self._send_message(MessageProtocol.MSG_GET_STATS, {})

    def create_directory(self, remote_path: str) -> bool:
        """Request creation of a directory."""
        return self._send_message(
            MessageProtocol.MSG_CREATE_DIR, {"path": remote_path}
        )

    def rename(self, old_path: str, new_path: str) -> bool:
        """Request rename of a file/directory."""
        return self._send_message(
            MessageProtocol.MSG_RENAME_FILE,
            {"old_path": old_path, "new_path": new_path},
        )