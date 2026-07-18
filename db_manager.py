import mysql.connector
from mysql.connector import Error
import hashlib
import json
import os

CONFIG_FILE = "config.json"

def load_db_config():
    """Load database configuration from config.json."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_db_config(host, user, password, port):
    """Save database configuration to config.json."""
    config = {
        "host": host,
        "user": user,
        "password": password,
        "port": int(port),
        "database": "bank_management_db"
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    return config

def hash_text(text):
    """Utility to hash PINs or passwords using SHA-256."""
    return hashlib.sha256(text.encode()).hexdigest()

class DBManager:
    def __init__(self, config=None):
        self.config = config or load_db_config()

    def get_connection(self, include_db=True):
        """Establish connection using current config."""
        if not self.config:
            raise ValueError("Database configuration not loaded.")
        
        conn_params = {
            "host": self.config["host"],
            "user": self.config["user"],
            "password": self.config["password"],
            "port": self.config["port"]
        }
        if include_db:
            conn_params["database"] = self.config["database"]
            
        return mysql.connector.connect(**conn_params)

    def test_connection(self):
        """Test connection to the MySQL server (without specifying DB)."""
        try:
            conn = self.get_connection(include_db=False)
            if conn.is_connected():
                conn.close()
                return True, "Successfully connected to MySQL server."
        except Error as e:
            return False, str(e)
        return False, "Failed to connect."

    def initialize_database(self):
        """Create database, tables and initial admin if they don't exist."""
        try:
            # 1. Connect without selecting database to run CREATE DATABASE
            conn = self.get_connection(include_db=False)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']}")
            cursor.close()
            conn.close()

            # 2. Connect with selecting database to create tables
            conn = self.get_connection(include_db=True)
            cursor = conn.cursor()

            # Create accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_number VARCHAR(12) PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    pin VARCHAR(64) NOT NULL,
                    account_type VARCHAR(20) NOT NULL,
                    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
                    email VARCHAR(100) UNIQUE NULL,
                    phone VARCHAR(15) NULL,
                    address TEXT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                    account_number VARCHAR(12) NOT NULL,
                    transaction_type VARCHAR(20) NOT NULL,
                    amount DECIMAL(15, 2) NOT NULL,
                    target_account VARCHAR(12) NULL,
                    description VARCHAR(255) NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_number) REFERENCES accounts(account_number) ON DELETE CASCADE
                )
            """)

            # Create admins table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    username VARCHAR(50) PRIMARY KEY,
                    password VARCHAR(64) NOT NULL,
                    name VARCHAR(100) NOT NULL
                )
            """)

            # Check if default admin exists, if not, create one
            cursor.execute("SELECT COUNT(*) FROM admins")
            count = cursor.fetchone()[0]
            if count == 0:
                default_admin_pass = hash_text("admin123")
                cursor.execute(
                    "INSERT INTO admins (username, password, name) VALUES (%s, %s, %s)",
                    ("admin", default_admin_pass, "System Administrator")
                )
                conn.commit()

            cursor.close()
            conn.close()
            return True, "Database initialized successfully."
        except Error as e:
            return False, f"Failed to initialize database: {str(e)}"

    def execute_query(self, query, params=None, fetch=None):
        """
        Execute a query and manage connection cleanup.
        fetch options: 'one', 'all', None (for write queries).
        Returns result or row count.
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            result = None
            if fetch == 'one':
                result = cursor.fetchone()
            elif fetch == 'all':
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
                
            return result
        except Error as e:
            if conn and not fetch:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_transaction(self, queries_with_params):
        """
        Execute multiple write queries in a single database transaction.
        queries_with_params: List of tuples (query_string, params_tuple)
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            conn.start_transaction()
            cursor = conn.cursor()
            
            for query, params in queries_with_params:
                cursor.execute(query, params or ())
                
            conn.commit()
            return True
        except Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
