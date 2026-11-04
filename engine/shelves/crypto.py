"""
FoxVC Cryptography, Hashing, Encoding, and Auth Shelf.
"""

import hashlib
import hmac
import uuid
import secrets
import base64
from typing import Dict, Any


def fox_hash_sha256(data):
    return hashlib.sha256(str(data).encode("utf-8")).hexdigest()


def fox_hash_sha512(data):
    return hashlib.sha512(str(data).encode("utf-8")).hexdigest()


def fox_hash_md5(data):
    return hashlib.md5(str(data).encode("utf-8")).hexdigest()


def fox_hmac_sha256(key, message):
    return hmac.new(str(key).encode("utf-8"), str(message).encode("utf-8"), hashlib.sha256).hexdigest()


def fox_uuid():
    return str(uuid.uuid4())


def fox_secure_token(nbytes=32):
    return secrets.token_hex(int(nbytes))


def fox_base64_encode(data):
    return base64.b64encode(str(data).encode("utf-8")).decode("utf-8")


def fox_base64_decode(encoded_str):
    try:
        return base64.b64decode(str(encoded_str).encode("utf-8")).decode("utf-8", errors="replace")
    except Exception:
        return ""


def fox_hex_encode(data):
    return str(data).encode("utf-8").hex()


def fox_hex_decode(hex_str):
    try:
        return bytes.fromhex(str(hex_str)).decode("utf-8", errors="replace")
    except Exception:
        return ""


def get_crypto_shelf() -> Dict[str, Any]:
    return {
        "hashSha256": fox_hash_sha256,
        "hashSha512": fox_hash_sha512,
        "hashMd5": fox_hash_md5,
        "hmacSha256": fox_hmac_sha256,
        "uuid": fox_uuid,
        "uuid4": fox_uuid,
        "secureToken": fox_secure_token,
        "base64Encode": fox_base64_encode,
        "base64Decode": fox_base64_decode,
        "hexEncode": fox_hex_encode,
        "hexDecode": fox_hex_decode,
    }
