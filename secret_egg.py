import time
import sys
import os

def print_slow(text: str, delay: float = 0.05) -> None:
    """
    Prints text to the console one character at a time.
    
    Args:
        text (str): The text to print.
        delay (float): The delay between characters in seconds.
    """
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)

def clear_screen() -> None:
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def set_console_title(title: str) -> None:
    """Sets the console window title (Windows only)."""
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(title)

class Colors:
    """ANSI escape codes for terminal colors."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

if __name__ == "__main__":
    # Example usage as a utility module
    clear_screen()
    set_console_title("Terminal Utility")
    print_slow(f"{Colors.GREEN}[INFO] System utility module loaded successfully.{Colors.RESET}\n", 0.03)