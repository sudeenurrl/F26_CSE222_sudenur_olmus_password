"""Automated checks for Milestone 2 account validation and persistence."""

import json
import tempfile
import unittest
from pathlib import Path

from application import account_service


class AccountServiceTests(unittest.TestCase):
    """Keep account-service tests isolated from the project's real data folder."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_data_directory = account_service.DATA_DIRECTORY
        self.original_accounts_file = account_service.ACCOUNTS_FILE
        account_service.DATA_DIRECTORY = Path(self.temporary_directory.name)
        account_service.ACCOUNTS_FILE = account_service.DATA_DIRECTORY / "accounts.json"

    def tearDown(self):
        account_service.DATA_DIRECTORY = self.original_data_directory
        account_service.ACCOUNTS_FILE = self.original_accounts_file
        self.temporary_directory.cleanup()

    def test_valid_account_can_be_verified(self):
        account_service.create_account("Sudenur", "StrongPass1")
        self.assertTrue(account_service.verify_account("sudenur", "StrongPass1"))

    def test_duplicate_username_is_rejected(self):
        account_service.create_account("Sudenur", "StrongPass1")
        with self.assertRaises(account_service.AccountValidationError):
            account_service.create_account("SUDENUR", "AnotherPass2")

    def test_invalid_password_is_rejected(self):
        with self.assertRaises(account_service.AccountValidationError):
            account_service.create_account("Sudenur", "short1A")

    def test_malformed_records_raise_useful_error(self):
        invalid_records = [None, {}, {"username": "Sudenur", "salt": "bad",
                                        "password_hash": "bad"}]
        for record in invalid_records:
            with self.subTest(record=record):
                account_service.ACCOUNTS_FILE.write_text(
                    json.dumps({"sudenur": record}), encoding="utf-8"
                )
                with self.assertRaises(account_service.AccountValidationError):
                    account_service.verify_account("Sudenur", "StrongPass1")

    def test_corrupt_json_raises_useful_error(self):
        account_service.ACCOUNTS_FILE.write_text("{", encoding="utf-8")
        with self.assertRaises(account_service.AccountValidationError):
            account_service.verify_account("Sudenur", "StrongPass1")

    def test_incorrect_password_does_not_verify(self):
        account_service.create_account("Sudenur", "StrongPass1")
        self.assertFalse(account_service.verify_account("Sudenur", "WrongPass2"))


if __name__ == "__main__":
    unittest.main()
