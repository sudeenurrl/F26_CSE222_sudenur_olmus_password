"""Educational authenticated encryption for password-entry records.

This module intentionally provides a small course-demonstration construction,
not a replacement for a reviewed authenticated-encryption standard.
"""

import base64
import hashlib
import hmac
import json
import secrets
import struct
from collections.abc import Mapping, Sequence


FORMAT_NAME = "cse222-password-entries"
FORMAT_VERSION = 1
KEY_SIZE = 32
NONCE_SIZE = 16
_AUTHENTICATION_TAG = "authentication_tag"
_FIELDS = ("description", "username", "password")
_STREAM_DOMAIN = b"cse222-password-entry-keystream-v1"


class PasswordEntryCryptoError(ValueError):
    """Raised when encrypted password-entry data is invalid or cannot be opened."""


def encrypt_entries(
    entries: Sequence[Mapping[str, str]], key: bytes
) -> dict[str, object]:
    """Encrypt password-entry fields into a versioned JSON-compatible document."""
    _validate_key(key)
    nonce = secrets.token_bytes(NONCE_SIZE)
    encrypted_entries = []

    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise PasswordEntryCryptoError("Password-entry data has an invalid format.")
        encrypted_entry = {}
        for field in _FIELDS:
            value = entry.get(field)
            if not isinstance(value, str):
                raise PasswordEntryCryptoError(
                    "Password-entry data has an invalid format."
                )
            plaintext = value.encode("utf-8")
            encrypted_entry[field] = _encode_bytes(
                _xor_with_keystream(plaintext, key, nonce, index, field)
            )
        encrypted_entries.append(encrypted_entry)

    payload = {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "nonce": _encode_bytes(nonce),
        "entries": encrypted_entries,
    }
    payload[_AUTHENTICATION_TAG] = _encode_bytes(
        _authentication_tag(payload, key)
    )
    return payload


def decrypt_entries(
    document: Mapping[str, object], key: bytes
) -> list[dict[str, str]]:
    """Authenticate and decrypt a versioned password-entry document."""
    _validate_key(key)
    payload, nonce, encrypted_entries, tag = _validate_document(document)
    expected_tag = _authentication_tag(payload, key)
    if not hmac.compare_digest(tag, expected_tag):
        raise PasswordEntryCryptoError(
            "Password-entry data could not be authenticated."
        )

    entries = []
    for index, encrypted_entry in enumerate(encrypted_entries):
        entry = {}
        for field in _FIELDS:
            ciphertext = _decode_bytes(encrypted_entry[field])
            plaintext = _xor_with_keystream(
                ciphertext, key, nonce, index, field
            )
            try:
                entry[field] = plaintext.decode("utf-8")
            except UnicodeDecodeError as error:
                raise PasswordEntryCryptoError(
                    "Password-entry data could not be decrypted."
                ) from error
        entries.append(entry)
    return entries


def _validate_key(key: bytes) -> None:
    if not isinstance(key, bytes) or len(key) != KEY_SIZE:
        raise PasswordEntryCryptoError("The encryption key must be 32 bytes.")


def _validate_document(
    document: Mapping[str, object],
) -> tuple[dict[str, object], bytes, list[Mapping[str, str]], bytes]:
    if not isinstance(document, Mapping):
        raise PasswordEntryCryptoError("Encrypted password data has an invalid format.")
    expected_keys = {"format", "version", "nonce", "entries", _AUTHENTICATION_TAG}
    if set(document) != expected_keys:
        raise PasswordEntryCryptoError("Encrypted password data has an invalid format.")
    if document["format"] != FORMAT_NAME or document["version"] != FORMAT_VERSION:
        raise PasswordEntryCryptoError(
            "Encrypted password data uses an unsupported format version."
        )

    nonce = _decode_bytes(document["nonce"])
    if len(nonce) != NONCE_SIZE:
        raise PasswordEntryCryptoError("Encrypted password data has an invalid nonce.")

    encrypted_entries = document["entries"]
    if not isinstance(encrypted_entries, list):
        raise PasswordEntryCryptoError("Encrypted password data has an invalid format.")
    for encrypted_entry in encrypted_entries:
        if not isinstance(encrypted_entry, Mapping) or set(encrypted_entry) != set(
            _FIELDS
        ):
            raise PasswordEntryCryptoError(
                "Encrypted password data has an invalid entry format."
            )
        if not all(isinstance(encrypted_entry[field], str) for field in _FIELDS):
            raise PasswordEntryCryptoError(
                "Encrypted password data has an invalid entry format."
            )

    tag = _decode_bytes(document[_AUTHENTICATION_TAG])
    if len(tag) != hashlib.sha256().digest_size:
        raise PasswordEntryCryptoError(
            "Encrypted password data has an invalid authentication tag."
        )
    payload = {
        "format": document["format"],
        "version": document["version"],
        "nonce": document["nonce"],
        "entries": encrypted_entries,
    }
    return payload, nonce, encrypted_entries, tag


def _authentication_tag(payload: Mapping[str, object], key: bytes) -> bytes:
    return hmac.new(key, _canonical_json(payload), hashlib.sha256).digest()


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _encode_bytes(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _decode_bytes(value: object) -> bytes:
    if not isinstance(value, str):
        raise PasswordEntryCryptoError("Encrypted password data has an invalid encoding.")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError):
        raise PasswordEntryCryptoError(
            "Encrypted password data has an invalid encoding."
        ) from None


def _xor_with_keystream(
    data: bytes, key: bytes, nonce: bytes, index: int, field: str
) -> bytes:
    result = bytearray()
    counter = 0
    while len(result) < len(data):
        message = b"".join(
            (
                _length_prefixed(_STREAM_DOMAIN),
                _length_prefixed(nonce),
                struct.pack(">Q", index),
                _length_prefixed(field.encode("ascii")),
                struct.pack(">Q", counter),
            )
        )
        result.extend(hmac.new(key, message, hashlib.sha256).digest())
        counter += 1
    return bytes(left ^ right for left, right in zip(data, result))


def _length_prefixed(value: bytes) -> bytes:
    return struct.pack(">I", len(value)) + value
