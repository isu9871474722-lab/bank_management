import sys
from colorama import Style
import cli_renderer as cli
from db_manager import DBManager, load_db_config, save_db_config
from auth_manager import AuthManager

def setup_wizard():
    """Run an automated setup wizard to gather MySQL credentials on first run."""
    cli.clear_screen()
    cli.print_header("Bank Database Setup Wizard")
    cli.print_info("No database configuration detected. Let's configure your local MySQL credentials.")
    
    while True:
        host = input(cli.Fore.BLUE + Style.BRIGHT + "Enter MySQL Host [localhost]: ").strip() or "localhost"
        user = input(cli.Fore.BLUE + Style.BRIGHT + "Enter MySQL Username [root]: ").strip() or "root"
        password = input(cli.Fore.BLUE + Style.BRIGHT + "Enter MySQL Password: ").strip()
        port_str = input(cli.Fore.BLUE + Style.BRIGHT + "Enter MySQL Port [3306]: ").strip() or "3306"
        
        try:
            port = int(port_str)
        except ValueError:
            cli.print_error("Invalid port. Port number must be an integer.")
            continue
            
        config = {
            "host": host,
            "user": user,
            "password": password,
            "port": port,
            "database": "bank_management_db"
        }
        
        db_temp = DBManager(config)
        cli.print_info("Testing connection to MySQL server...")
        success, msg = db_temp.test_connection()
        
        if success:
            save_db_config(host, user, password, port)
            cli.print_success("Connection details saved successfully!")
            
            cli.print_info("Initializing database and tables...")
            init_success, init_msg = db_temp.initialize_database()
            if init_success:
                cli.print_success(init_msg)
                input(cli.Fore.CYAN + "\nPress Enter to continue to the application...")
                break
            else:
                cli.print_error(init_msg)
        else:
            cli.print_error(f"Connection test failed: {msg}")
            retry = cli.prompt_choice(["Y", "N", "y", "n"], "Would you like to try configuring credentials again? (y/n): ").upper()
            if retry != "Y":
                cli.print_info("Exiting setup wizard.")
                sys.exit(1)

def handle_admin_login(db_manager, auth_manager):
    """Admin login handler."""
    cli.clear_screen()
    cli.print_header("Staff / Admin Login")
    username = cli.prompt_non_empty("Enter Username: ")
    password = input(cli.Fore.BLUE + Style.BRIGHT + "Enter Password: ").strip()
    
    success, msg = auth_manager.login_admin(username, password, db_manager)
    if success:
        cli.print_success(msg)
        input(cli.Fore.CYAN + "\nPress Enter to open Dashboard...")
        admin_dashboard(db_manager, auth_manager)
    else:
        cli.print_error(msg)
        input(cli.Fore.CYAN + "\nPress Enter to return to main menu...")

def handle_customer_login(db_manager, auth_manager):
    """Customer login handler."""
    cli.clear_screen()
    cli.print_header("Customer Login")
    acc_num = cli.prompt_non_empty("Enter 12-Digit Account Number: ")
    pin = cli.prompt_pin("Enter 4-Digit PIN: ")
    
    success, msg = auth_manager.login_customer(acc_num, pin, db_manager)
    if success:
        cli.print_success(msg)
        input(cli.Fore.CYAN + "\nPress Enter to open Dashboard...")
        customer_dashboard(db_manager, auth_manager)
    else:
        cli.print_error(msg)
        input(cli.Fore.CYAN + "\nPress Enter to return to main menu...")

