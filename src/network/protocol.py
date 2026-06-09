"""
Give Space — Network Protocol Layer
JSON length-prefixed message protocol for TCP communication.
All messages between Mobile A and Mobile B follow this format.
"""

import json
import struct
from typing import Any, Optional


class MessageProtocol:
    """
    Implements a simple length-prefixed JSON protocol.
    Format: [4-byte payload length][JSON payload]
    All integers are network byte order (big-endian).
    """

    HEADER_SIZE = 4  # 4 bytes for uint32 length

    # --- Message Types ---
    # Mobile A → Mobile B
    MSG_LIST_DIR = "list_dir"
    MSG_UPLOAD_FILE = "upload_file"
    MSG_DOWNLOAD_FILE = "download_file"
    MSG_DELETE_FILE = "delete_file"
    MSG_GET_STATS = "get_stats"
    MSG_CREATE_DIR = "create_dir"
    MSG_RENAME_FILE = "rename_file"
    MSG_PAIRING_REQUEST = "pairing_request"

    # Mobile B → Mobile A
    MSG_LIST_DIR_RESP = "list_dir_resp"
    MSG_UPLOAD_RESP = "upload_resp"
    MSG_DOWNLOAD_RESP = "download_resp"
    MSG_DELETE_RESP = "delete_resp"
    MSG_STATS_RESP = "stats_resp"
    MSG_CREATE_DIR_RESP = "create_dir_resp"
    MSG_RENAME_RESP = "rename_resp"
    MSG_PAIRING_RESP = "pairing_resp"
    MSG_ERROR = "error"
    MSG_STORAGE_UPDATE = "storage_update"

    @staticmethod
    def encode(msg_type: str, payload: Optional[dict] = None) -> bytes:
        """
        Encode a message into bytes for transmission.
        Args:
            msg_type: One of the MSG_* constants
            payload: Optional dictionary payload
        Returns:
            Length-prefixed JSON bytes ready for socket.send()
        """
        data = {"type": msg_type, "payload": payload or {}}
        json_str = json.dumps(data, separators=(",", ":"))
        raw = json_str.encode("utf-8")
        header = struct.pack("!I", len(raw))
        return header + raw

    @staticmethod
    def decode(data: bytes) -> dict:
        """
        Decode received bytes. Must provide complete message.
        For streaming, use the decoder class below.
        """
        msg = json.loads(data.decode("utf-8"))
        return msg

    @staticmethod
    def get_message_length(data: bytes) -> int:
        """Extract payload length from header bytes."""
        if len(data) < MessageProtocol.HEADER_SIZE:
            return -1
        return struct.unpack("!I", data[: MessageProtocol.HEADER_SIZE])[0]

    @staticmethod
    def get_total_message_length(data: bytes) -> int:
        """Get total message length including header."""
        payload_len = MessageProtocol.get_message_length(data)
        if payload_len < 0:
            return -1
        return MessageProtocol.HEADER_SIZE + payload_len


class StreamDecoder:
    """
    Handles incremental TCP stream decoding.
    Maintains buffer state across multiple recv() calls.
    """

    def __init__(self):
        self._buffer = bytearray()
        self._expected_length = -1

    def feed(self, chunk: bytes) -> list[dict]:
        """
        Feed raw bytes into the decoder. Returns all complete messages.
        Partial data remains buffered for next feed.
        """
        self._buffer.extend(chunk)
        messages: list[dict] = []

        while True:
            if self._expected_length < 0:
                if len(self._buffer) < MessageProtocol.HEADER_SIZE:
                    break
                self._expected_length = MessageProtocol.get_message_length(
                    bytes(self._buffer)
                )

            total = MessageProtocol.HEADER_SIZE + self._expected_length
            if len(self._buffer) < total:
                break

            msg_bytes = bytes(self._buffer[:total])
            self._buffer = self._buffer[total:]
            self._expected_length = -1

            try:
                msg = MessageProtocol.decode(
                    msg_bytes[MessageProtocol.HEADER_SIZE:]
                )
                messages.append(msg)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                messages.append(
                    {
                        "type": MessageProtocol.MSG_ERROR,
                        "payload": {"error": f"Protocol decode error: {e}"},
                    }
                )

        return messages

    def reset(self):
        """Clear the buffer. Useful after a connection reset."""
        self._buffer.clear()
        self._expected_length = -1