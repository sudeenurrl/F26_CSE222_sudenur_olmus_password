"""Tests for saving password entries from the main-window callback."""

import tempfile
import unittest
from pathlib import Path
from types import MethodType, SimpleNamespace
from unittest.mock import Mock, patch

from application.password_entry_service import (
    PasswordEntry,
    PasswordEntryStorage,
    PasswordEntryStorageError,
)
from gui.main_window import MainWindow


class MainWindowPasswordEntryTests(unittest.TestCase):
    """Exercise the Update callback without opening a desktop window."""

    def test_main_interface_enables_search_and_preserves_other_button_states(self):
        window = SimpleNamespace(
            _clear_window=Mock(),
            geometry=Mock(),
            _add_main_entry=Mock(),
            _save_password_entry=Mock(),
            _search_password_entry=Mock(),
            _display_all_password_entries=Mock(),
            show_start_screen=Mock(),
        )
        created_buttons = []

        def make_button(*args, **kwargs):
            button = Mock()
            created_buttons.append((kwargs, button))
            return button

        with patch("gui.main_window.ttk.Frame", return_value=Mock()), patch(
            "gui.main_window.ttk.Label", return_value=Mock()
        ), patch("gui.main_window.ttk.Button", side_effect=make_button), patch(
            "gui.main_window.tk.StringVar", side_effect=Mock
        ):
            MainWindow.show_main_interface(window, "fake-user")

        buttons_by_text = {options["text"]: options for options, _ in created_buttons}
        self.assertEqual(buttons_by_text["Search"]["state"], "normal")
        self.assertIs(
            buttons_by_text["Search"]["command"], window._search_password_entry
        )
        self.assertIs(
            buttons_by_text["Update"]["command"], window._save_password_entry
        )
        self.assertEqual(buttons_by_text["Display All"]["state"], "normal")
        self.assertIs(
            buttons_by_text["Display All"]["command"],
            window._display_all_password_entries,
        )

    def make_window(self, description="Email", username="fake-user",
                    password="fake-password"):
        window = SimpleNamespace(
            description=Mock(get=Mock(return_value=description)),
            entry_username=Mock(get=Mock(return_value=username)),
            entry_password=Mock(get=Mock(return_value=password)),
            _display_all_window=None,
            _display_all_table=None,
        )
        window._refresh_open_display_all_window = MethodType(
            MainWindow._refresh_open_display_all_window, window
        )
        window._populate_display_all_table = MainWindow._populate_display_all_table
        return window

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
        list_window = Mock()
        tree = Mock()
        window._display_all_window = list_window
        window._display_all_table = tree

        with patch("gui.main_window.PasswordEntryStorage") as storage_class, patch(
            "gui.main_window.messagebox.showerror"
        ) as error, patch("gui.main_window.messagebox.showinfo") as success:
            MainWindow._save_password_entry(window)

        storage_class.assert_not_called()
        error.assert_called_once()
        self.assertEqual(error.call_args.args[0], "Missing Information")
        success.assert_not_called()
        list_window.winfo_exists.assert_not_called()
        tree.delete.assert_not_called()
        tree.insert.assert_not_called()

    def test_successful_save_refreshes_open_display_all_table(self):
        window = self.make_window()
        list_window = Mock()
        list_window.winfo_exists.return_value = True
        tree = Mock()
        tree.get_children.return_value = ("old-row",)
        window._display_all_window = list_window
        window._display_all_table = tree
        entries = [
            PasswordEntry("zeta", "fake-zeta-user", "secret-zeta"),
            PasswordEntry("Beta", "fake-beta-user", "secret-beta"),
        ]
        storage = SimpleNamespace(entries=entries, save_entries=Mock())

        with patch(
            "gui.main_window.PasswordEntryStorage", return_value=storage
        ), patch("gui.main_window.tk.Toplevel") as new_window, patch(
            "gui.main_window.messagebox.showinfo"
        ) as success:
            MainWindow._save_password_entry(window)

        tree.delete.assert_called_once_with("old-row")
        self.assertEqual(
            [call.kwargs["values"] for call in tree.insert.call_args_list],
            [
                ("Beta", "fake-beta-user", "********"),
                ("Email", "fake-user", "********"),
                ("zeta", "fake-zeta-user", "********"),
            ],
        )
        self.assertNotIn("secret-beta", repr(tree.insert.call_args_list))
        self.assertNotIn("secret-zeta", repr(tree.insert.call_args_list))
        new_window.assert_not_called()
        success.assert_called_once()

    def test_successful_save_with_closed_display_all_window_is_safe(self):
        window = self.make_window()
        list_window = Mock()
        list_window.winfo_exists.return_value = False
        tree = Mock()
        window._display_all_window = list_window
        window._display_all_table = tree
        storage = SimpleNamespace(entries=[], save_entries=Mock())

        with patch(
            "gui.main_window.PasswordEntryStorage", return_value=storage
        ), patch("gui.main_window.messagebox.showinfo") as success:
            MainWindow._save_password_entry(window)

        self.assertIsNone(window._display_all_window)
        self.assertIsNone(window._display_all_table)
        tree.delete.assert_not_called()
        tree.insert.assert_not_called()
        success.assert_called_once()

    def test_each_empty_update_field_is_rejected(self):
        for field_name in ("description", "entry_username", "entry_password"):
            with self.subTest(field=field_name):
                values = {
                    "description": "Email",
                    "username": "fake-user",
                    "password": "fake-password",
                }
                values[
                    {
                        "description": "description",
                        "entry_username": "username",
                        "entry_password": "password",
                    }[field_name]
                ] = "   "
                window = self.make_window(**values)

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
        list_window = Mock()
        tree = Mock()
        window._display_all_window = list_window
        window._display_all_table = tree
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
        list_window.winfo_exists.assert_not_called()
        tree.delete.assert_not_called()
        tree.insert.assert_not_called()

    def test_storage_failure_shows_error_without_success(self):
        window = self.make_window()
        list_window = Mock()
        tree = Mock()
        window._display_all_window = list_window
        window._display_all_table = tree
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
        list_window.winfo_exists.assert_not_called()
        tree.delete.assert_not_called()
        tree.insert.assert_not_called()

    def test_search_loads_matching_credentials_without_unmasking_password(self):
        window = self.make_window(description=" email ")
        entry = PasswordEntry("Email", "saved-user", "saved-password")
        storage = SimpleNamespace(find_entry=Mock(return_value=entry))

        with patch("gui.main_window.PasswordEntryStorage", return_value=storage), patch(
            "gui.main_window.messagebox.showerror"
        ) as error, patch("gui.main_window.messagebox.showinfo") as info:
            MainWindow._search_password_entry(window)

        storage.find_entry.assert_called_once_with(" email ")
        window.entry_username.set.assert_called_once_with("saved-user")
        window.entry_password.set.assert_called_once_with("saved-password")
        error.assert_not_called()
        info.assert_not_called()

    def test_search_with_blank_description_shows_error_without_loading_storage(self):
        window = self.make_window(description="   ")

        with patch("gui.main_window.PasswordEntryStorage") as storage_class, patch(
            "gui.main_window.messagebox.showerror"
        ) as error, patch("gui.main_window.messagebox.showinfo") as info:
            MainWindow._search_password_entry(window)

        storage_class.assert_not_called()
        error.assert_called_once()
        self.assertEqual(error.call_args.args[0], "Missing Description")
        info.assert_not_called()

    def test_search_with_no_match_shows_helpful_message(self):
        window = self.make_window()
        storage = SimpleNamespace(find_entry=Mock(return_value=None))

        with patch("gui.main_window.PasswordEntryStorage", return_value=storage), patch(
            "gui.main_window.messagebox.showerror"
        ) as error, patch("gui.main_window.messagebox.showinfo") as info:
            MainWindow._search_password_entry(window)

        storage.find_entry.assert_called_once_with("Email")
        window.entry_username.set.assert_not_called()
        window.entry_password.set.assert_not_called()
        error.assert_not_called()
        self.assertEqual(info.call_args.args[0], "Entry Not Found")

    def test_search_storage_error_is_reported_without_crashing(self):
        window = self.make_window()
        storage = SimpleNamespace(
            find_entry=Mock(
                side_effect=PasswordEntryStorageError(
                    "Saved password entries could not be read."
                )
            )
        )

        with patch("gui.main_window.PasswordEntryStorage", return_value=storage), patch(
            "gui.main_window.messagebox.showerror"
        ) as error, patch("gui.main_window.messagebox.showinfo") as info:
            MainWindow._search_password_entry(window)

        error.assert_called_once_with(
            "Storage Error",
            "Saved password entries could not be read.",
            parent=window,
        )
        window.entry_username.set.assert_not_called()
        window.entry_password.set.assert_not_called()
        info.assert_not_called()

    def test_display_all_sorts_descriptions_and_masks_passwords(self):
        window = self.make_window()
        entries = [
            PasswordEntry("zeta", "fake-zeta-user", "secret-zeta"),
            PasswordEntry("Beta", "fake-beta-user", "secret-beta"),
            PasswordEntry("alpha", "fake-alpha-user", "secret-alpha"),
        ]
        tree = Mock()
        tree.get_children.return_value = ()

        with patch(
            "gui.main_window.PasswordEntryStorage",
            return_value=SimpleNamespace(entries=entries),
        ), patch("gui.main_window.tk.Toplevel", return_value=Mock()), patch(
            "gui.main_window.ttk.Frame", return_value=Mock()
        ), patch("gui.main_window.ttk.Treeview", return_value=tree), patch(
            "gui.main_window.ttk.Scrollbar", return_value=Mock()
        ):
            MainWindow._display_all_password_entries(window)

        displayed_values = [
            call.kwargs["values"] for call in tree.insert.call_args_list
        ]
        self.assertEqual(
            displayed_values,
            [
                ("alpha", "fake-alpha-user", "********"),
                ("Beta", "fake-beta-user", "********"),
                ("zeta", "fake-zeta-user", "********"),
            ],
        )
        self.assertNotIn("secret-alpha", repr(displayed_values))
        self.assertNotIn("secret-beta", repr(displayed_values))
        self.assertNotIn("secret-zeta", repr(displayed_values))

    def test_display_all_scrollbar_is_wired_for_many_entries(self):
        window = self.make_window()
        entries = [
            PasswordEntry(
                f"service-{index:02d}",
                f"fake-user-{index:02d}",
                f"fake-password-{index:02d}",
            )
            for index in range(59, -1, -1)
        ]
        list_frame = Mock()
        tree = Mock()
        tree.get_children.return_value = ()
        scrollbar = Mock()

        with patch(
            "gui.main_window.PasswordEntryStorage",
            return_value=SimpleNamespace(entries=entries),
        ), patch("gui.main_window.tk.Toplevel", return_value=Mock()), patch(
            "gui.main_window.ttk.Frame", return_value=list_frame
        ), patch("gui.main_window.ttk.Treeview", return_value=tree) as treeview, patch(
            "gui.main_window.ttk.Scrollbar", return_value=scrollbar
        ) as scrollbar_factory:
            MainWindow._display_all_password_entries(window)

        treeview.assert_called_once_with(
            list_frame,
            columns=("description", "username", "password"),
            show="headings",
        )
        self.assertEqual(
            [(call.args, call.kwargs) for call in tree.heading.call_args_list],
            [
                (("description",), {"text": "Description"}),
                (("username",), {"text": "Username"}),
                (("password",), {"text": "Password"}),
            ],
        )
        scrollbar_factory.assert_called_once_with(
            list_frame, orient="vertical", command=tree.yview
        )
        tree.configure.assert_called_once_with(yscrollcommand=scrollbar.set)
        tree.grid.assert_called_once_with(row=0, column=0, sticky="nsew")
        scrollbar.grid.assert_called_once_with(row=0, column=1, sticky="ns")
        list_frame.rowconfigure.assert_called_once_with(0, weight=1)
        list_frame.columnconfigure.assert_called_once_with(0, weight=1)

        displayed_values = [
            call.kwargs["values"] for call in tree.insert.call_args_list
        ]
        self.assertEqual(len(displayed_values), 60)
        self.assertEqual(
            [values[0] for values in displayed_values],
            [f"service-{index:02d}" for index in range(60)],
        )
        self.assertTrue(all(values[2] == "********" for values in displayed_values))
        self.assertNotIn("fake-password-", repr(displayed_values))

    def test_display_all_shows_message_when_storage_is_empty(self):
        window = SimpleNamespace()

        with patch(
            "gui.main_window.PasswordEntryStorage",
            return_value=SimpleNamespace(entries=[]),
        ), patch("gui.main_window.messagebox.showinfo") as info, patch(
            "gui.main_window.tk.Toplevel"
        ) as list_window:
            MainWindow._display_all_password_entries(window)

        info.assert_called_once_with(
            "No Saved Entries",
            "There are no saved password entries to display.",
            parent=window,
        )
        list_window.assert_not_called()

    def test_display_all_reports_storage_errors(self):
        window = SimpleNamespace()

        with patch(
            "gui.main_window.PasswordEntryStorage",
            side_effect=PasswordEntryStorageError(
                "Saved password entries could not be read."
            ),
        ), patch("gui.main_window.messagebox.showerror") as error, patch(
            "gui.main_window.tk.Toplevel"
        ) as list_window:
            MainWindow._display_all_password_entries(window)

        error.assert_called_once_with(
            "Storage Error",
            "Saved password entries could not be read.",
            parent=window,
        )
        list_window.assert_not_called()

    def test_display_all_reports_unreadable_or_invalid_storage(self):
        cases = (
            (
                "unreadable",
                lambda path: path.mkdir(),
                "Saved password entries could not be read.",
            ),
            (
                "invalid-encoding",
                lambda path: path.write_bytes(b"\xff"),
                "Saved password entries could not be read.",
            ),
            (
                "invalid-structure",
                lambda path: path.write_text("{}", encoding="utf-8"),
                "Saved password entries have an invalid format.",
            ),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            for name, create_file, expected_message in cases:
                with self.subTest(case=name):
                    entries_file = Path(temporary_directory) / f"{name}.json"
                    create_file(entries_file)

                    def create_storage(file_path=entries_file):
                        return PasswordEntryStorage(file_path)

                    window = self.make_window()
                    with patch(
                        "gui.main_window.PasswordEntryStorage",
                        side_effect=create_storage,
                    ), patch("gui.main_window.messagebox.showerror") as error, patch(
                        "gui.main_window.tk.Toplevel"
                    ) as list_window:
                        MainWindow._display_all_password_entries(window)

                    error.assert_called_once_with(
                        "Storage Error",
                        expected_message,
                        parent=window,
                    )
                    list_window.assert_not_called()

    def test_multiple_entries_survive_restart_search_and_display_alphabetically(self):
        entries_to_save = [
            ("zeta", "fake-zeta-user", "fake-zeta-secret"),
            ("Beta", "fake-beta-user", "fake-beta-secret"),
            ("alpha", "fake-alpha-user", "fake-alpha-secret"),
        ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            entries_file = Path(temporary_directory) / "entries.json"

            # Every GUI action gets a new service instance, as it would in the app.
            def create_storage():
                return PasswordEntryStorage(entries_file)

            with patch(
                "gui.main_window.PasswordEntryStorage", side_effect=create_storage
            ), patch("gui.main_window.messagebox.showinfo") as success:
                for description, username, password in entries_to_save:
                    window = self.make_window(description, username, password)
                    MainWindow._save_password_entry(window)

            self.assertEqual(success.call_count, len(entries_to_save))
            saved_file_contents = entries_file.read_bytes()

            duplicate_window = self.make_window(
                description=" BETA ",
                username="different-fake-user",
                password="different-fake-secret",
            )
            with patch(
                "gui.main_window.PasswordEntryStorage", side_effect=create_storage
            ), patch("gui.main_window.messagebox.showerror") as error, patch(
                "gui.main_window.messagebox.showinfo"
            ) as duplicate_success:
                MainWindow._save_password_entry(duplicate_window)

            self.assertEqual(error.call_args.args[0], "Duplicate Description")
            duplicate_success.assert_not_called()
            self.assertEqual(entries_file.read_bytes(), saved_file_contents)

            # A fresh instance confirms the saved entries remain after a restart.
            restarted_storage = PasswordEntryStorage(entries_file)
            self.assertEqual(
                [entry.description for entry in restarted_storage.entries],
                ["zeta", "Beta", "alpha"],
            )

            search_window = self.make_window(description=" beta ")
            with patch(
                "gui.main_window.PasswordEntryStorage", side_effect=create_storage
            ), patch("gui.main_window.messagebox.showerror") as error:
                MainWindow._search_password_entry(search_window)

            search_window.entry_username.set.assert_called_once_with("fake-beta-user")
            search_window.entry_password.set.assert_called_once_with("fake-beta-secret")
            error.assert_not_called()

            tree = Mock()
            tree.get_children.return_value = ()
            with patch(
                "gui.main_window.PasswordEntryStorage", side_effect=create_storage
            ), patch("gui.main_window.tk.Toplevel", return_value=Mock()), patch(
                "gui.main_window.ttk.Frame", return_value=Mock()
            ), patch("gui.main_window.ttk.Treeview", return_value=tree), patch(
                "gui.main_window.ttk.Scrollbar", return_value=Mock()
            ):
                MainWindow._display_all_password_entries(self.make_window())

            displayed_values = [
                call.kwargs["values"] for call in tree.insert.call_args_list
            ]
            self.assertEqual(
                displayed_values,
                [
                    ("alpha", "fake-alpha-user", "********"),
                    ("Beta", "fake-beta-user", "********"),
                    ("zeta", "fake-zeta-user", "********"),
                ],
            )
            self.assertNotIn("fake-alpha-secret", repr(displayed_values))
            self.assertNotIn("fake-beta-secret", repr(displayed_values))
            self.assertNotIn("fake-zeta-secret", repr(displayed_values))
            self.assertEqual(entries_file.read_bytes(), saved_file_contents)

    def test_corrupted_storage_is_reported_by_search_and_display_all(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            entries_file = Path(temporary_directory) / "entries.json"
            corrupted_contents = b"{"
            entries_file.write_bytes(corrupted_contents)

            def create_storage():
                return PasswordEntryStorage(entries_file)

            window = self.make_window()
            with patch(
                "gui.main_window.PasswordEntryStorage", side_effect=create_storage
            ), patch("gui.main_window.messagebox.showerror") as error, patch(
                "gui.main_window.tk.Toplevel"
            ) as list_window:
                MainWindow._search_password_entry(window)
                MainWindow._display_all_password_entries(window)

            self.assertEqual(error.call_count, 2)
            self.assertTrue(
                all(call.args[0] == "Storage Error" for call in error.call_args_list)
            )
            list_window.assert_not_called()
            self.assertEqual(entries_file.read_bytes(), corrupted_contents)


if __name__ == "__main__":
    unittest.main()
