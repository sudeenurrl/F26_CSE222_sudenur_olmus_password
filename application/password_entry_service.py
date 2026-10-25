"""Local JSON storage for password entries."""

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


ENTRIES_FILE = Path(__file__).resolve().parent.parent / "data" / "password_entries.json"


class PasswordEntryStorageError(ValueError):
    """Raised when password-entry data cannot be read or saved safely."""


@dataclass(frozen=True)
class PasswordEntry:
    """Keep the description and its login credentials together."""

    description: str
    username: str
    password: str


class PasswordEntryStorage:
    """Load and save password entries in a project-local JSON file."""

    def __init__(self, file_path: Path | str = ENTRIES_FILE):
        self.file_path = Path(file_path)
        # Load saved JSON at startup so entries remain available after restarting.
        self.entries = self.load_entries()

    def load_entries(self) -> list[PasswordEntry]:
        """Load entries, treating a missing file as an empty collection."""
        try:
            with self.file_path.open("r", encoding="utf-8") as entries_file:
                saved_entries = json.load(entries_file)
        except FileNotFoundError:
            self.entries = []
            return self.entries
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise PasswordEntryStorageError(
                "Saved password entries could not be read."
            ) from error

        self.entries = self._validate_entries(saved_entries)
        return self.entries

    def save_entries(self, entries: list[PasswordEntry] | None = None) -> None:
        """Save entries as JSON so they are retained across application restarts."""
        entries_to_save = self.entries if entries is None else entries
        validated_entries = self._validate_entries(
            [
                {
                    "description": entry.description,
                    "username": entry.username,
                    "password": entry.password,
                }
                for entry in entries_to_save
                if isinstance(entry, PasswordEntry)
            ]
        )
        if len(validated_entries) != len(entries_to_save):
            raise PasswordEntryStorageError("Password entries have an invalid format.")

        # Refuse to replace existing data if its JSON is already malformed.
        self._read_existing_entries()

        temporary_file = None
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.file_path.parent,
                prefix=f"{self.file_path.stem}-",
                suffix=".tmp",
                delete=False,
            ) as entries_file:
                temporary_file = Path(entries_file.name)
                # JSON gives each entry named fields that can be sorted by description later.
                json.dump(
                    [entry.__dict__ for entry in validated_entries],
                    entries_file,
                    indent=2,
                )
            # The file stays on disk, allowing a later application run to reload these entries.
            os.replace(temporary_file, self.file_path)
        except (OSError, UnicodeError) as error:
            raise PasswordEntryStorageError(
                "Password entries could not be saved."
            ) from error
        finally:
            if temporary_file is not None:
                try:
                    temporary_file.unlink(missing_ok=True)
                except OSError:
                    pass

        self.entries = validated_entries

    def _read_existing_entries(self) -> list[PasswordEntry]:
        """Check existing data before saving to avoid overwriting corruption."""
        try:
            with self.file_path.open("r", encoding="utf-8") as entries_file:
                saved_entries = json.load(entries_file)
        except FileNotFoundError:
            return []
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise PasswordEntryStorageError(
                "Existing password-entry data could not be read safely."
            ) from error
        return self._validate_entries(saved_entries)

    @staticmethod
    def _validate_entries(saved_entries: object) -> list[PasswordEntry]:
        """Check the JSON structure and enforce unique, nonempty descriptions."""
        if not isinstance(saved_entries, list):
            raise PasswordEntryStorageError(
                "Saved password entries have an invalid format."
            )

        entries = []
        descriptions = set()
        for saved_entry in saved_entries:
            if not isinstance(saved_entry, dict):
                raise PasswordEntryStorageError(
                    "Saved password entries have an invalid format."
                )

            description = saved_entry.get("description")
            username = saved_entry.get("username")
            password = saved_entry.get("password")
            if (
                not isinstance(description, str)
                or not description.strip()
                or not isinstance(username, str)
                or not username.strip()
                or not isinstance(password, str)
                or not password.strip()
            ):
                raise PasswordEntryStorageError(
                    "Each password entry must include a description, username, and password."
                )

            description_key = description.strip().casefold()
            if description_key in descriptions:
                raise PasswordEntryStorageError(
                    "Password-entry descriptions must be unique."
                )
            descriptions.add(description_key)
            entries.append(PasswordEntry(description, username, password))

        return entries
