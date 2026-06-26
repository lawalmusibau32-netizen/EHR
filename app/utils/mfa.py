from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time


def generate_mfa_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _hotp(secret: str, counter: int, digits: int = 6) -> str:
    padded = secret + ("=" * ((8 - len(secret) % 8) % 8))
    key = base64.b32decode(padded.upper())
    message = struct.pack(">Q", counter)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10**digits)).zfill(digits)


def verify_totp(secret: str | None, code: str | None, window: int = 1) -> bool:
    if not secret or not code:
        return False
    code = code.strip()
    if not code.isdigit():
        return False
    current_counter = int(time.time() // 30)
    for offset in range(-window, window + 1):
        if hmac.compare_digest(_hotp(secret, current_counter + offset), code):
            return True
    return False
