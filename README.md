# CSE222 Password Manager — Milestone 2

A Python desktop application built with Tkinter. It supports account creation,
password validation, and login with persistent local accounts.

## Run

Use Python 3.8 or newer with Tkinter installed. From this project directory:

```sh
python3 main.py
```

The application uses only the Python standard library. If importing `tkinter`
fails, use a Python installation that includes Tk support.

### Run in VS Code

Open this project folder in VS Code, select **Run and Debug**, and choose
**Run Password Manager**. The configuration launches `main.py` with the project
folder as its working directory, so no manual `PYTHONPATH` setting is needed.
The login dialog opens first. Select **Cancel** to return to the opening screen,
where you can create an account or open the login dialog again.

Run the command above in a shell terminal. If the prompt begins with `>>>`, the
terminal is in the Python interpreter; enter `exit()` before running shell
commands.

### macOS Tk compatibility

This workspace is configured to use `/usr/local/bin/python3` (Python 3.15.1,
Tcl/Tk 9.0.4). If that interpreter is installed elsewhere, update
`python.defaultInterpreterPath` in `.vscode/settings.json` and the `python`
entries in `.vscode/launch.json` and the Code Runner settings. No system
Python installation is changed by the project.

## Test

```sh
python3 -B -m unittest discover -s tests -v
```

Tests use temporary directories for account data and mocked GUI callbacks;
they do not open windows or change your saved accounts.

## Current features

- Create an account with a unique, case-insensitive username.
- Require at least nine password characters, with uppercase, lowercase, and a digit.
- Confirm the password before saving the account.
- Store salted PBKDF2-SHA256 password hashes in `data/accounts.json`.
- Validate saved records and report unreadable or malformed account data.
- Write accounts through a temporary file so failed saves preserve existing data.
- Log in and log out; account dialogs are modal.

The post-login form is preparation for later milestones. Update displays an
informational message; Search and Display All are disabled. Password-entry
storage and retrieval are not implemented in Milestone 2.

## Project structure

```text
main.py                         Application entry point
application/account_service.py  Account validation, hashing, and persistence
gui/main_window.py              Opening and post-login screens
gui/account_gui.py              Account creation dialog
gui/login_gui.py                Login dialog
data/                           Local account storage
tests/                          Service and login callback tests
```

Local account files, Python caches, virtual environments, and macOS metadata
are ignored by Git. Account storage is intended for one running application
instance at a time.
