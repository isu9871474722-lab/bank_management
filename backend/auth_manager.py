from db_manager import hash_text

class AuthManager:
    def __init__(self):
        self.current_user = None  # Will hold username (admin) or account_number (customer)
        self.role = None          # 'admin' or 'customer'
        self.user_data = None     # Database row for the logged-in user

    def login_admin(self, username, password, db_manager):
        """
        Authenticate an admin against the admins table.
        Returns (success_boolean, message_or_data).
        """
        hashed_password = hash_text(password)
        query = "SELECT username, name FROM admins WHERE username = %s AND password = %s"
        try:
            result = db_manager.execute_query(query, (username, hashed_password), fetch='one')
            if result:
                self.current_user = result['username']
                self.role = 'admin'
                self.user_data = result
                return True, f"Welcome back, {result['name']}!"
            else:
                return False, "Invalid username or password."
        except Exception as e:
            return False, f"Database error during admin login: {str(e)}"

    def login_customer(self, account_number, pin, db_manager):
        """
        Authenticate a customer against the accounts table, checking status.
        Returns (success_boolean, message_or_data).
        """
        hashed_pin = hash_text(pin)
        query = "SELECT account_number, first_name, last_name, status, balance FROM accounts WHERE account_number = %s AND pin = %s"
        try:
            result = db_manager.execute_query(query, (account_number, hashed_pin), fetch='one')
            if result:
                status = result['status']
                if status == 'Suspended':
                    return False, "This account is Suspended. Please contact bank staff."
                elif status == 'Closed':
                    return False, "This account is Closed. Access is denied."
                elif status == 'Active':
                    self.current_user = result['account_number']
                    self.role = 'customer'
                    self.user_data = result
                    full_name = f"{result['first_name']} {result['last_name']}"
                    return True, f"Welcome back, {full_name}!"
                else:
                    return False, f"Unknown account status: {status}"
            else:
                return False, "Invalid Account Number or PIN."
        except Exception as e:
            return False, f"Database error during customer login: {str(e)}"

    def logout(self):
        """Clear active user session."""
        self.current_user = None
        self.role = None
        self.user_data = None

    def is_authenticated(self):
        """Check if any user is authenticated."""
        return self.current_user is not None
