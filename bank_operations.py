from db_manager import hash_text
import cli_renderer as cli
from colorama import Style


# --- ADMIN OPERATIONS ---

def admin_create_account(db_manager):
    """Admin workflow to create a new customer account."""
    cli.print_header("Open New Account")
    
    first_name = cli.prompt_non_empty("Enter First Name: ")
    last_name = cli.prompt_non_empty("Enter Last Name: ")
    pin = cli.prompt_pin("Enter 4-Digit Temporary PIN: ")
    
    print("\nAccount Types:")
    print("  [1] Savings")
    print("  [2] Current")
    type_choice = cli.prompt_choice(["1", "2"], "Select Account Type: ")
    account_type = "Savings" if type_choice == "1" else "Current"
    
    initial_balance = cli.prompt_number("Enter Initial Deposit Amount: $", num_type=float, min_val=0.0)
    email = cli.prompt_email("Enter Email (Optional, press Enter to skip): ", optional=True)
    phone = cli.prompt_phone("Enter Phone Number (Optional, press Enter to skip): ", optional=True)
    
    address = input(cli.Fore.BLUE + Style_Bright_String("Enter Address (Optional, press Enter to skip): ")).strip()
    if not address:
        address = None

    # Generate unique 12-digit account number starting at 100000000001
    try:
        res = db_manager.execute_query("SELECT MAX(account_number) as max_acc FROM accounts", fetch='one')
        if res and res['max_acc']:
            account_number = str(int(res['max_acc']) + 1)
        else:
            account_number = "100000000001"
    except Exception as e:
        cli.print_error(f"Failed to generate account number: {str(e)}")
        return

    hashed_pin = hash_text(pin)
    
    queries = []
    # 1. Insert into accounts
    queries.append((
        """INSERT INTO accounts 
        (account_number, first_name, last_name, pin, account_type, balance, email, phone, address, status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')""",
        (account_number, first_name, last_name, hashed_pin, account_type, initial_balance, email, phone, address)
    ))
    
    # 2. Insert initial transaction if balance > 0
    if initial_balance > 0:
        queries.append((
            """INSERT INTO transactions 
            (account_number, transaction_type, amount, target_account, description) 
            VALUES (%s, 'Deposit', %s, NULL, 'Initial Deposit')""",
            (account_number, initial_balance)
        ))
        
    try:
        db_manager.execute_transaction(queries)
        cli.print_success(f"Account created successfully!")
        print(f"  Account Number: {account_number}")
        print(f"  Account Holder: {first_name} {last_name}")
        print(f"  Account Type:   {account_type}")
        print(f"  Initial Balance: ${initial_balance:.2f}")
    except Exception as e:
        # Check for duplicate email error
        if "Duplicate entry" in str(e) and "email" in str(e):
            cli.print_error("The email address provided is already registered to another account.")
        else:
            cli.print_error(f"Failed to create account: {str(e)}")


def admin_view_all_accounts(db_manager):
    """Admin workflow to view all bank accounts in a table."""
    cli.print_header("All Registered Bank Accounts")
    
    try:
        query = "SELECT account_number, first_name, last_name, account_type, balance, status, created_at FROM accounts ORDER BY created_at DESC"
        rows = db_manager.execute_query(query, fetch='all')
        
        if not rows:
            cli.print_info("No bank accounts registered yet.")
            return
            
        headers = ["Account No", "Name", "Type", "Balance", "Status", "Created At"]
        table_data = []
        for r in rows:
            table_data.append([
                r['account_number'],
                f"{r['first_name']} {r['last_name']}",
                r['account_type'],
                f"${r['balance']:.2f}",
                r['status'],
                str(r['created_at'])
            ])
        cli.render_table(table_data, headers)
    except Exception as e:
        cli.print_error(f"Failed to retrieve accounts: {str(e)}")


def admin_search_accounts(db_manager):
    """Admin workflow to search for accounts."""
    cli.print_header("Search Bank Accounts")
    search_term = cli.prompt_non_empty("Enter Search Term (Name, Acc Number, or Phone): ")
    
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
        like_term = f"%{search_term}%"
        rows = db_manager.execute_query(query, (like_term, like_term, like_term, like_term), fetch='all')
        
        if not rows:
            cli.print_info(f"No accounts found matching '{search_term}'.")
            return
            
        headers = ["Account No", "Name", "Type", "Balance", "Status", "Created At"]
        table_data = []
        for r in rows:
            table_data.append([
                r['account_number'],
                f"{r['first_name']} {r['last_name']}",
                r['account_type'],
                f"${r['balance']:.2f}",
                r['status'],
                str(r['created_at'])
            ])
        cli.render_table(table_data, headers)
    except Exception as e:
        cli.print_error(f"Search failed: {str(e)}")


