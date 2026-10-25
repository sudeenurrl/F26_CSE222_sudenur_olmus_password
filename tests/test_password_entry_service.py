"""Tests for local password-entry storage using temporary files and fake values."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from application import password_entry_service
from application.password_entry_service import (
    PasswordEntry,
    PasswordEntryStorage,
    PasswordEntryStorageError,
)


class PasswordEntryStorageTests(unittest.TestCase):
    """Keep storage tests isolated from the project's real data folder."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.entries_file = Path(self.temporary_directory.name) / "entries.json"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_entries_can_be_saved_and_loaded_after_restart(self):
        entries = [
            PasswordEntry("Email", "fake-user", "fake-password"),
            PasswordEntry("Forum", "another-fake-user", "another-fake-password"),
        ]
        PasswordEntryStorage(self.entries_file).save_entries(entries)

        restarted_storage = PasswordEntryStorage(self.entries_file)

        self.assertEqual(restarted_storage.entries, entries)
        saved_json = json.loads(self.entries_file.read_text(encoding="utf-8"))
        self.assertEqual(
            [entry["description"] for entry in saved_json], ["Email", "Forum"]
        )

    def test_missing_file_starts_with_empty_entries(self):
        storage = PasswordEntryStorage(self.entries_file)

        self.assertEqual(storage.entries, [])

    def test_find_entry_ignores_description_case_and_extra_spaces(self):
        storage = PasswordEntryStorage(self.entries_file)
        saved_entry = PasswordEntry("Email", "fake-user", "fake-password")
        storage.save_entries([saved_entry])

        found_entry = PasswordEntryStorage(self.entries_file).find_entry(" email ")

        self.assertEqual(found_entry, saved_entry)

    def test_find_entry_returns_none_when_description_is_not_saved(self):
        storage = PasswordEntryStorage(self.entries_file)

        self.assertIsNone(storage.find_entry("Missing"))

    def test_malformed_json_is_reported_without_overwriting_file(self):
        original_data = b"{"
        self.entries_file.write_bytes(original_data)

        with self.assertRaises(PasswordEntryStorageError):
            PasswordEntryStorage(self.entries_file)

        self.assertEqual(self.entries_file.read_bytes(), original_data)

    def test_save_does_not_overwrite_json_corrupted_after_loading(self):
        storage = PasswordEntryStorage(self.entries_file)
        self.entries_file.write_text("{", encoding="utf-8")
        original_data = self.entries_file.read_bytes()

        with self.assertRaises(PasswordEntryStorageError):
            storage.save_entries([PasswordEntry("Email", "fake-user", "fake-password")])

        self.assertEqual(self.entries_file.read_bytes(), original_data)

    def test_failed_write_preserves_existing_entries(self):
        storage = PasswordEntryStorage(self.entries_file)
        original_entries = [PasswordEntry("Email", "fake-user", "fake-password")]
        storage.save_entries(original_entries)
        original_data = self.entries_file.read_bytes()

        with patch.object(password_entry_service.os, "replace", side_effect=OSError):
            with self.assertRaises(PasswordEntryStorageError):
                storage.save_entries(
                    [PasswordEntry("Forum", "other-fake-user", "other-fake-password")]
                )

        self.assertEqual(self.entries_file.read_bytes(), original_data)
        self.assertEqual(list(self.entries_file.parent.glob("*.tmp")), [])

    def test_duplicate_descriptions_are_rejected(self):
        storage = PasswordEntryStorage(self.entries_file)

        with self.assertRaises(PasswordEntryStorageError):
            storage.save_entries(
                [
                    PasswordEntry("Email", "fake-user", "fake-password"),
                    PasswordEntry(" email ", "other-fake-user", "other-fake-password"),
                ]
            )


if __name__ == "__main__":
    unittest.main()
