"""Login window class for Password Manager Milestone 2."""

import tkinter as tk
from tkinter import messagebox, ttk

from application.account_service import AccountValidationError, verify_account


class LoginGUI(tk.Toplevel):
    """Verify account credentials and notify the main window after login."""

    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.title("Login")
        self.resizable(False, False)
        self.transient(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.on_success = on_success
        self._build_interface()
        self.bind("<Return>", self._handle_return)
        self._center_over_parent(parent)
        self.wait_visibility()
        self.lift()
        self.grab_set()
        self.username_entry.focus_set()

    def _build_interface(self):
        frame = ttk.Frame(self, padding=20)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Login", font=("Arial", 15, "bold")).grid(
            column=0, row=0, columnspan=2, pady=(0, 12)
        )
        ttk.Label(
            frame,
            text="Enter the username and password you created.",
            wraplength=350
        ).grid(column=0, row=1, columnspan=2, sticky="w", pady=(0, 14))

        self.username = tk.StringVar()
        self.password = tk.StringVar()
        ttk.Label(frame, text="Username:").grid(
            column=0, row=2, sticky="e", padx=(0, 8), pady=5
        )
        self.username_entry = ttk.Entry(
            frame, textvariable=self.username, justify="left", width=30
        )
        self.username_entry.grid(
            column=1, row=2, pady=5
        )
        ttk.Label(frame, text="Password:").grid(
            column=0, row=3, sticky="e", padx=(0, 8), pady=5
        )
        self.password_entry = ttk.Entry(
            frame, textvariable=self.password, show="*", justify="left", width=30
        )
        self.password_entry.grid(column=1, row=3, pady=5)
        buttons = ttk.Frame(frame)
        buttons.grid(column=0, row=4, columnspan=2, pady=(14, 0))
        self.login_button = ttk.Button(buttons, text="Login", command=self.login)
        self.login_button.grid(column=0, row=0, padx=(0, 8))
        ttk.Button(buttons, text="Cancel", command=self.destroy).grid(column=1, row=0)

    def _handle_return(self, event):
        """Submit when Enter is pressed in either credential field."""
        if event.widget in (self.username_entry, self.password_entry):
            self.login()

    def login(self):
        """Verify saved credentials and clear invalid password input."""
        # Disable first to avoid duplicate login attempts from repeated clicks.
        self.login_button.configure(state="disabled")
        try:
            verified = verify_account(self.username.get(), self.password.get())
        except AccountValidationError as error:
            messagebox.showerror("Login Error", str(error), parent=self)
            verified = False
        else:
            if not verified:
                messagebox.showerror(
                    "Login Error", "The username or password is not valid.", parent=self
                )
        if not verified:
            self.password_entry.delete(0, tk.END)
            self.login_button.configure(state="normal")
            self.password_entry.focus_set()
            return
        username = self.username.get().strip()
        self.destroy()
        self.on_success(username)

    def _center_over_parent(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
