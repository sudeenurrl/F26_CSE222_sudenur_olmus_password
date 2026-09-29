"""Login window class for Password Manager Milestone 1."""

import tkinter as tk
from tkinter import messagebox, ttk


class LoginGUI(tk.Toplevel):
    """Show the initial login form and its instructions."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Login")
        self.resizable(False, False)
        self.transient(parent)
        self._build_interface()
        self.bind("<Return>", lambda event: self.login())
        self._center_over_parent(parent)

    def _build_interface(self):
        frame = ttk.Frame(self, padding=20)
        frame.grid(sticky="nsew")

        ttk.Label(frame, text="Login", font=("Arial", 15, "bold")).grid(
            column=0, row=0, columnspan=2, pady=(0, 12)
        )
        ttk.Label(
            frame,
            text=("Enter your username and password. Account verification is "
                  "completed in Milestone 2."),
            wraplength=350
        ).grid(column=0, row=1, columnspan=2, sticky="w", pady=(0, 14))

        self.username = tk.StringVar()
        self.password = tk.StringVar()
        ttk.Label(frame, text="Username:").grid(
            column=0, row=2, sticky="e", padx=(0, 8), pady=5
        )
        ttk.Entry(frame, textvariable=self.username, justify="right", width=30).grid(
            column=1, row=2, pady=5
        )
        ttk.Label(frame, text="Password:").grid(
            column=0, row=3, sticky="e", padx=(0, 8), pady=5
        )
        ttk.Entry(frame, textvariable=self.password, show="*", justify="right",
                  width=30).grid(column=1, row=3, pady=5)
        ttk.Button(frame, text="Login", command=self.login).grid(
            column=0, row=4, columnspan=2, pady=(14, 0)
        )

    def login(self):
        """Keep the required Login control working before Milestone 2."""
        messagebox.showinfo(
            "Milestone 1",
            "Login verification and the main interface are implemented in Milestone 2.",
            parent=self
        )

    def _center_over_parent(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
