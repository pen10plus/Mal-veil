"""
Cryptographic Key Derivation & ChaCha20 String Encryptor
Provides Python build-time encryption matching the C99 chacha20.c implementation.
"""

import hashlib
import struct
from typing import Tuple


def rotl32(v: int, c: int) -> int:
    return ((v << c) & 0xFFFFFFFF) | (v >> (32 - c))


def chacha20_quarter_round(x: list, a: int, b: int, c: int, d: int):
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = rotl32(x[d] ^ x[a], 16)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = rotl32(x[b] ^ x[c], 12)
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = rotl32(x[d] ^ x[a], 8)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = rotl32(x[b] ^ x[c], 7)


def chacha20_block(key: bytes, counter: int, nonce: bytes) -> bytes:
    constants = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
    key_words = list(struct.unpack("<8I", key))
    nonce_words = list(struct.unpack("<3I", nonce))
    state = constants + key_words + [counter] + nonce_words

    x = list(state)
    for _ in range(10):
        # Column round
        chacha20_quarter_round(x, 0, 4, 8, 12)
        chacha20_quarter_round(x, 1, 5, 9, 13)
        chacha20_quarter_round(x, 2, 6, 10, 14)
        chacha20_quarter_round(x, 3, 7, 11, 15)
        # Diagonal round
        chacha20_quarter_round(x, 0, 5, 10, 15)
        chacha20_quarter_round(x, 1, 6, 11, 12)
        chacha20_quarter_round(x, 2, 7, 8, 13)
        chacha20_quarter_round(x, 3, 4, 9, 14)

    out = []
    for i in range(16):
        out.append((x[i] + state[i]) & 0xFFFFFFFF)
    return struct.pack("<16I", *out)


def chacha20_encrypt(data: bytes, key: bytes, nonce: bytes, counter: int = 1) -> bytes:
    """Encrypts or decrypts data using ChaCha20 (symmetric XOR keystream)."""
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes.")
    if len(nonce) != 12:
        raise ValueError("Nonce must be 12 bytes.")

    keystream_blocks = []
    num_blocks = (len(data) + 63) // 64
    for i in range(num_blocks):
        keystream_blocks.append(chacha20_block(key, counter + i, nonce))

    full_keystream = b"".join(keystream_blocks)[:len(data)]
    return bytes(a ^ b for a, b in zip(data, full_keystream))


def derive_key_and_nonce(secret_seed: str, salt: str = "v2_hardened_pipeline") -> Tuple[bytes, bytes]:
    """Derives a 32-byte key and 12-byte nonce using SHA-256 HKDF-like digest."""
    prk = hashlib.sha256(f"{salt}_{secret_seed}".encode("utf-8")).digest()
    key = hashlib.sha256(prk + b"KEY").digest()
    nonce = hashlib.sha256(prk + b"NONCE").digest()[:12]
    return key, nonce


def encrypt_string_literal(text: str, secret_seed: str = "default_seed") -> Tuple[bytes, bytes, bytes]:
    """
    Encrypts a string into ciphertext bytes.
    Returns (ciphertext, key, nonce).
    """
    key, nonce = derive_key_and_nonce(secret_seed)
    ciphertext = chacha20_encrypt(text.encode("utf-8"), key, nonce)
    return ciphertext, key, nonce


def decrypt_string_literal(ciphertext: bytes, key: bytes, nonce: bytes) -> str:
    """Decrypts ciphertext bytes back to string."""
    plain = chacha20_encrypt(ciphertext, key, nonce)
    return plain.decode("utf-8")
