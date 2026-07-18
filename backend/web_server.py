import os
import sys
from flask import Flask, request, jsonify, send_from_directory

# Add current folder to path to import local modules correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder='../static', static_url_path='')

@app.route('/')
def index():
    """Serve the single page application HTML."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/status', methods=['GET'])
def db_status():
    """Check if the database configuration exists and the database connection is active."""
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    if not config:
        return jsonify({"status": "setup_required", "message": "Database credentials config.json not found."}), 200
    
    db = DBManager(config)
    connected, msg = db.test_connection()
    if not connected:
        return jsonify({"status": "setup_required", "message": f"Connection failed: {msg}"}), 200
        
    return jsonify({"status": "ready", "message": "Database connected successfully."}), 200

@app.route('/api/setup', methods=['POST'])
def db_setup():
    """Setup and initialize the database with user credentials."""
    data = request.json or {}
    host = data.get('host', 'localhost')
    user = data.get('user', 'root')
    password = data.get('password', '')
    port_val = data.get('port', 3306)
    
    try:
        port = int(port_val)
    except ValueError:
        return jsonify({"success": False, "message": "Port must be an integer."}), 400

    config = {
        "host": host,
        "user": user,
        "password": password,
        "port": port,
        "database": "bank_management_db"
    }

    from db_manager import DBManager, save_db_config
    db_temp = DBManager(config)
    connected, msg = db_temp.test_connection()
    if not connected:
        return jsonify({"success": False, "message": f"Connection failed: {msg}"}), 400

    # Save config and initialize database tables
    save_db_config(host, user, password, port)
    init_success, init_msg = db_temp.initialize_database()
    if not init_success:
        return jsonify({"success": False, "message": init_msg}), 500

    return jsonify({"success": True, "message": "Database configured and initialized successfully!"}), 200

@app.route('/api/auth/admin/login', methods=['POST'])
def admin_login():
    """Authenticate staff / admin credentials."""
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    from db_manager import load_db_config, DBManager
    from auth_manager import AuthManager
    
    config = load_db_config()
    if not config:
        return jsonify({"success": False, "message": "Server is not configured."}), 500
        
    db = DBManager(config)
    auth = AuthManager()
    success, msg = auth.login_admin(username, password, db)
    if success:
        return jsonify({"success": True, "message": msg, "user": auth.user_data}), 200
    else:
        return jsonify({"success": False, "message": msg}), 401

@app.route('/api/auth/customer/login', methods=['POST'])
def customer_login():
    """Authenticate customer credentials."""
    data = request.json or {}
    account_number = data.get('account_number')
    pin = data.get('pin')
    
    from db_manager import load_db_config, DBManager
    from auth_manager import AuthManager
    
    config = load_db_config()
    if not config:
        return jsonify({"success": False, "message": "Server is not configured."}), 500
        
    db = DBManager(config)
    auth = AuthManager()
    success, msg = auth.login_customer(account_number, pin, db)
    if success:
        return jsonify({"success": True, "message": msg, "user": auth.user_data}), 200
    else:
        return jsonify({"success": False, "message": msg}), 401

# --- ADMIN ENDPOINTS ---

@app.route('/api/admin/accounts', methods=['POST'])
def admin_create_account():
    """Create a new bank account."""
    data = request.json or {}
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    pin = data.get('pin')
    account_type = data.get('account_type', 'Savings')
    initial_balance_val = data.get('initial_balance', 0.0)
    email = data.get('email') or None
    phone = data.get('phone') or None
    address = data.get('address') or None
    
    if not first_name or not last_name or not pin:
        return jsonify({"success": False, "message": "First name, last name, and PIN are required."}), 400
        
    try:
        initial_balance = float(initial_balance_val)
        if initial_balance < 0:
            return jsonify({"success": False, "message": "Initial balance cannot be negative."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid initial balance."}), 400
        
    from db_manager import load_db_config, DBManager, hash_text
    config = load_db_config()
    db = DBManager(config)
    
    # Generate unique 12-digit account number starting at 100000000001
    try:
        res = db.execute_query("SELECT MAX(account_number) as max_acc FROM accounts", fetch='one')
        if res and res['max_acc']:
            account_number = str(int(res['max_acc']) + 1)
        else:
            account_number = "100000000001"
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to generate account number: {str(e)}"}), 500
        
    hashed_pin = hash_text(pin)
    queries = [
        ("""INSERT INTO accounts 
         (account_number, first_name, last_name, pin, account_type, balance, email, phone, address, status) 
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')""",
         (account_number, first_name, last_name, hashed_pin, account_type, initial_balance, email, phone, address))
    ]
    
    if initial_balance > 0:
        queries.append((
            """INSERT INTO transactions 
            (account_number, transaction_type, amount, target_account, description) 
            VALUES (%s, 'Deposit', %s, NULL, 'Initial Deposit')""",
            (account_number, initial_balance)
        ))
        
    try:
        db.execute_transaction(queries)
        return jsonify({
            "success": True, 
            "message": "Account created successfully!", 
            "account_number": account_number
        }), 200
    except Exception as e:
        if "Duplicate entry" in str(e) and "email" in str(e):
            return jsonify({"success": False, "message": "The email address is already registered to another account."}), 400
        return jsonify({"success": False, "message": f"Failed to create account: {str(e)}"}), 500

