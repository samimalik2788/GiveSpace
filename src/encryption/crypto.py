"""
Give Space — Encryption Module (AES-256-GCM)
Provides authenticated encryption for "Hide" mode.
When Mobile A toggles "Hide", files are encrypted before transfer
and decrypted on Mobile B.
"""

import os
import base64
import hashlib
import logging
from typing import Optional, Tuple

logger = logging.getLogger("GiveSpace.Crypto")

# Derive from cryptography library
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.exceptions import InvalidTag

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography library not available — encryption disabled")

KEY_SIZE = 32  # AES-256
NONCE_SIZE = 12  # 96-bit nonce for GCM
SALT_SIZE = 16
PBKDF2_ITERATIONS = 100_000


class FileCipher:
    """
    AES-256-GCM encryption/decryption for file data.
    Uses password-based key derivation (PBKDF2) for the cipher key.
    The default password is derived from the pairing code for automatic operation.
    """

    def __init__(self, password: Optional[str] = None):
        """
        Initialize cipher with optional password.
        If no password provided, a default derived key is used.
        """
        if not CRYPTO_AVAILABLE:
            self._available = False
            return

        self._available = True
        self._password = password or "GiveSpace-Default-Pairing-Key-2026"

    @property
    def is_available(self) -> bool:
        return self._available

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive a 256-bit key from the password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        return kdf.derive(self._password.encode("utf-8"))

    def encrypt(self, data: bytes) -> Optional[bytes]:
        """
        Encrypt data with AES-256-GCM.
        Returns: nonce + ciphertext + tag (concatenated)
        Returns None if encryption fails.
        """
        if not self._available:
            return None

        try:
            salt = os.urandom(SALT_SIZE)
            key = self._derive_key(salt)
            aesgcm = AESGCM(key)
            nonce = os.urandom(NONCE_SIZE)
            ciphertext = aesgcm.encrypt(nonce, data, None)
            # Format: salt (16) + nonce (12) + ciphertext+tag (varies)
            return salt + nonce + ciphertext
        except Exception as e:
            logger.exception("Encryption failed")
            return None

    def decrypt(self, encrypted_data: bytes) -> Optional[bytes]:
        """
        Decrypt data that was encrypted with encrypt().
        Format expected: salt (16) + nonce (12) + ciphertext+tag (rest)
        Returns None if decryption fails (wrong key or corrupted data).
        """
        if not self._available:
            return None

        try:
            salt = encrypted_data[:SALT_SIZE]
            nonce = encrypted_data[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
            ciphertext = encrypted_data[SALT_SIZE + NONCE_SIZE :]

            key = self._derive_key(salt)
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext
        except (InvalidTag, Exception) as e:
            logger.error("Decryption failed: %s", e)
            return None

    def encrypt_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """
        Encrypt a file on disk.
        If output_path is None, appends '.encrypted' to input filename.
        Returns True on success.
        """
        if not self._available:
            return False

        try:
            with open(input_path, "rb") as f:
                data = f.read()

            encrypted = self.encrypt(data)
            if encrypted is None:
                return False

            dest = output_path or (input_path + ".encrypted")
            with open(dest, "wb") as f:
                f.write(encrypted)
            return True
        except IOError as e:
            logger.error("File encrypt failed: %s", e)
            return False

    def decrypt_file(
        self, input_path: str, output_path: Optional[str] = None
    ) -> bool:
        """
        Decrypt a file that was encrypted with encrypt_file().
        If output_path is None, removes '.encrypted' suffix or appends '.decrypted'.
        Returns True on success.
        """
        if not self._available:
            return False

        try:
            with open(input_path, "rb") as f:
                data = f.read()

            plaintext = self.decrypt(data)
            if plaintext is None:
                return False

            if output_path:
                dest = output_path
            elif input_path.endswith(".encrypted"):
                dest = input_path[: -len(".encrypted")]
            else:
                dest = input_path + ".decrypted"

            with open(dest, "wb") as f:
                f.write(plaintext)
            return True
        except IOError as e:
            logger.error("File decrypt failed: %s", e)
            return False

    @staticmethod
    def generate_hidden_filename(original_name: str) -> str:
        """
        Generate an obfuscated filename for hidden files.
        Uses a hash of the original name.
        """
        name_hash = hashlib.sha256(original_name.encode()).hexdigest()[:16]
        return f".gs_hidden_{name_hash}"