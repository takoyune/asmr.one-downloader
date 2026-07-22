import re
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.theme import Theme

APP_VERSION = "v1.2.07072026"
GITHUB_REPO = "takoyune/asmr.one-downloader"

APP_NAME = "ASMR.ONE DOWNLOADER"
WORK_CODE_PATTERN = re.compile(r"(?P<code>(?:(?P<prefix>RJ|VJ))?(?P<id>[\d]{6,}))", re.IGNORECASE)
RJ_PATTERN = WORK_CODE_PATTERN
CHUNK_SIZE = 1048576  # 1MB chunks for smoother throttling and progress
CONFIG_FILE = Path("config.json")
DB_FILE = Path("history.db")
LOG_FILE = Path("singularity.log")

def normalize_work_code(value: str) -> Optional[str]:
    """Return a normalized DLsite work code, preserving RJ/VJ prefixes when present."""
    match = WORK_CODE_PATTERN.search(value)
    if not match:
        return None
    return match.group("code").upper()

def get_localized_tag_name(tag: Any, priority_list: Optional[List[str]] = None) -> str:
    """Extract tag name according to language priority list (e.g. ['ja-jp', 'en-us', 'zh-cn'])."""
    if isinstance(tag, str):
        return tag
    if not isinstance(tag, dict):
        return str(tag)
    
    if not priority_list:
        priority_list = ["ja-jp", "en-us", "zh-cn"]

    i18n = tag.get('i18n')
    if isinstance(i18n, dict):
        for lang in priority_list:
            lang_clean = lang.lower().strip()
            for key, val in i18n.items():
                key_clean = key.lower().strip()
                if key_clean == lang_clean or key_clean.startswith(lang_clean) or lang_clean.startswith(key_clean):
                    if isinstance(val, dict) and val.get('name'):
                        return val['name']
    
    return tag.get('name', 'Unknown')

TKINTER_AVAILABLE = False
try:
    import tkinter as tk
    from tkinter import filedialog, Tk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

HOSTNAME_MIRRORS = [
    "https://api.asmr-200.com",
    "https://api.asmr.one",
    "https://api.asmr-100.com",
    "https://api.asmr-300.com"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Configure logging with RotatingFileHandler (max 5MB, keep 3 backups)
log_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
)
log_formatter = logging.Formatter(
    fmt='%(asctime)s | %(levelname)s | [%(name)s] %(message)s', 
    datefmt='%H:%M:%S'
)
log_handler.setFormatter(log_formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# Remove existing handlers if any (useful during hot reloads or multiple imports)
for h in root_logger.handlers[:]:
    root_logger.removeHandler(h)
root_logger.addHandler(log_handler)

# Create console with theme
theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "dim": "dim white",
    "hack": "bright_green",
    "matrix": "bright_green",
    "glitch": "bright_magenta",
    "cyber": "bright_cyan",
    "neon": "bright_yellow",
    "gold": "rgb(255,215,0)"
})
console = Console(theme=theme)