def admin_dashboard(db_manager, auth_manager):
    """Admin Operations Menu."""
    options = {
        "1": "Create New Account",
        "2": "View All Accounts",
        "3": "Search Account",
        "4": "Update Account Holder Details",
        "5": "Modify Account Status (Suspend/Activate)",
        "6": "Close/Delete Account",
        "7": "Global Transaction Ledger",
        "8": "Logout"
    }
    
    while auth_manager.role == 'admin':
        cli.clear_screen()
        cli.print_header(f"Admin / Staff Dashboard - {auth_manager.user_data['name']}")
        cli.print_menu_options(options)
        
        choice = cli.prompt_choice(list(options.keys()))
        import bank_operations as ops
        
        if choice == "1":
            ops.admin_create_account(db_manager)
        elif choice == "2":
            ops.admin_view_all_accounts(db_manager)
        elif choice == "3":
            ops.admin_search_accounts(db_manager)
        elif choice == "4":
            ops.admin_update_account(db_manager)
        elif choice == "5":
            ops.admin_change_status(db_manager)
        elif choice == "6":
            ops.admin_close_account(db_manager)
        elif choice == "7":
            ops.admin_view_global_ledger(db_manager)
        elif choice == "8":
            auth_manager.logout()
            cli.print_success("Admin logged out successfully.")
            
        if choice != "8":
            input(cli.Fore.CYAN + "\nPress Enter to return to dashboard...")

def customer_dashboard(db_manager, auth_manager):
    """Customer Operations Menu."""
    options = {
        "1": "Check Balance & Status",
        "2": "Deposit Funds",
        "3": "Withdraw Funds",
        "4": "Transfer Funds",
        "5": "View Account Statement",
        "6": "Change PIN",
        "7": "Logout"
    }
    
    acc_num = auth_manager.current_user
    while auth_manager.role == 'customer':
        cli.clear_screen()
        cli.print_header(f"Customer Dashboard - Account {acc_num}")
        cli.print_menu_options(options)
        
        choice = cli.prompt_choice(list(options.keys()))
        import bank_operations as ops
        
        if choice == "1":
            ops.customer_check_balance(acc_num, db_manager)
        elif choice == "2":
            ops.customer_deposit(acc_num, db_manager)
        elif choice == "3":
            ops.customer_withdraw(acc_num, db_manager)
        elif choice == "4":
            ops.customer_transfer(acc_num, db_manager)
        elif choice == "5":
            ops.customer_view_statement(acc_num, db_manager)
        elif choice == "6":
            ops.customer_change_pin(acc_num, db_manager)
        elif choice == "7":
            auth_manager.logout()
            cli.print_success("Customer logged out successfully.")
            
        if choice != "7":
            input(cli.Fore.CYAN + "\nPress Enter to return to dashboard...")

def main():
    # Verify DB Configuration exists and is correct
    config = load_db_config()
    if not config:
        setup_wizard()
        config = load_db_config()
    else:
        # Configuration exists, but let's make sure it's valid
        db = DBManager(config)
        connected, _ = db.test_connection()
        if not connected:
            cli.print_error("Saved database credentials failed to connect.")
            retry = cli.prompt_choice(["Y", "N", "y", "n"], "Run MySQL Setup Wizard? (y/n): ").upper()
            if retry == "Y":
                setup_wizard()
                config = load_db_config()
            else:
                cli.print_info("Exiting bank system.")
                sys.exit(1)
        else:
            # Successfully connected, let's verify database initialization (tables created)
            _, _ = db.initialize_database()

    # Re-initialize DB Manager and Auth Manager
    db_manager = DBManager(config)
    auth_manager = AuthManager()

    # Welcome Menu Loop
    welcome_options = {
        "1": "Staff / Admin Login",
        "2": "Customer Portal Login",
        "3": "Exit System"
    }

    while True:
        cli.clear_screen()
        cli.print_header("Apex Banking Corporation")
        cli.print_menu_options(welcome_options)
        
        choice = cli.prompt_choice(list(welcome_options.keys()))
        
        if choice == "1":
            handle_admin_login(db_manager, auth_manager)
        elif choice == "2":
            handle_customer_login(db_manager, auth_manager)
        elif choice == "3":
            cli.clear_screen()
            cli.print_header("Thank You")
            cli.print_success("Thank you for banking with Apex Banking Corporation. Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    main()
