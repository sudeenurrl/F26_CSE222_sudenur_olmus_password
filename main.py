"""Entry point for the CSE 222 Password Manager Milestone 2 program."""

from gui.main_window import MainWindow


def main():
    """Create and start the opening Password Manager window."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
