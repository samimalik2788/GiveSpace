"""
Give Space — TCP Server (Mobile B)
Handles incoming file operations from paired Mobile A devices.
Runs on a background thread to keep the UI responsive.
"""

import os
import json
import socket
import threading
import logging
from typing import Callable, Optional

from src.network.protocol import MessageProtocol, StreamDecoder

logger = logging.getLogger("GiveSpace.Server")

DEFAULT_PORT = 9876
BUFFER_SIZE = 65536  # 64 KB chunks for file transfers


class FileServer:
    """
    TCP server that listens for connections from Mobile A devices.
    Handles file listing, upload, download, delete, and stats requests.
    """

    def __init__(
        self,
        storage_path: str,
        allocated_bytes: int,
        port: int = DEFAULT_PORT,
    ):
        self._storage_path = storage_path
        self._allocated_bytes = allocated_bytes
        self._port = port
        self._server_socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._clients: list[socket.socket] = []
        self._lock = threading.Lock()
        self._on_error: Optional[Callable[[str], None]] = None

        os.makedirs(self._storage_path, exist_ok=True)

    def set_error_handler(self, handler: Callable[[str], None]):
        self._on_error = handler

    @property
    def port(self) -> int:
        return self._port

    def start(self):
        """Start the server on a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Gracefully stop the server."""
        self._running = False
        with self._lock:
            for client in self._clients:
                try:
                    client.close()
                except OSError:
                    pass
            self._clients.clear()
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def is_running(self) -> bool:
        return self._running

    def _run(self):
        """Main server loop — runs in background thread."""
        try:
            self._server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            self._server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
            )
            self._server_socket.bind(("0.0.0.0", self._port))
            self._server_socket.listen(5)
            self._server_socket.settimeout(1.0)

            logger.info(
                "FileServer listening on port %d (path: %s)",
                self._port,
                self._storage_path,
            )

            while self._running:
                try:
                    client_sock, addr = self._server_socket.accept()
                    logger.info("New connection from %s:%d", addr[0], addr[1])
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_sock, addr),
                        daemon=True,
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
                except OSError:
                    if self._running:
                        logger.exception("Socket accept error")

        except Exception as e:
            logger.exception("Server failed to start")
            if self._on_error:
                self._on_error(str(e))
            self._running = False

    def _handle_client(self, client_sock: socket.socket, addr: tuple):
        """Handle a single client connection — processes messages."""
        decoder = StreamDecoder()
        with self._lock:
            self._clients.append(client_sock)

        try:
            while self._running:
                try:
                    chunk = client_sock.recv(BUFFER_SIZE)
                except (socket.timeout, BlockingIOError):
                    continue

                if not chunk:
                    break

                messages = decoder.feed(chunk)
                for msg in messages:
                    self._process_message(client_sock, msg)

        except (ConnectionResetError, ConnectionAbortedError, OSError):
            logger.info("Client %s disconnected", addr[0])
        finally:
            with self._lock:
                try:
                    self._clients.remove(client_sock)
                except ValueError:
                    pass
            try:
                client_sock.close()
            except OSError:
                pass

    def _process_message(self, client_sock: socket.socket, msg: dict):
        """Route a decoded message to the appropriate handler."""
        msg_type = msg.get("type", "")
        payload = msg.get("payload", {})

        handlers = {
            MessageProtocol.MSG_LIST_DIR: self._handle_list_dir,
            MessageProtocol.MSG_UPLOAD_FILE: self._handle_upload,
            MessageProtocol.MSG_DOWNLOAD_FILE: self._handle_download,
            MessageProtocol.MSG_DELETE_FILE: self._handle_delete,
            MessageProtocol.MSG_GET_STATS: self._handle_get_stats,
            MessageProtocol.MSG_CREATE_DIR: self._handle_create_dir,
            MessageProtocol.MSG_RENAME_FILE: self._handle_rename,
        }

        handler = handlers.get(msg_type)
        if handler:
            try:
                handler(client_sock, payload)
            except Exception as e:
                logger.exception("Handler error for %s", msg_type)
                self._send_error(client_sock, str(e))
        else:
            self._send_error(client_sock, f"Unknown message type: {msg_type}")

    def _send_response(self, client_sock: socket.socket, msg_type: str, payload: dict):
        """Send a response message to the client."""
        try:
            data = MessageProtocol.encode(msg_type, payload)
            client_sock.sendall(data)
        except OSError:
            pass

    def _send_error(self, client_sock: socket.socket, error_msg: str):
        """Send an error response."""
        self._send_response(
            client_sock, MessageProtocol.MSG_ERROR, {"error": error_msg}
        )

    def _safe_path(self, relative_path: str) -> str:
        """
        Resolve a relative path within the storage root.
        Prevents path traversal attacks.
        """
        base = os.path.realpath(self._storage_path)
        requested = os.path.realpath(os.path.join(self._storage_path, relative_path))
        if not requested.startswith(base + os.sep) and requested != base:
            raise PermissionError("Path traversal detected")
        return requested

    def _handle_list_dir(self, client_sock: socket.socket, payload: dict):
        """List contents of a directory."""
        path = payload.get("path", "/")
        target = self._safe_path(path)

        if not os.path.exists(target):
            self._send_error(client_sock, f"Path does not exist: {path}")
            return
        if not os.path.isdir(target):
            self._send_error(client_sock, f"Not a directory: {path}")
            return

        entries = []
        try:
            for name in sorted(os.listdir(target)):
                full = os.path.join(target, name)
                try:
                    stat = os.stat(full)
                    entries.append(
                        {
                            "name": name,
                            "is_dir": os.path.isdir(full),
                            "size": stat.st_size,
                            "modified": int(stat.st_mtime),
                        }
                    )
                except OSError:
                    continue  # Skip inaccessible entries
        except PermissionError:
            self._send_error(client_sock, f"Permission denied: {path}")
            return

        self._send_response(
            client_sock,
            MessageProtocol.MSG_LIST_DIR_RESP,
            {"path": path, "entries": entries},
        )

    def _handle_upload(self, client_sock: socket.socket, payload: dict):
        """Receive and save a file from Mobile A."""
        dest_path = payload.get("path", "")
        file_size = payload.get("size", 0)
        file_data_hex = payload.get("data", "")
        file_data = bytes.fromhex(file_data_hex) if file_data_hex else b""

        # Check quota
        used = self._get_used_bytes()
        available = self._allocated_bytes - used
        if file_size > available:
            self._send_error(
                client_sock,
                f"Insufficient space: need {file_size}, available {available}",
            )
            return

        target = self._safe_path(dest_path)
        os.makedirs(os.path.dirname(target), exist_ok=True)

        try:
            with open(target, "wb") as f:
                f.write(file_data)
            self._send_response(
                client_sock,
                MessageProtocol.MSG_UPLOAD_RESP,
                {"path": dest_path, "size": file_size, "success": True},
            )
        except IOError as e:
            self._send_error(client_sock, f"Write failed: {e}")

    def _handle_download(self, client_sock: socket.socket, payload: dict):
        """Send a file from storage to Mobile A."""
        src_path = payload.get("path", "")
        target = self._safe_path(src_path)

        if not os.path.exists(target):
            self._send_error(client_sock, f"File not found: {src_path}")
            return
        if os.path.isdir(target):
            self._send_error(client_sock, f"Cannot download a directory: {src_path}")
            return

        try:
            with open(target, "rb") as f:
                data = f.read()
            self._send_response(
                client_sock,
                MessageProtocol.MSG_DOWNLOAD_RESP,
                {
                    "path": src_path,
                    "size": len(data),
                    "data": data.hex(),
                },
            )
        except IOError as e:
            self._send_error(client_sock, f"Read failed: {e}")

    def _handle_delete(self, client_sock: socket.socket, payload: dict):
        """Delete a file or empty directory."""
        del_path = payload.get("path", "")
        target = self._safe_path(del_path)

        if not os.path.exists(target):
            self._send_error(client_sock, f"Path not found: {del_path}")
            return

        try:
            if os.path.isdir(target):
                os.rmdir(target)  # Only empty dirs
            else:
                os.remove(target)
            self._send_response(
                client_sock,
                MessageProtocol.MSG_DELETE_RESP,
                {"path": del_path, "success": True},
            )
        except OSError as e:
            self._send_error(client_sock, f"Delete failed: {e}")

    def _handle_get_stats(self, client_sock: socket.socket, payload: dict):
        """Return storage usage statistics."""
        used = self._get_used_bytes()
        self._send_response(
            client_sock,
            MessageProtocol.MSG_STATS_RESP,
            {
                "allocated": self._allocated_bytes,
                "used": used,
                "available": self._allocated_bytes - used,
                "storage_path": self._storage_path,
            },
        )

    def _handle_create_dir(self, client_sock: socket.socket, payload: dict):
        """Create a new directory."""
        dir_path = payload.get("path", "")
        target = self._safe_path(dir_path)

        try:
            os.makedirs(target, exist_ok=True)
            self._send_response(
                client_sock,
                MessageProtocol.MSG_CREATE_DIR_RESP,
                {"path": dir_path, "success": True},
            )
        except OSError as e:
            self._send_error(client_sock, f"Create directory failed: {e}")

    def _handle_rename(self, client_sock: socket.socket, payload: dict):
        """Rename or move a file/directory."""
        old_path = payload.get("old_path", "")
        new_path = payload.get("new_path", "")
        old_target = self._safe_path(old_path)
        new_target = self._safe_path(new_path)

        if not os.path.exists(old_target):
            self._send_error(client_sock, f"Source not found: {old_path}")
            return

        try:
            os.makedirs(os.path.dirname(new_target), exist_ok=True)
            os.rename(old_target, new_target)
            self._send_response(
                client_sock,
                MessageProtocol.MSG_RENAME_RESP,
                {"old_path": old_path, "new_path": new_path, "success": True},
            )
        except OSError as e:
            self._send_error(client_sock, f"Rename failed: {e}")

    def _get_used_bytes(self) -> int:
        """Calculate total bytes used by files in storage."""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(self._storage_path):
                for f in filenames:
                    try:
                        fp = os.path.join(dirpath, f)
                        total += os.path.getsize(fp)
                    except OSError:
                        continue
        except OSError:
            pass
        return total

    def send_storage_update(self):
        """Broadcast current storage stats to all connected clients."""
        used = self._get_used_bytes()
        payload = {
            "allocated": self._allocated_bytes,
            "used": used,
            "available": self._allocated_bytes - used,
        }
        data = MessageProtocol.encode(MessageProtocol.MSG_STORAGE_UPDATE, payload)
        with self._lock:
            for client in list(self._clients):
                try:
                    client.sendall(data)
                except OSError:
                    try:
                        self._clients.remove(client)
                    except ValueError:
                        pass