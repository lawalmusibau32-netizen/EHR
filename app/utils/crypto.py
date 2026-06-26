from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import current_app


ENCRYPTED_PREFIX = "enc:v1:"


class EncryptionError(ValueError):
    pass


def generate_encryption_key() -> str:
    return base64.urlsafe_b64encode(AESGCM.generate_key(bit_length=256)).decode("ascii")


def _key_bytes() -> bytes:
    key = current_app.config.get("EHR_ENCRYPTION_KEY", "")
    if not key:
        raise EncryptionError("EHR_ENCRYPTION_KEY is not configured.")
    try:
        raw = base64.urlsafe_b64decode(key.encode("ascii"))
    except Exception as exc:
        raise EncryptionError("EHR_ENCRYPTION_KEY must be base64 encoded.") from exc
    if len(raw) != 32:
        raise EncryptionError("EHR_ENCRYPTION_KEY must decode to 32 bytes for AES-256.")
    return raw


def encrypt_value(value: str | None) -> str | None:
    if value in (None, ""):
        return value
    if str(value).startswith(ENCRYPTED_PREFIX):
        return str(value)
    nonce = os.urandom(12)
    encrypted = AESGCM(_key_bytes()).encrypt(nonce, str(value).encode("utf-8"), None)
    payload = base64.urlsafe_b64encode(nonce + encrypted).decode("ascii")
    return f"{ENCRYPTED_PREFIX}{payload}"


def decrypt_value(value: str | None) -> str | None:
    if value in (None, ""):
        return value
    if not str(value).startswith(ENCRYPTED_PREFIX):
        return value
    payload = str(value)[len(ENCRYPTED_PREFIX) :]
    try:
        raw = base64.urlsafe_b64decode(payload.encode("ascii"))
        nonce, encrypted = raw[:12], raw[12:]
        return AESGCM(_key_bytes()).decrypt(nonce, encrypted, None).decode("utf-8")
    except Exception as exc:
        raise EncryptionError("Unable to decrypt protected value.") from exc


def decrypt_mapping(row: dict | None, fields: list[str]) -> dict | None:
    if not row:
        return row
    copy = dict(row)
    for field in fields:
        if field in copy:
            copy[field] = decrypt_value(copy[field])
    return copy