@app.route('/api/admin/accounts', methods=['GET'])
def admin_view_accounts():
    """Retrieve all accounts."""
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        rows = db.execute_query("SELECT account_number, first_name, last_name, account_type, balance, status, created_at FROM accounts ORDER BY created_at DESC", fetch='all')
        for r in rows:
            r['created_at'] = str(r['created_at'])
        return jsonify({"success": True, "accounts": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/accounts/search', methods=['GET'])
def admin_search_accounts():
    """Search for accounts by query."""
    q = request.args.get('q', '')
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        query = """
            SELECT account_number, first_name, last_name, account_type, balance, status, created_at 
            FROM accounts 
            WHERE account_number LIKE %s 
               OR first_name LIKE %s 
               OR last_name LIKE %s 
               OR phone LIKE %s
            ORDER BY created_at DESC
        """
        like_q = f"%{q}%"
        rows = db.execute_query(query, (like_q, like_q, like_q, like_q), fetch='all')
        for r in rows:
            r['created_at'] = str(r['created_at'])
        return jsonify({"success": True, "accounts": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/accounts/<account_number>', methods=['PUT'])
def admin_update_account(account_number):
    """Update profile details of an account."""
    data = request.json or {}
    email = data.get('email')
    phone = data.get('phone')
    address = data.get('address')
    
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        acc = db.execute_query("SELECT email, phone, address FROM accounts WHERE account_number = %s", (account_number,), fetch='one')
        if not acc:
            return jsonify({"success": False, "message": "Account not found."}), 404
            
        final_email = email if email is not None else acc['email']
        final_phone = phone if phone is not None else acc['phone']
        final_address = address if address is not None else acc['address']
        
        db.execute_query("UPDATE accounts SET email = %s, phone = %s, address = %s WHERE account_number = %s", 
                         (final_email, final_phone, final_address, account_number))
        return jsonify({"success": True, "message": "Account details updated successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/accounts/<account_number>/status', methods=['PUT'])
def admin_change_status(account_number):
    """Suspend or Activate an account."""
    data = request.json or {}
    new_status = data.get('status')
    if new_status not in ['Active', 'Suspended', 'Closed']:
        return jsonify({"success": False, "message": "Invalid status option."}), 400
        
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        db.execute_query("UPDATE accounts SET status = %s WHERE account_number = %s", (new_status, account_number))
        return jsonify({"success": True, "message": f"Account status updated to '{new_status}' successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/accounts/<account_number>', methods=['DELETE'])
def admin_close_account(account_number):
    """Close an account (support soft or hard delete)."""
    delete_type = request.args.get('type', 'soft')
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        if delete_type == 'soft':
            db.execute_query("UPDATE accounts SET status = 'Closed' WHERE account_number = %s", (account_number,))
            return jsonify({"success": True, "message": "Account marked as Closed (soft-delete)."}), 200
        else:
            db.execute_query("DELETE FROM accounts WHERE account_number = %s", (account_number,))
            return jsonify({"success": True, "message": "Account permanently deleted from database."}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/ledger', methods=['GET'])
def admin_ledger():
    """Retrieve global transaction logs."""
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        query = "SELECT transaction_id, account_number, transaction_type, amount, target_account, description, created_at FROM transactions ORDER BY created_at DESC"
        rows = db.execute_query(query, fetch='all')
        for r in rows:
            r['created_at'] = str(r['created_at'])
        return jsonify({"success": True, "ledger": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# --- CUSTOMER ENDPOINTS ---

@app.route('/api/customer/accounts/<account_number>', methods=['GET'])
def customer_account_info(account_number):
    """Fetch balance and status check for logged-in customer."""
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        acc = db.execute_query("SELECT account_number, first_name, last_name, account_type, balance, status FROM accounts WHERE account_number = %s", (account_number,), fetch='one')
        if not acc:
            return jsonify({"success": False, "message": "Account not found."}), 404
        return jsonify({"success": True, "account": acc}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/customer/accounts/<account_number>/deposit', methods=['POST'])
def customer_deposit(account_number):
    """Credit money into customer account."""
    data = request.json or {}
    amount_val = data.get('amount', 0.0)
    
    try:
        amount = float(amount_val)
        if amount <= 0:
            return jsonify({"success": False, "message": "Amount must be greater than zero."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid deposit amount."}), 400
        
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        acc = db.execute_query("SELECT status FROM accounts WHERE account_number = %s", (account_number,), fetch='one')
        if not acc:
            return jsonify({"success": False, "message": "Account not found."}), 404
        if acc['status'] != 'Active':
            return jsonify({"success": False, "message": f"Transactions not allowed. Account is {acc['status']}."}), 400
            
        queries = [
            ("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, account_number)),
            ("INSERT INTO transactions (account_number, transaction_type, amount, target_account, description) VALUES (%s, 'Deposit', %s, NULL, 'Cash Deposit')", (account_number, amount))
        ]
        db.execute_transaction(queries)
        return jsonify({"success": True, "message": f"Successfully deposited ${amount:.2f}!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/customer/accounts/<account_number>/withdraw', methods=['POST'])
def customer_withdraw(account_number):
    """Debit money from customer account."""
    data = request.json or {}
    amount_val = data.get('amount', 0.0)
    
    try:
        amount = float(amount_val)
        if amount <= 0:
            return jsonify({"success": False, "message": "Amount must be greater than zero."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid withdrawal amount."}), 400
        
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        acc = db.execute_query("SELECT balance, status FROM accounts WHERE account_number = %s", (account_number,), fetch='one')
        if not acc:
            return jsonify({"success": False, "message": "Account not found."}), 404
        if acc['status'] != 'Active':
            return jsonify({"success": False, "message": f"Withdrawal denied. Account status is {acc['status']}."}), 400
        if acc['balance'] < amount:
            return jsonify({"success": False, "message": "Insufficient funds."}), 400
            
        queries = [
            ("UPDATE accounts SET balance = balance - %s WHERE account_number = %s", (amount, account_number)),
            ("INSERT INTO transactions (account_number, transaction_type, amount, target_account, description) VALUES (%s, 'Withdrawal', %s, NULL, 'Cash Withdrawal')", (account_number, amount))
        ]
        db.execute_transaction(queries)
        return jsonify({"success": True, "message": f"Successfully withdrew ${amount:.2f}!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/customer/accounts/<account_number>/transfer', methods=['POST'])
def customer_transfer(account_number):
    """Transfer funds atomically between accounts."""
    data = request.json or {}
    receiver_acc = data.get('receiver_account')
    amount_val = data.get('amount', 0.0)
    
    if not receiver_acc:
        return jsonify({"success": False, "message": "Destination account number is required."}), 400
    if receiver_acc == account_number:
        return jsonify({"success": False, "message": "You cannot transfer to your own account."}), 400
        
    try:
        amount = float(amount_val)
        if amount <= 0:
            return jsonify({"success": False, "message": "Amount must be greater than zero."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid transfer amount."}), 400
        
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        sender = db.execute_query("SELECT balance, first_name, last_name, status FROM accounts WHERE account_number = %s", (account_number,), fetch='one')
        if not sender:
            return jsonify({"success": False, "message": "Sender account not found."}), 404
        if sender['status'] != 'Active':
            return jsonify({"success": False, "message": f"Transfer denied. Your account status is {sender['status']}."}), 400
        if sender['balance'] < amount:
            return jsonify({"success": False, "message": "Insufficient funds."}), 400
            
        receiver = db.execute_query("SELECT first_name, last_name, status FROM accounts WHERE account_number = %s", (receiver_acc,), fetch='one')
        if not receiver:
            return jsonify({"success": False, "message": f"Destination Account {receiver_acc} does not exist."}), 404
        if receiver['status'] != 'Active':
            return jsonify({"success": False, "message": f"Destination Account is currently inactive ({receiver['status']})."}), 400
            
        sender_name = f"{sender['first_name']} {sender['last_name']}"
        receiver_name = f"{receiver['first_name']} {receiver['last_name']}"
        
        queries = [
            ("UPDATE accounts SET balance = balance - %s WHERE account_number = %s", (amount, account_number)),
            ("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, receiver_acc)),
            ("INSERT INTO transactions (account_number, transaction_type, amount, target_account, description) VALUES (%s, 'Transfer Out', %s, %s, %s)", 
             (account_number, amount, receiver_acc, f"Transfer to {receiver_name}")),
            ("INSERT INTO transactions (account_number, transaction_type, amount, target_account, description) VALUES (%s, 'Transfer In', %s, %s, %s)", 
             (receiver_acc, amount, account_number, f"Transfer from {sender_name}"))
        ]
        db.execute_transaction(queries)
        return jsonify({"success": True, "message": f"Successfully transferred ${amount:.2f} to {receiver_name}!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/customer/accounts/<account_number>/statement', methods=['GET'])
def customer_statement(account_number):
    """View transaction statements for logged-in customer."""
    from db_manager import load_db_config, DBManager
    config = load_db_config()
    db = DBManager(config)
    try:
        query = """
            SELECT transaction_id, transaction_type, amount, target_account, description, created_at 
            FROM transactions 
            WHERE account_number = %s 
            ORDER BY created_at DESC
        """
        rows = db.execute_query(query, (account_number,), fetch='all')
        for r in rows:
            r['created_at'] = str(r['created_at'])
        return jsonify({"success": True, "statement": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/customer/accounts/<account_number>/pin', methods=['PUT'])
def customer_change_pin(account_number):
    """Modify customer account 4-digit PIN."""
    data = request.json or {}
    old_pin = data.get('old_pin')
    new_pin = data.get('new_pin')
    
    if not old_pin or not new_pin:
        return jsonify({"success": False, "message": "Current and New PINs are required."}), 400
    if len(new_pin) != 4 or not new_pin.isdigit():
        return jsonify({"success": False, "message": "PIN must be exactly 4 digits."}), 400
        
    from db_manager import load_db_config, DBManager, hash_text
    config = load_db_config()
    db = DBManager(config)
    try:
        acc = db.execute_query("SELECT pin FROM accounts WHERE account_number = %s", (account_number,), fetch='one')
        if not acc:
            return jsonify({"success": False, "message": "Account not found."}), 404
        if acc['pin'] != hash_text(old_pin):
            return jsonify({"success": False, "message": "Incorrect current PIN."}), 400
            
        db.execute_query("UPDATE accounts SET pin = %s WHERE account_number = %s", (hash_text(new_pin), account_number))
        return jsonify({"success": True, "message": "PIN changed successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    # Start on port 5000 by default
    app.run(host='0.0.0.0', port=5000, debug=True)
