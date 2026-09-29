"""Account validation and persistence services for the Password Manager."""

import re


class AccountValidationError(ValueError):
    """Raised when account input does not meet the project requirements."""


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
