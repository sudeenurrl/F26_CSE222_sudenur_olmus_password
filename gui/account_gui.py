"""Account Creation window class for Password Manager Milestone 2."""

import tkinter as tk
from tkinter import messagebox, ttk

from application.account_service import AccountValidationError, create_account


class AccountGUI(tk.Toplevel):
    """Create a validated account and close when the account is saved."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Create Account")
        self.resizable(False, False)
        self.transient(parent)
        self._build_interface()
        self._center_over_parent(parent)
        self.grab_set()

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

        buttons = ttk.Frame(frame)
        buttons.grid(column=0, row=5, columnspan=2, pady=(14, 0))
        ttk.Button(buttons, text="Create Account", command=self.create_account).grid(
            column=0, row=0, padx=(0, 8)
        )
        ttk.Button(buttons, text="Cancel", command=self.destroy).grid(column=1, row=0)
        self.bind("<Return>", self._handle_return)

    def _handle_return(self, event):
        """Create an account when Enter is pressed in a form field."""
        if event.keysym == "Return":
            self.create_account()

    def _add_entry(self, frame, label, variable, row, show=None):
        ttk.Label(frame, text=label).grid(
            column=0, row=row, sticky="e", padx=(0, 8), pady=5
        )
        entry = ttk.Entry(frame, textvariable=variable, show=show, justify="left",
                          width=33)
        entry.grid(column=1, row=row, sticky="ew", pady=5)
        if row == 2:
            entry.focus_set()

    def create_account(self):
        """Validate the form, save the account, and report useful errors."""
        password = self.password.get()
        if password != self.confirm_password.get():
            messagebox.showerror(
                "Account Error", "The two passwords do not match.", parent=self
            )
            self.password.set("")
            self.confirm_password.set("")
            return
        try:
            create_account(self.username.get(), password)
        except AccountValidationError as error:
            messagebox.showerror("Account Error", str(error), parent=self)
            self.password.set("")
            self.confirm_password.set("")
            return
        messagebox.showinfo(
            "Account Created", "Your account was created. You may now log in.",
            parent=self
        )
        self.destroy()

    def _center_over_parent(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
