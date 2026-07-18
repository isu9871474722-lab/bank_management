import os
import re
import colorama
from colorama import Fore, Style
from tabulate import tabulate

# Initialize colorama
colorama.init(autoreset=True)

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Print a styled header for menus and sections."""
    print("\n" + Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.YELLOW + Style.BRIGHT + f"{title.center(60)}")
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)

def print_menu_options(options):
    """Print numbered menu options styled nicely."""
    for key, val in options.items():
        print(Fore.WHITE + Style.BRIGHT + f"  [{key}] " + Fore.LIGHTWHITE_EX + f"{val}")
    print()

def print_success(message):
    """Print a success message in green."""
    print(Fore.GREEN + Style.BRIGHT + f"\n[SUCCESS] {message}")

def print_error(message):
    """Print an error message in red."""
    print(Fore.RED + Style.BRIGHT + f"\n[ERROR] {message}")

def print_info(message):
    """Print an informational message in cyan."""
    print(Fore.CYAN + f"\n[INFO] {message}")

def prompt_non_empty(prompt_text):
    """Prompt user for a non-empty string."""
    while True:
        val = input(Fore.BLUE + Style.BRIGHT + prompt_text).strip()
        if val:
            return val
        print_error("Input cannot be empty. Please try again.")

def prompt_number(prompt_text, num_type=int, min_val=None, max_val=None):
    """Prompt user for a number, validating type and range constraints."""
    while True:
        val_str = input(Fore.BLUE + Style.BRIGHT + prompt_text).strip()
        try:
            val = num_type(val_str)
            if min_val is not None and val < min_val:
                print_error(f"Value must be at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print_error(f"Value must be at most {max_val}.")
                continue
            return val
        except ValueError:
            type_name = "number" if num_type == float else "integer"
            print_error(f"Invalid input. Please enter a valid {type_name}.")

def prompt_email(prompt_text, optional=False):
    """Prompt user for a valid email format, allowing optional empty value."""
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    while True:
        val = input(Fore.BLUE + Style.BRIGHT + prompt_text).strip()
        if not val and optional:
            return None
        if re.match(regex, val):
            return val
        print_error("Invalid email format. E.g., user@example.com")

def prompt_phone(prompt_text, optional=False):
    """Prompt user for a valid phone format (10-15 digits), allowing optional empty value."""
    regex = r'^\+?[0-9]{10,15}$'
    while True:
        val = input(Fore.BLUE + Style.BRIGHT + prompt_text).strip()
        if not val and optional:
            return None
        if re.match(regex, val):
            return val
        print_error("Invalid phone format. Must be 10-15 digits (e.g., +1234567890).")

def prompt_pin(prompt_text):
    """Prompt user for a 4-digit PIN."""
    while True:
        val = input(Fore.BLUE + Style.BRIGHT + prompt_text).strip()
        if len(val) == 4 and val.isdigit():
            return val
        print_error("Invalid PIN. PIN must be exactly 4 digits.")

def prompt_choice(choices, prompt_text="Enter choice: "):
    """Prompt user for a choice from a given list of strings."""
    while True:
        val = input(Fore.BLUE + Style.BRIGHT + prompt_text).strip()
        if val in choices:
            return val
        print_error(f"Invalid choice. Please select from: {', '.join(choices)}")

def render_table(data, headers, table_format="grid"):
    """Render a table with tabulate formatted output."""
    if not data:
        print_info("No records found.")
        return
    print("\n" + Fore.WHITE + tabulate(data, headers=headers, tablefmt=table_format))
