"""Opening window for Password Manager Milestone 1."""

import tkinter as tk
from tkinter import ttk

from gui.account_gui import AccountGUI
from gui.login_gui import LoginGUI


class MainWindow(tk.Tk):
    """Display the required Create Account, Login, and Cancel buttons."""

    def __init__(self):
        super().__init__()
        self.title("Password Manager - Milestone 1")
        self.geometry("520x330")
        self.resizable(False, False)
        self._center_window()
        self._build_interface()

    def _build_interface(self):
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
        LoginGUI(self)

    def _center_window(self):
        """Center the first window on the desktop."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
