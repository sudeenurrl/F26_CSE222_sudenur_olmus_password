"""Account Creation window class for Password Manager Milestone 1."""

import tkinter as tk
from tkinter import messagebox, ttk


class AccountGUI(tk.Toplevel):
    """Show the initial account-creation form and its instructions."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Create Account")
        self.resizable(False, False)
        self.transient(parent)
        self._build_interface()
        self._center_over_parent(parent)

    def _build_interface(self):
        frame = ttk.Frame(self, padding=20)
        frame.grid(sticky="nsew")

        ttk.Label(
            frame,
            text="Create a Password Manager Account",
            font=("Arial", 15, "bold")
        ).grid(column=0, row=0, columnspan=2, pady=(0, 12))

        ttk.Label(
            frame,
            text=("Choose a unique username. Your password will need at least "
                  "9 characters, including an uppercase letter, lowercase "
                  "letter, and digit."),
            wraplength=390,
            justify="left"
        ).grid(column=0, row=1, columnspan=2, sticky="w", pady=(0, 14))

        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.confirm_password = tk.StringVar()
        self._add_entry(frame, "Username:", self.username, 2)
        self._add_entry(frame, "Password:", self.password, 3, "*")
        self._add_entry(frame, "Confirm password:", self.confirm_password, 4, "*")

        ttk.Button(frame, text="Create Account",
                   command=self.show_milestone_message).grid(
                       column=0, row=5, columnspan=2, pady=(14, 0)
                   )

    def _add_entry(self, frame, label, variable, row, show=None):
        ttk.Label(frame, text=label).grid(
            column=0, row=row, sticky="e", padx=(0, 8), pady=5
        )
        ttk.Entry(frame, textvariable=variable, show=show, justify="right",
                  width=33).grid(column=1, row=row, sticky="ew", pady=5)

    def show_milestone_message(self):
        """Keep the required button active before its Milestone 2 logic exists."""
        messagebox.showinfo(
            "Milestone 1",
            "Account validation and file storage are implemented in Milestone 2.",
            parent=self
        )

    def _center_over_parent(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