def admin_update_account(db_manager):
    """Admin workflow to update account holder details."""
    cli.print_header("Update Customer Account Details")
    acc_num = cli.prompt_non_empty("Enter Account Number: ")
    
    try:
        # Check if account exists
        acc = db_manager.execute_query("SELECT email, phone, address, first_name, last_name FROM accounts WHERE account_number = %s", (acc_num,), fetch='one')
        if not acc:
            cli.print_error(f"Account {acc_num} not found.")
            return
            
        print(f"\nEditing account of: {acc['first_name']} {acc['last_name']}")
        print(f"Current Email:   {acc['email'] or 'N/A'}")
        print(f"Current Phone:   {acc['phone'] or 'N/A'}")
        print(f"Current Address: {acc['address'] or 'N/A'}\n")
        
        email = cli.prompt_email("Enter New Email (press Enter to keep current): ", optional=True)
        phone = cli.prompt_phone("Enter New Phone Number (press Enter to keep current): ", optional=True)
        address = input(cli.Fore.BLUE + Style_Bright_String("Enter New Address (press Enter to keep current): ")).strip()
        
        # Decide values
        final_email = email if email is not None else acc['email']
        final_phone = phone if phone is not None else acc['phone']
        final_address = address if address != "" else acc['address']
        
        update_query = """
            UPDATE accounts 
            SET email = %s, phone = %s, address = %s 
            WHERE account_number = %s
        """
        db_manager.execute_query(update_query, (final_email, final_phone, final_address, acc_num))
        cli.print_success("Account details updated successfully!")
    except Exception as e:
        cli.print_error(f"Failed to update account: {str(e)}")


def admin_change_status(db_manager):
    """Admin workflow to change account status (Active, Suspended, Closed)."""
    cli.print_header("Modify Account Status")
    acc_num = cli.prompt_non_empty("Enter Account Number: ")
    
    try:
        acc = db_manager.execute_query("SELECT status, first_name, last_name FROM accounts WHERE account_number = %s", (acc_num,), fetch='one')
        if not acc:
            cli.print_error(f"Account {acc_num} not found.")
            return
            
        print(f"\nAccount Holder: {acc['first_name']} {acc['last_name']}")
        print(f"Current Status: {acc['status']}")
        
        print("\nSelect New Status:")
        print("  [1] Active")
        print("  [2] Suspended")
        print("  [3] Closed")
        
        choice = cli.prompt_choice(["1", "2", "3"], "Select Choice: ")
        status_map = {"1": "Active", "2": "Suspended", "3": "Closed"}
        new_status = status_map[choice]
        
        db_manager.execute_query("UPDATE accounts SET status = %s WHERE account_number = %s", (new_status, acc_num))
        cli.print_success(f"Account status updated to '{new_status}' successfully!")
    except Exception as e:
        cli.print_error(f"Failed to modify status: {str(e)}")


def admin_close_account(db_manager):
    """Admin workflow to close an account (Soft-delete or Hard-delete)."""
    cli.print_header("Close Customer Account")
    acc_num = cli.prompt_non_empty("Enter Account Number: ")
    
    try:
        acc = db_manager.execute_query("SELECT status, first_name, last_name FROM accounts WHERE account_number = %s", (acc_num,), fetch='one')
        if not acc:
            cli.print_error(f"Account {acc_num} not found.")
            return
            
        print(f"\nAccount Holder: {acc['first_name']} {acc['last_name']}")
        print(f"Current Status: {acc['status']}")
        
        print("\nChoose Closure Type:")
        print("  [1] Soft-Delete (Update status to 'Closed', preserving history)")
        print("  [2] Hard-Delete (Permanently delete from database - WARNING: Deletes history!)")
        
        choice = cli.prompt_choice(["1", "2"], "Select Choice: ")
        
        confirm = cli.prompt_choice(["Y", "N", "y", "n"], "Are you absolutely sure? (y/n): ").upper()
        if confirm != "Y":
            cli.print_info("Operation cancelled.")
            return
            
        if choice == "1":
            db_manager.execute_query("UPDATE accounts SET status = 'Closed' WHERE account_number = %s", (acc_num,))
            cli.print_success("Account soft-deleted successfully (status marked 'Closed').")
        else:
            db_manager.execute_query("DELETE FROM accounts WHERE account_number = %s", (acc_num,))
            cli.print_success("Account and associated transactions permanently removed from database.")
    except Exception as e:
        cli.print_error(f"Failed to close account: {str(e)}")


