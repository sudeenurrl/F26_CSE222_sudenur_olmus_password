"""Account validation and persistence services for the Password Manager."""

import hashlib
import json
import os
import re
import secrets
import tempfile
from pathlib import Path


class AccountValidationError(ValueError):
    """Raised when account input does not meet the project requirements."""


DATA_DIRECTORY = Path(__file__).resolve().parent.parent / "data"
ACCOUNTS_FILE = DATA_DIRECTORY / "accounts.json"


def validate_username(username):
    """Return a trimmed username or raise an error for missing input."""
    cleaned_username = username.strip()
    if not cleaned_username:
        raise AccountValidationError("Enter a username.")
    return cleaned_username


def validate_password(password):
    """Validate the password rules required for Milestone 2."""
    if len(password) < 9:
        raise AccountValidationError("Password must contain at least 9 characters.")
    if not re.search(r"[A-Z]", password):
        raise AccountValidationError("Password must include an uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise AccountValidationError("Password must include a lowercase letter.")
    if not re.search(r"\d", password):
        raise AccountValidationError("Password must include a digit.")
    return password


def _read_accounts():
    """Read saved accounts; an absent file simply means no accounts exist yet."""
    if not ACCOUNTS_FILE.exists():
        return {}
    try:
        with ACCOUNTS_FILE.open("r", encoding="utf-8") as account_file:
            accounts = json.load(account_file)
    except (OSError, json.JSONDecodeError) as error:
        raise AccountValidationError("Saved account data could not be read.") from error
    if not isinstance(accounts, dict):
        raise AccountValidationError("Saved account data has an invalid format.")
    for key, account in accounts.items():
        if not isinstance(key, str) or not isinstance(account, dict):
            raise AccountValidationError("Saved account data has an invalid format.")
        username = account.get("username")
        salt = account.get("salt")
        password_hash = account.get("password_hash")
        if (
            not isinstance(username, str)
            or not username.strip()
            or username.strip().casefold() != key
            or not isinstance(salt, str)
            or re.fullmatch(r"[0-9a-fA-F]{32}", salt) is None
            or not isinstance(password_hash, str)
            or re.fullmatch(r"[0-9a-fA-F]{64}", password_hash) is None
        ):
            raise AccountValidationError("Saved account data has an invalid format.")
    return accounts


def _save_accounts(accounts):
    """Write account data through a temporary file to avoid partial saves."""
    temporary_file = None
    try:
        DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=DATA_DIRECTORY,
            prefix="accounts-", suffix=".tmp", delete=False
        ) as account_file:
            temporary_file = Path(account_file.name)
            json.dump(accounts, account_file, indent=2)
        os.replace(temporary_file, ACCOUNTS_FILE)
    except OSError as error:
        raise AccountValidationError("Account data could not be saved.") from error
    finally:
        if temporary_file is not None:
            try:
                temporary_file.unlink(missing_ok=True)
            except OSError:
                pass


def _hash_password(password, salt):
    """Return a salted password hash instead of storing the raw account password."""
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 150_000
    ).hex()


def create_account(username, password):
    """Validate and persist a new account with a unique username."""
    cleaned_username = validate_username(username)
    validate_password(password)
    accounts = _read_accounts()
    account_key = cleaned_username.casefold()
    if account_key in accounts:
        raise AccountValidationError("That username is already in use.")

    salt = secrets.token_bytes(16).hex()
    accounts[account_key] = {
        "username": cleaned_username,
        "salt": salt,
        "password_hash": _hash_password(password, salt),
    }
    _save_accounts(accounts)


def verify_account(username, password):
    """Return True only when the saved account credentials match."""
    try:
        cleaned_username = validate_username(username)
    except AccountValidationError:
        return False

    account = _read_accounts().get(cleaned_username.casefold())
    if account is None:
        return False
    supplied_hash = _hash_password(password, account["salt"])
    return secrets.compare_digest(account["password_hash"], supplied_hash)
