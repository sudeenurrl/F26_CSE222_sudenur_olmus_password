"""Tests for saving password entries from the main-window callback."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from application.password_entry_service import (
    PasswordEntry,
    PasswordEntryStorageError,
)
from gui.main_window import MainWindow


class MainWindowPasswordEntryTests(unittest.TestCase):
    """Exercise the Update callback without opening a desktop window."""

    def make_window(self, description="Email", username="fake-user",
                    password="fake-password"):
        return SimpleNamespace(
            description=Mock(get=Mock(return_value=description)),
            entry_username=Mock(get=Mock(return_value=username)),
            entry_password=Mock(get=Mock(return_value=password)),
        )

    def test_update_saves_entry_before_showing_success(self):
        window = self.make_window()
        existing_entry = PasswordEntry("Forum", "other-fake-user", "other-fake-password")
        storage = SimpleNamespace(entries=[existing_entry])
        events = []

        def save_entries(entries):
            events.append(("save", entries))

        def show_success(*args, **kwargs):
            events.append(("success", args, kwargs))

        storage.save_entries = Mock(side_effect=save_entries)
        with patch("gui.main_window.PasswordEntryStorage", return_value=storage), patch(
            "gui.main_window.messagebox.showinfo", side_effect=show_success
        ) as success:
            MainWindow._save_password_entry(window)

        storage.save_entries.assert_called_once_with(
            [
                existing_entry,
                PasswordEntry("Email", "fake-user", "fake-password"),
            ]
        )
        self.assertEqual([event[0] for event in events], ["save", "success"])
        success.assert_called_once()

    def test_empty_fields_show_error_without_loading_storage(self):
        window = self.make_window(description="   ")

        with patch("gui.main_window.PasswordEntryStorage") as storage_class, patch(
            "gui.main_window.messagebox.showerror"
        ) as error, patch("gui.main_window.messagebox.showinfo") as success:
            MainWindow._save_password_entry(window)

        storage_class.assert_not_called()
        error.assert_called_once()
        self.assertEqual(error.call_args.args[0], "Missing Information")
        success.assert_not_called()

    def test_duplicate_description_is_rejected_case_insensitively(self):
        window = self.make_window(description=" email ")
        storage = SimpleNamespace(
            entries=[PasswordEntry("Email", "saved-user", "saved-password")],
            save_entries=Mock(),
        )

        with patch("gui.main_window.PasswordEntryStorage", return_value=storage), patch(
            "gui.main_window.messagebox.showerror"
        ) as error, patch("gui.main_window.messagebox.showinfo") as success:
            MainWindow._save_password_entry(window)

        storage.save_entries.assert_not_called()
        error.assert_called_once()
        self.assertEqual(error.call_args.args[0], "Duplicate Description")
        success.assert_not_called()

    def test_storage_failure_shows_error_without_success(self):
        window = self.make_window()
        storage = SimpleNamespace(
            entries=[],
            save_entries=Mock(
                side_effect=PasswordEntryStorageError(
                    "Password entries could not be saved."
                )
            ),
        )

        with patch("gui.main_window.PasswordEntryStorage", return_value=storage), patch(
            "gui.main_window.messagebox.showerror"
        ) as error, patch("gui.main_window.messagebox.showinfo") as success:
            MainWindow._save_password_entry(window)

        error.assert_called_once_with(
            "Storage Error",
            "Password entries could not be saved.",
            parent=window,
        )
        success.assert_not_called()


if __name__ == "__main__":
    unittest.main()