def admin_view_global_ledger(db_manager):
    """Admin workflow to view all transactions across the system."""
    cli.print_header("Global Transaction Ledger")
    
    try:
        query = "SELECT transaction_id, account_number, transaction_type, amount, target_account, description, created_at FROM transactions ORDER BY created_at DESC"
        rows = db_manager.execute_query(query, fetch='all')
        
        if not rows:
            cli.print_info("No transactions logged in the system.")
            return
            
        headers = ["Tx ID", "Account No", "Type", "Amount", "Target Acc", "Description", "Timestamp"]
        table_data = []
        for r in rows:
            table_data.append([
                r['transaction_id'],
                r['account_number'],
                r['transaction_type'],
                f"${r['amount']:.2f}",
                r['target_account'] or "N/A",
                r['description'] or "",
                str(r['created_at'])
            ])
        cli.render_table(table_data, headers)
    except Exception as e:
        cli.print_error(f"Failed to retrieve ledger: {str(e)}")


# --- CUSTOMER OPERATIONS ---

def customer_check_balance(account_number, db_manager):
    """Check customer account balance and details."""
    cli.print_header("Account Balance Enquiry")
    
    try:
        acc = db_manager.execute_query("SELECT balance, status, account_type FROM accounts WHERE account_number = %s", (account_number,), fetch='one')
        if acc:
            print(f"\nAccount Number: {account_number}")
            print(f"Account Type:   {acc['account_type']}")
            print(f"Account Status: {acc['status']}")
            print(cli.Fore.GREEN + Style_Bright_String(f"Available Balance: ${acc['balance']:.2f}"))
        else:
            cli.print_error("Failed to retrieve balance. Account record missing.")
    except Exception as e:
        cli.print_error(f"Database error: {str(e)}")


