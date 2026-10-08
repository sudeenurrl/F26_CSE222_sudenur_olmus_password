"""Check login callbacks without opening desktop windows."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from application.account_service import AccountValidationError
from gui.login_gui import LoginGUI


class LoginGUITests(unittest.TestCase):
    def make_dialog(self):
        return SimpleNamespace(
            username=Mock(get=Mock(return_value=" Sudenur ")),
            password=Mock(get=Mock(return_value="StrongPass1")),
            login_button=Mock(), password_entry=Mock(),
            destroy=Mock(), on_success=Mock(),
        )

    def test_storage_error_shows_one_message_and_allows_retry(self):
        dialog = self.make_dialog()
        with patch("gui.login_gui.verify_account", side_effect=AccountValidationError("Bad data")), patch("gui.login_gui.messagebox.showerror") as error:
            LoginGUI.login(dialog)
        error.assert_called_once_with("Login Error", "Bad data", parent=dialog)
        dialog.login_button.configure.assert_called_with(state="normal")
        dialog.password_entry.delete.assert_called_once()
        dialog.on_success.assert_not_called()

    def test_invalid_credentials_allow_retry(self):
        dialog = self.make_dialog()
        with patch("gui.login_gui.verify_account", return_value=False), patch("gui.login_gui.messagebox.showerror") as error:
            LoginGUI.login(dialog)
        error.assert_called_once()
        dialog.login_button.configure.assert_called_with(state="normal")
        dialog.on_success.assert_not_called()

    def test_success_closes_dialog_and_opens_main_interface(self):
        dialog = self.make_dialog()
        with patch("gui.login_gui.verify_account", return_value=True):
            LoginGUI.login(dialog)
        dialog.destroy.assert_called_once()
        dialog.on_success.assert_called_once_with("Sudenur")
