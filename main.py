"""Entry point for the CSE 222 Password Manager Milestone 2 program."""

from gui.main_window import MainWindow


def main():
    """Open the login dialog and start the Password Manager event loop."""
    app = MainWindow()
    app.after_idle(app.open_login)
    app.mainloop()


if __name__ == "__main__":
    main()
