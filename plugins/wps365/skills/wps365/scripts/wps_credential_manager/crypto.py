# -*- coding: utf-8 -*-
"""
WPS 365 凭证加解密，精确对齐 Node.js crypto-utils.js。
使用 AES-256-GCM，密钥通过 scrypt 从 app_id 派生。
"""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

ALGORITHM = "aes-256-gcm"
KEY_LENGTH = 32
IV_LENGTH = 12
SALT_LENGTH = 16
DEFAULT_KEY_SOURCE = "openclaw_agentspace"


def _derive_key(app_id: str, salt: bytes) -> bytes:
    key_source = app_id or DEFAULT_KEY_SOURCE
    return Scrypt(salt=salt, length=KEY_LENGTH, n=2**14, r=8, p=1).derive(
        key_source.encode("utf-8")
    )


def encrypt_wps_sid(wps_sid: str, app_id: str = "") -> str:
    if not wps_sid:
        raise ValueError("wpsSid cannot be empty")
    salt = os.urandom(SALT_LENGTH)
    key = _derive_key(app_id, salt)
    iv = os.urandom(IV_LENGTH)
    aesgcm = AESGCM(key)
    encrypted = aesgcm.encrypt(iv, wps_sid.encode("utf-8"), None)
    auth_tag = encrypted[-16:]
    encrypted_data = encrypted[:-16]
    return f"{salt.hex()}:{iv.hex()}:{auth_tag.hex()}:{encrypted_data.hex()}"


def decrypt_wps_sid(encrypted_token: str, app_id: str = "") -> str:
    if not encrypted_token:
        raise ValueError("encryptedToken cannot be empty")
    parts = encrypted_token.split(":")
    if len(parts) != 4:
        raise ValueError(
            "Invalid encrypted token format. Expected format: salt:iv:authTag:encryptedData"
        )
    salt_hex, iv_hex, auth_tag_hex, encrypted_data_hex = parts
    salt = bytes.fromhex(salt_hex)
    key = _derive_key(app_id, salt)
    iv = bytes.fromhex(iv_hex)
    auth_tag = bytes.fromhex(auth_tag_hex)
    encrypted_data = bytes.fromhex(encrypted_data_hex)
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(iv, encrypted_data + auth_tag, None)
    return decrypted.decode("utf-8")
