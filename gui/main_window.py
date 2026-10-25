"""Opening and post-login interfaces for Password Manager Milestone 3."""

import tkinter as tk
from tkinter import messagebox, ttk

from application.password_entry_service import (
    PasswordEntry,
    PasswordEntryStorage,
    PasswordEntryStorageError,
)
from gui.account_gui import AccountGUI
from gui.login_gui import LoginGUI


class MainWindow(tk.Tk):
    """Display the opening screen and switch to the main interface after login."""

    def __init__(self):
        super().__init__()
        self.title("Password Manager - Milestone 3")
        self.geometry("520x330")
        self.resizable(False, False)
        self._center_window()
        self.show_start_screen()

    def _clear_window(self):
        """Remove the visible view before displaying the next application screen."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_start_screen(self):
        """Display Create Account, Login, and Cancel controls."""
        self._clear_window()
        self.geometry("520x330")
        frame = ttk.Frame(self, padding=32)
        frame.pack(expand=True, fill="both")

        ttk.Label(
            frame,
            text="Password Manager",
            font=("Arial", 22, "bold")
        ).pack(pady=(0, 8))

        ttk.Label(
            frame,
            text="Create an account or log in to begin. Select Cancel to close the program.",
            justify="center",
            wraplength=400
        ).pack(pady=(0, 22))

        # Each button creates an instance of a class in a separate GUI module.
        ttk.Button(frame, text="Create Account", width=24,
                   command=self.open_account_creation).pack(pady=5)
        ttk.Button(frame, text="Login", width=24,
                   command=self.open_login).pack(pady=5)
        ttk.Button(frame, text="Cancel", width=24,
                   command=self.destroy).pack(pady=5)

    def open_account_creation(self):
        """Open the separate Account Creation window class."""
        AccountGUI(self)

    def open_login(self):
        """Open the separate Login window class."""
        LoginGUI(self, self.show_main_interface)

    def show_main_interface(self, username):
        """Replace the opening screen after a successful account login."""
        self._clear_window()
        self.geometry("600x420")
        frame = ttk.Frame(self, padding=24)
        frame.pack(expand=True, fill="both")

        ttk.Label(
            frame, text="Password Manager", font=("Arial", 20, "bold")
        ).grid(column=0, row=0, columnspan=3, sticky="w")
        ttk.Label(frame, text=f"Logged in as: {username}").grid(
            column=0, row=1, columnspan=3, sticky="w", pady=(2, 18)
        )
        ttk.Label(
            frame,
            text="Enter a description, username, and password. Description must be unique.",
            wraplength=520,
        ).grid(column=0, row=2, columnspan=3, sticky="w", pady=(0, 12))

        self.description = tk.StringVar()
        self.entry_username = tk.StringVar()
        self.entry_password = tk.StringVar()
        self._add_main_entry(frame, "Description:", self.description, 3)
        self._add_main_entry(frame, "Username:", self.entry_username, 4)
        self._add_main_entry(frame, "Password:", self.entry_password, 5, show="*")

        controls = ttk.Frame(frame)
        controls.grid(column=0, row=6, columnspan=3, sticky="w", pady=(18, 0))
        self.update_button = ttk.Button(
            controls, text="Update", command=self._save_password_entry
        )
        self.update_button.grid(column=0, row=0, padx=(0, 8))
        # The main screen appears after login, so Search is ready to use here.
        ttk.Button(
            controls,
            text="Search",
            command=self._search_password_entry,
            state="normal",
        ).grid(column=1, row=0, padx=8)
        # Display All is enabled after login and opens a separate list window.
        ttk.Button(
            controls,
            text="Display All",
            command=self._display_all_password_entries,
            state="normal",
        ).grid(column=2, row=0, padx=8)
        ttk.Button(controls, text="Log Out", command=self.show_start_screen).grid(
            column=3, row=0, padx=8
        )
        frame.columnconfigure(1, weight=1)

    def _add_main_entry(self, frame, label, variable, row, show=None):
        """Create one consistently aligned field in the main interface."""
        ttk.Label(frame, text=label).grid(
            column=0, row=row, sticky="e", padx=(0, 8), pady=6
        )
        ttk.Entry(
            frame, textvariable=variable, show=show, justify="left", width=42
        ).grid(column=1, row=row, columnspan=2, sticky="ew", pady=6)

    def _save_password_entry(self):
        """Validate the form and save a new password entry."""
        description = self.description.get()
        username = self.entry_username.get()
        password = self.entry_password.get()

        # Whitespace-only values are not useful credentials, so reject them up front.
        if not all(value.strip() for value in (description, username, password)):
            messagebox.showerror(
                "Missing Information",
                "Please enter a description, username, and password before updating.",
                parent=self,
            )
            return

        try:
            # Reload saved entries so duplicate checks include earlier saves.
            storage = PasswordEntryStorage()
            description_key = description.strip().casefold()
            if any(
                entry.description.strip().casefold() == description_key
                for entry in storage.entries
            ):
                messagebox.showerror(
                    "Duplicate Description",
                    "An entry with this description already exists. Please choose a unique description.",
                    parent=self,
                )
                return

            # Save the existing entries together with the new one to keep prior data.
            storage.save_entries(
                storage.entries + [PasswordEntry(description, username, password)]
            )
        except PasswordEntryStorageError as error:
            messagebox.showerror("Storage Error", str(error), parent=self)
            return

        # Report success only after the storage service confirms the save completed.
        messagebox.showinfo(
            "Password Saved",
            "The password entry was saved successfully.",
            parent=self,
        )

    def _search_password_entry(self):
        """Find credentials by description and put them into the existing fields."""
        description = self.description.get()

        # A description is required because it tells the app which entry to find.
        if not description.strip():
            messagebox.showerror(
                "Missing Description",
                "Please enter a description before searching.",
                parent=self,
            )
            return

        try:
            # Opening storage reloads saved entries, including entries from earlier runs.
            storage = PasswordEntryStorage()
            entry = storage.find_entry(description)
        except PasswordEntryStorageError as error:
            messagebox.showerror("Storage Error", str(error), parent=self)
            return

        if entry is None:
            messagebox.showinfo(
                "Entry Not Found",
                "No saved entry matches that description.",
                parent=self,
            )
            return

        # The existing password field stays masked because its Entry widget uses show="*".
        self.entry_username.set(entry.username)
        self.entry_password.set(entry.password)

    def _display_all_password_entries(self):
        """Show every saved entry in a separate, alphabetically sorted window."""
        try:
            # Loading storage reads current entries from disk without changing the file.
            entries = PasswordEntryStorage().entries
        except PasswordEntryStorageError as error:
            messagebox.showerror("Storage Error", str(error), parent=self)
            return

        if not entries:
            messagebox.showinfo(
                "No Saved Entries",
                "There are no saved password entries to display.",
                parent=self,
            )
            return

        list_window = tk.Toplevel(self)
        list_window.title("Saved Password Entries")
        list_window.geometry("620x320")
        list_frame = ttk.Frame(list_window, padding=12)
        list_frame.pack(expand=True, fill="both")

        columns = ("description", "username", "password")
        entry_table = ttk.Treeview(
            list_frame, columns=columns, show="headings"
        )
        for column, heading in (
            ("description", "Description"),
            ("username", "Username"),
            ("password", "Password"),
        ):
            entry_table.heading(column, text=heading)
            entry_table.column(column, anchor="w", width=180)

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=entry_table.yview
        )
        entry_table.configure(yscrollcommand=scrollbar.set)
        entry_table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        # Sort without regard to capitalization and use a fixed mask instead of passwords.
        sorted_entries = sorted(
            entries, key=lambda saved_entry: saved_entry.description.casefold()
        )
        for entry in sorted_entries:
            entry_table.insert(
                "",
                "end",
                values=(entry.description, entry.username, "********"),
            )

    def _center_window(self):
        """Center the first window on the desktop."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
