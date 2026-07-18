# Bank Management System - Project Documentation

This project is a modern, responsive, and secure **Bank Management System** featuring both a command-line interface (CLI) and a web-based user interface (Web UI). It integrates a Python Flask backend with a local MySQL database to manage standard banking operations.

---

## 1. System Architecture

The application is built using a clean, modular structure:

```
bank_management/
│
├── backend/                  # Python backend code
│   ├── auth_manager.py       # Authentication and session handling
│   ├── bank_management_system.py # CLI welcome page and router driver
│   ├── bank_operations.py    # Core CLI business logic and DB transactions
│   ├── cli_renderer.py       # CLI text rendering, validation, and table grids
│   ├── db_manager.py         # Database connectivity, pooling, and schemas
│   └── web_server.py         # Flask Web Server exposing REST APIs
│
├── static/                   # Web UI frontend assets
│   ├── index.html            # SPA page structure
│   ├── style.css             # Premium CSS styling
│   └── app.js                # Frontend SPA controller and API caller
│
├── document.md               # Project documentation
└── .gitignore                # Excludes credentials and build caches
```

---

## 2. Technology Stack

- **Core**: Python 3
- **Web Backend**: Flask
- **Database**: MySQL (using `mysql-connector-python` connection pool)
- **CLI Utilities**: `colorama` (for colored console text) and `tabulate` (for text grids)
- **Web Frontend**: HTML5, Vanilla CSS3 (custom HSL color palette and Glassmorphism), and Vanilla JavaScript (ES6 Fetch API)

---

## 3. Database Schema Design

The relational database is named `bank_management_db` and contains three tables:

### A. Accounts Table
Stores core banking details for each customer account.
- `account_number`: `VARCHAR(12)` (Primary Key) - Unique 12-digit auto-generated number (e.g. `100000000001`+).
- `first_name`: `VARCHAR(50)` (Not Null)
- `last_name`: `VARCHAR(50)` (Not Null)
- `pin`: `VARCHAR(64)` (Not Null) - 4-digit PIN stored securely as a SHA-256 hash.
- `account_type`: `VARCHAR(20)` (Not Null) - `Savings` or `Current`.
- `balance`: `DECIMAL(15, 2)` (Default `0.00`) - Current balance.
- `email`: `VARCHAR(100)` (Unique, Optional)
- `phone`: `VARCHAR(15)` (Optional)
- `address`: `TEXT` (Optional)
- `status`: `VARCHAR(20)` (Default `'Active'`) - Can be `'Active'`, `'Suspended'`, or `'Closed'`.
- `created_at`: `TIMESTAMP` (Default `CURRENT_TIMESTAMP`)

### B. Transactions Table
Logs credit, debit, and inter-account funds transfers.
- `transaction_id`: `INT AUTO_INCREMENT` (Primary Key)
- `account_number`: `VARCHAR(12)` (Foreign Key references `accounts(account_number)` ON DELETE CASCADE)
- `transaction_type`: `VARCHAR(20)` - `Deposit`, `Withdrawal`, `Transfer Out`, or `Transfer In`.
- `amount`: `DECIMAL(15, 2)` (Not Null)
- `target_account`: `VARCHAR(12)` (Null unless transaction type is a transfer)
- `description`: `VARCHAR(255)`
- `created_at`: `TIMESTAMP` (Default `CURRENT_TIMESTAMP`)

### C. Admins Table
Stores credentials for staff access.
- `username`: `VARCHAR(50)` (Primary Key)
- `password`: `VARCHAR(64)` (Not Null) - SHA-256 hashed password.
- `name`: `VARCHAR(100)` (Not Null)
- *Note: A default admin account (`admin` / `admin123`) is seeded automatically upon first-run setup.*

---

## 4. Key Workflows & Features

### A. Setup Wizard (Automated Configuration)
If no local `config.json` database settings are detected on startup (CLI or Web UI), the system displays a setup wizard that:
1. Gathers local MySQL Host, Username, Password, and Port.
2. Verifies connectivity to the MySQL server.
3. Automatically creates the database `bank_management_db` and all three tables.
4. Seeds the default admin account and saves credentials locally to `config.json`.

### B. Admin / Staff Dashboard
Accessible to users with admin credentials:
- **Create Account**: Register new customers with type selection, PIN setup, and initial deposit options.
- **View All Accounts**: Display a table listing all accounts, status details, and balances.
- **Search Account**: Instantly search by name, account number, or phone.
- **Update Account**: Modify profile details (email, phone, address).
- **Suspend/Activate Account**: Block/unblock customer logins.
- **Close Account**: Soft-delete (set status to `'Closed'` to preserve transactions history) or Hard-delete (permanently remove record).
- **Global Ledger**: Audit history of all logs across all accounts.

### C. Customer Dashboard
Accessible to customers using their Account Number and 4-digit PIN:
- **Balance & Status**: View available funds and account health.
- **Deposit Funds**: Credit money to the account balance.
- **Withdraw Funds**: Debit money (subject to active status and balance checks).
- **Transfer Funds**: Atomic transfers sending money to other accounts. (Debits sender, credits receiver, logs entries in both accounts inside a single SQL transaction block).
- **Statements**: Chronological search of account statements.
- **Security PIN**: Modify the 4-digit PIN.

---

## 5. Web Interface Aesthetics

The Web UI features a premium design system built with:
- **Palette**: Sleek dark mode utilizing deep slate blues (`#0f172a`, `#1e293b`), bright teals (`#0ea5e9`), success greens (`#10b981`), and danger reds (`#ef4444`).
- **Glassmorphism**: Translucent boxes with border outlines, backdrop blurs, and glow animations.
- **Micro-animations**: Smooth transitions on inputs, button clicks, tab transitions, and animated warning/success toasts.

---

## 6. How to Run the Project

### Prerequisites
- Python 3.x
- MySQL Server installed and running locally
- Required libraries:
  ```bash
  pip install mysql-connector-python colorama tabulate flask
  ```

### Run the Web Interface
1. Run the server script:
   ```bash
   python backend/web_server.py
   ```
2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```
3. Complete the setup wizard with your local MySQL password.

### Run the CLI Interface
1. Open your terminal and run:
   ```bash
   python backend/bank_management_system.py
   ```
2. Navigate menus using numeric console selections.