def customer_deposit(account_number, db_manager):
    """Deposit money into a customer account."""
    cli.print_header("Deposit Funds")
    
    amount = cli.prompt_number("Enter amount to deposit: $", num_type=float, min_val=0.01)
    
    queries = [
        ("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, account_number)),
        ("INSERT INTO transactions (account_number, transaction_type, amount, target_account, description) VALUES (%s, 'Deposit', %s, NULL, 'Cash Deposit')", (account_number, amount))
    ]
    
    try:
        db_manager.execute_transaction(queries)
        cli.print_success(f"Successfully deposited ${amount:.2f}!")
        
        # Display new balance
        acc = db_manager.execute_query("SELECT balance FROM accounts WHERE account_number = %s", (account_number,), fetch='one')
        if acc:
            print(cli.Fore.GREEN + Style_Bright_String(f"New Balance: ${acc['balance']:.2f}"))
    except Exception as e:
        cli.print_error(f"Deposit failed: {str(e)}")


def customer_withdraw(account_number, db_manager):
    """Withdraw money from a customer account."""
    cli.print_header("Withdraw Funds")
    
    amount = cli.prompt_number("Enter amount to withdraw: $", num_type=float, min_val=0.01)
    
    try:
        acc = db_manager.execute_query("SELECT balance, status FROM accounts WHERE account_number = %s", (account_number,), fetch='one')
        if not acc:
            cli.print_error("Account not found.")
            return
            
        if acc['balance'] < amount:
            cli.print_error(f"Insufficient funds. Your current balance is ${acc['balance']:.2f}.")
            return
            
        queries = [
            ("UPDATE accounts SET balance = balance - %s WHERE account_number = %s", (amount, account_number)),
            ("INSERT INTO transactions (account_number, transaction_type, amount, target_account, description) VALUES (%s, 'Withdrawal', %s, NULL, 'Cash Withdrawal')", (account_number, amount))
        ]
        
        db_manager.execute_transaction(queries)
        cli.print_success(f"Successfully withdrew ${amount:.2f}!")
        print(cli.Fore.GREEN + Style_Bright_String(f"Remaining Balance: ${acc['balance'] - amount:.2f}"))
    except Exception as e:
        cli.print_error(f"Withdrawal failed: {str(e)}")


def customer_transfer(sender_acc, db_manager):
    """Transfer funds from one customer account to another (Atomic Transaction)."""
    cli.print_header("Transfer Funds")
    
    receiver_acc = cli.prompt_non_empty("Enter Destination Account Number: ")
    if receiver_acc == sender_acc:
        cli.print_error("You cannot transfer money to your own account.")
        return
        
    amount = cli.prompt_number("Enter amount to transfer: $", num_type=float, min_val=0.01)
    
    try:
        # Validate sender and fetch details
        sender = db_manager.execute_query("SELECT balance, first_name, last_name, status FROM accounts WHERE account_number = %s", (sender_acc,), fetch='one')
        if not sender:
            cli.print_error("Sender account not found.")
            return
            
        if sender['status'] != 'Active':
            cli.print_error("Your account status must be Active to make transfers.")
            return
            
        if sender['balance'] < amount:
            cli.print_error(f"Insufficient funds. Available balance: ${sender['balance']:.2f}")
            return
            
        # Validate receiver and fetch details
        receiver = db_manager.execute_query("SELECT first_name, last_name, status FROM accounts WHERE account_number = %s", (receiver_acc,), fetch='one')
        if not receiver:
            cli.print_error(f"Destination Account {receiver_acc} does not exist.")
            return
            
        if receiver['status'] != 'Active':
            cli.print_error(f"Destination Account is currently inactive ({receiver['status']}).")
            return
            
        sender_name = f"{sender['first_name']} {sender['last_name']}"
        receiver_name = f"{receiver['first_name']} {receiver['last_name']}"
        
        # Prepare atomic queries
        queries = [
            # 1. Deduct sender balance
            ("UPDATE accounts SET balance = balance - %s WHERE account_number = %s", (amount, sender_acc)),
            # 2. Credit receiver balance
            ("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, receiver_acc)),
            # 3. Log transfer out for sender
            ("INSERT INTO transactions (account_number, transaction_type, amount, target_account, description) VALUES (%s, 'Transfer Out', %s, %s, %s)", 
             (sender_acc, amount, receiver_acc, f"Transfer to {receiver_name}")),
            # 4. Log transfer in for receiver
            ("INSERT INTO transactions (account_number, transaction_type, amount, target_account, description) VALUES (%s, 'Transfer In', %s, %s, %s)", 
             (receiver_acc, amount, sender_acc, f"Transfer from {sender_name}"))
        ]
        
        db_manager.execute_transaction(queries)
        cli.print_success(f"Successfully transferred ${amount:.2f} to {receiver_name} ({receiver_acc})!")
        print(cli.Fore.GREEN + Style_Bright_String(f"Your remaining balance: ${sender['balance'] - amount:.2f}"))
    except Exception as e:
        cli.print_error(f"Transfer failed: {str(e)}")


def customer_view_statement(account_number, db_manager):
    """View transactions related to this customer account."""
    cli.print_header("Account Transaction Statement")
    
    try:
        query = """
            SELECT transaction_id, transaction_type, amount, target_account, description, created_at 
            FROM transactions 
            WHERE account_number = %s 
            ORDER BY created_at DESC
        """
        rows = db_manager.execute_query(query, (account_number,), fetch='all')
        
        if not rows:
            cli.print_info("No transactions found on this account.")
            return
            
        headers = ["Tx ID", "Type", "Amount", "Target Acc", "Description", "Timestamp"]
        table_data = []
        for r in rows:
            # Color coding transaction type
            tx_type = r['transaction_type']
            if tx_type in ['Deposit', 'Transfer In']:
                tx_type_styled = cli.Fore.GREEN + tx_type
            else:
                tx_type_styled = cli.Fore.RED + tx_type
                
            table_data.append([
                r['transaction_id'],
                tx_type_styled,
                f"${r['amount']:.2f}",
                r['target_account'] or "N/A",
                r['description'] or "",
                str(r['created_at'])
            ])
        cli.render_table(table_data, headers)
    except Exception as e:
        cli.print_error(f"Failed to fetch statement: {str(e)}")


def customer_change_pin(account_number, db_manager):
    """Change customer account 4-digit PIN."""
    cli.print_header("Change Account PIN")
    
    old_pin = cli.prompt_pin("Enter Current PIN: ")
    hashed_old = hash_text(old_pin)
    
    try:
        acc = db_manager.execute_query("SELECT pin FROM accounts WHERE account_number = %s", (account_number,), fetch='one')
        if not acc or acc['pin'] != hashed_old:
            cli.print_error("Incorrect current PIN.")
            return
            
        new_pin = cli.prompt_pin("Enter New 4-Digit PIN: ")
        confirm_pin = cli.prompt_pin("Confirm New 4-Digit PIN: ")
        
        if new_pin != confirm_pin:
            cli.print_error("PIN mismatch. PINs do not match.")
            return
            
        hashed_new = hash_text(new_pin)
        db_manager.execute_query("UPDATE accounts SET pin = %s WHERE account_number = %s", (hashed_new, account_number))
        cli.print_success("PIN changed successfully!")
    except Exception as e:
        cli.print_error(f"Failed to change PIN: {str(e)}")

def Style_Bright_String(text):
    """Utility to style strings with Fore + Style.BRIGHT."""
    return Style.BRIGHT + text
