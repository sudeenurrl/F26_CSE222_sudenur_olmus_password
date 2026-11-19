"""Tests for the standalone password-entry encryption codec."""

import copy
import unittest

from application.password_entry_crypto import (
    FORMAT_VERSION,
    PasswordEntryCryptoError,
    decrypt_entries,
    encrypt_entries,
)


TEST_KEY = bytes(range(32))
WRONG_KEY = bytes(reversed(range(32)))
ENTRIES = [
    {
        "description": "Email",
        "username": "fictional-user",
        "password": "fictional-password",
    },
    {
        "description": "Forum",
        "username": "another-fictional-user",
        "password": "another-fictional-password",
    },
]


class PasswordEntryCryptoTests(unittest.TestCase):
    """Exercise encryption using fictional in-memory records only."""

    def test_round_trip_preserves_multiple_entries(self):
        document = encrypt_entries(ENTRIES, TEST_KEY)

        self.assertEqual(decrypt_entries(document, TEST_KEY), ENTRIES)
        self.assertEqual(document["version"], FORMAT_VERSION)
        self.assertNotEqual(document["nonce"], encrypt_entries(ENTRIES, TEST_KEY)["nonce"])

    def test_empty_entries_round_trip(self):
        document = encrypt_entries([], TEST_KEY)

        self.assertEqual(decrypt_entries(document, TEST_KEY), [])

    def test_encrypted_document_does_not_contain_plaintext_fields(self):
        document = encrypt_entries(ENTRIES, TEST_KEY)
        serialized_document = repr(document)

        for entry in ENTRIES:
            for value in entry.values():
                self.assertNotIn(value, serialized_document)

    def test_wrong_key_is_rejected_without_revealing_data(self):
        document = encrypt_entries(ENTRIES, TEST_KEY)

        with self.assertRaisesRegex(
            PasswordEntryCryptoError, "could not be authenticated"
        ):
            decrypt_entries(document, WRONG_KEY)

    def test_tampered_ciphertext_is_rejected(self):
        document = encrypt_entries(ENTRIES, TEST_KEY)
        tampered_document = copy.deepcopy(document)
        tampered_document["entries"][0]["password"] = "AAAA"

        with self.assertRaises(PasswordEntryCryptoError):
            decrypt_entries(tampered_document, TEST_KEY)

    def test_tampered_metadata_is_rejected(self):
        document = encrypt_entries(ENTRIES, TEST_KEY)
        tampered_document = copy.deepcopy(document)
        tampered_document["nonce"] = document["nonce"][:-2] + "AA"

        with self.assertRaises(PasswordEntryCryptoError):
            decrypt_entries(tampered_document, TEST_KEY)

    def test_malformed_base64_is_rejected(self):
        document = encrypt_entries(ENTRIES, TEST_KEY)
        document["entries"][0]["description"] = "not valid base64!"

        with self.assertRaises(PasswordEntryCryptoError):
            decrypt_entries(document, TEST_KEY)

    def test_unsupported_version_is_rejected(self):
        document = encrypt_entries(ENTRIES, TEST_KEY)
        document["version"] = FORMAT_VERSION + 1

        with self.assertRaisesRegex(
            PasswordEntryCryptoError, "unsupported format version"
        ):
            decrypt_entries(document, TEST_KEY)

    def test_invalid_document_structure_is_rejected(self):
        invalid_documents = (
            {},
            {"format": "wrong", "version": FORMAT_VERSION},
            {"format": "wrong", "version": FORMAT_VERSION, "entries": []},
        )
        for document in invalid_documents:
            with self.subTest(document=document):
                with self.assertRaises(PasswordEntryCryptoError):
                    decrypt_entries(document, TEST_KEY)

    def test_invalid_key_length_is_rejected(self):
        with self.assertRaises(PasswordEntryCryptoError):
            encrypt_entries(ENTRIES, b"short")


if __name__ == "__main__":
    unittest.main()
