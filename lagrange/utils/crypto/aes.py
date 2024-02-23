import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def aes_gcm_encrypt(data: bytes, key: bytes) -> bytes:
    nonce = secrets.token_bytes(12)

    cipher = AESGCM(key)
    return nonce + cipher.encrypt(nonce, data, None)


def aes_gcm_decrypt(data: bytes, key: bytes) -> bytes:
    nonce = data[:12]
    cipher = AESGCM(key)
    return cipher.decrypt(nonce, data[12:], None)


__all__ = ["aes_gcm_encrypt", "aes_gcm_decrypt"]
