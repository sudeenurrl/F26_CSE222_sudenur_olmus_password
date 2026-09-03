# Python Project Starter -

## Project Structure

```text
CSE222-python-project-starter-code/
├── main.py
├── application/
│   └── README.md
├── data/
│   └── README.md
└── gui/
    ├── README.md
    ├── main_window.py
    ├── login_gui.py
    └── account_gui.py
```

## Project Organization

- Data Layer - Handles all data storage and retrieval
- GUI Layer - Handles the user interface and display
- Application Layer - Handles the core logic and business rules

### Data Layer (data/)
Responsible for:

- Storing and retrieving account information
- File I/O operations
- Data persistence

Example Implementation:

- Implement functions to save accounts to a file
- Implement functions to load accounts from storage
- Implement functions to retrieve account data when needed

### GUI Layer (gui/)
Responsible for:

- Creating and managing windows
- Displaying user interface components
- Capturing user input
- Triggering business logic through buttons/events

Example Implementation:

- Implement the main window with login and create account buttons
- Implement the login window with username and password entry
- Implement the account creation window with validation feedback
- Implement event handlers for buttons and entry fields
- Connect GUI components to business layer functions

### Application Layer (application/)
Responsible for:

- Account creation logic
- Login verification
- Password validation
- Business rules enforcement

Example Implementation:

- Implement account creation logic (validation, uniqueness check, storage)
- Implement login verification (checking credentials)
- Implement password strength validation (minimum 9 characters, uppercase, lowercase, digit)
- Handle business logic errors and return appropriate feedback
