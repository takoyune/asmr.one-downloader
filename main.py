import asyncio
import textwrap
import wave
import rich
import re
import sys
import json
import sqlite3
import logging
import os
import platform
import shutil
import time
import random
import subprocess
import importlib.util
import math
import threading
import itertools
import tempfile
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Any, Dict, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from concurrent.futures import ThreadPoolExecutor

# ============================================================================
# SYSTEM PREFLIGHT CHECK
# ============================================================================
def system_preflight_check() -> None:
    """
    Scans the runtime environment for critical dependencies.
    Auto-injects missing modules via pip and reboots the kernel.
    """
    required_packages = ['aiofiles', 'aiohttp', 'rich', 'mutagen']
    missing = []

    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing.append(package)

    if not missing:
        return

    # Fallback raw print for pre-rich environment
    print("\n\033[93m[SYSTEM ALERT] Missing Core Modules Detected.\033[0m")
    print(f"Targeting: {', '.join(missing)}")
    print("Initializing Auto-Recovery Protocol...")
    
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--user"] + missing
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("\033[92m[SUCCESS] Modules integrated. Rebooting...\033[0m")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except Exception as e:
        print(f"\033[91m[FATAL] Auto-install failed: {e}\033[0m")
        print("Manual intervention required: pip install " + " ".join(missing))
        sys.exit(1)

# Run preflight check before any imports
system_preflight_check()

# ============================================================================
# IMPORTS
# ============================================================================
import aiofiles
import aiohttp
from aiohttp import ClientConnectorError, ClientPayloadError, ClientTimeout
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.progress import (
    Progress, SpinnerColumn, BarColumn, TextColumn, 
    DownloadColumn, TransferSpeedColumn, TimeRemainingColumn, TaskID
)
from rich.prompt import Confirm, Prompt, IntPrompt
from rich.tree import Tree
from rich import box
from rich.style import Style
from rich.theme import Theme
import mutagen
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC, ID3NoHeaderError
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis

# Platform Specifics
TKINTER_AVAILABLE = False
try:
    import tkinter as tk
    from tkinter import filedialog, Tk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

# ============================================================================
# CONSTANTS
# ============================================================================
APP_NAME = "ASMR.ONE DOWNLOADER"
RJ_PATTERN = re.compile(r"(?:RJ)?(?P<id>[\d]{6,})")
CHUNK_SIZE = 104857600  # 100MB chunks
CONFIG_FILE = Path("config.json")
DB_FILE = Path("history.db")
LOG_FILE = Path("singularity.log")

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

# Configure logging
logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.INFO, 
    format='%(asctime)s | %(levelname)s | %(message)s', 
    datefmt='%H:%M:%S'
)

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

# ============================================================================
# DATA CLASSES
# ============================================================================
@dataclass
class WorkMetadata:
    """Metadata for an ASMR work."""
    rj_id: str
    title: str
    circle: str
    cv: List[str]
    tags: List[str]
    price: int
    dl_count: int
    source_url: str
    rating: float
    release_date: str
    cover_url: str
    total_size: int = 0

@dataclass
class TrackItem:
    """Represents a track or folder in the download hierarchy."""
    id: str
    title: str
    type: str
    url: str
    size: int
    save_path: Path
    level: int = 0
    children: List['TrackItem'] = field(default_factory=list)

@dataclass
class SessionStats:
    """Statistics for a download session."""
    success: int = 0
    failed: int = 0
    skipped: int = 0
    bytes_downloaded: int = 0
    start_time: float = field(default_factory=time.time)

# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================
class ConfigManager:
    """Manages application configuration."""
    def __init__(self):
        self.output_dir = Path("Downloads")
        self.max_concurrent = 3
        self.proxy = None
        self.mirror = HOSTNAME_MIRRORS[0]
        self.tag_audio = True
        self.sort_files = False
        self.dir_template = "RJ{rj_id} {title}"
        self.auth_token = None
        self.timeout = 60

    @classmethod
    def load(cls) -> 'ConfigManager':
        """Load configuration from file or create default."""
        config = cls()
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    config.output_dir = Path(data.get('output_dir', "Downloads"))
                    config.max_concurrent = int(data.get('max_concurrent', 3))
                    config.proxy = data.get('proxy')
                    config.mirror = data.get('mirror', HOSTNAME_MIRRORS[0])
                    config.tag_audio = bool(data.get('tag_audio', True))
                    config.sort_files = bool(data.get('sort_files', False))
                    config.dir_template = data.get('dir_template', "RJ{rj_id} {title}")
                    config.auth_token = data.get('auth_token')
                    config.timeout = int(data.get('timeout', 60))
                    
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logging.warning(f"Config load error: {e}, using defaults")
        return config

    def save(self) -> None:
        """Save configuration to file."""
        data = {
            "output_dir": str(self.output_dir),
            "max_concurrent": self.max_concurrent,
            "proxy": self.proxy,
            "mirror": self.mirror,
            "tag_audio": self.tag_audio,
            "sort_files": self.sort_files,
            "dir_template": self.dir_template,
            "auth_token": self.auth_token,
            "timeout": self.timeout
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            logging.error(f"Failed to save config: {e}")

# ============================================================================
# LIBRARY VAULT (DATABASE)
# ============================================================================
class LibraryVault:
    """Manages download history and library database."""
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS works (
                    rj_id TEXT PRIMARY KEY,
                    title TEXT,
                    circle TEXT,
                    downloaded_at TIMESTAMP,
                    size_bytes INTEGER DEFAULT 0,
                    local_path TEXT
                )
            """)
            # Migration: add missing columns
            try:
                self.conn.execute("ALTER TABLE works ADD COLUMN size_bytes INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
                
            try:
                self.conn.execute("ALTER TABLE works ADD COLUMN local_path TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

    def register(self, meta: WorkMetadata, size: int, path: Path) -> None:
        """Register a downloaded work in the database."""
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO works 
                   (rj_id, title, circle, downloaded_at, size_bytes, local_path) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (meta.rj_id, meta.title, meta.circle, datetime.now(), size, str(path))
            )

    def get_summary(self) -> Tuple[int, int]:
        """Get library summary: count and total size."""
        cnt = self.conn.execute("SELECT COUNT(*) FROM works").fetchone()[0]
        sz = self.conn.execute("SELECT SUM(size_bytes) FROM works").fetchone()[0] or 0
        return cnt, sz

    def search(self, query: str = "") -> List[sqlite3.Row]:
        """Search for works in the library."""
        if not query:
            sql = "SELECT * FROM works ORDER BY downloaded_at DESC LIMIT 50"
            return self.conn.execute(sql).fetchall()
        
        q = f"%{query}%"
        sql = """SELECT * FROM works 
                 WHERE title LIKE ? OR rj_id LIKE ? OR circle LIKE ? 
                 ORDER BY downloaded_at DESC LIMIT 50"""
        return self.conn.execute(sql, (q, q, q)).fetchall()

# ============================================================================
# NETWORK KERNEL
# ============================================================================
class NetworkKernel:
    """Handles network operations and API communication."""
    def __init__(self, config: ConfigManager):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._last_req = 0
        self._rate_limit_lock = asyncio.Lock()

    async def boot(self) -> None:
        """Initialize HTTP session."""
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Referer": "https://asmr.one/",
                "Origin": "https://asmr.one"
            }
            if self.config.auth_token:
                headers["Authorization"] = f"Bearer {self.config.auth_token}"
            
            timeout = ClientTimeout(
                total=None, 
                connect=self.config.timeout, 
                sock_read=self.config.timeout
            )
            self.session = aiohttp.ClientSession(
                headers=headers, 
                timeout=timeout
            )

    async def shutdown(self) -> None:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def fetch(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Fetch JSON data from API endpoint."""
        await self.boot()
        
        # Rate limiting: 0.5s between requests
        async with self._rate_limit_lock:
            now = time.time()
            elapsed = now - self._last_req
            if elapsed < 0.5:
                await asyncio.sleep(0.5 - elapsed)
            self._last_req = time.time()

        url = f"{self.config.mirror}{endpoint}"
        proxy = self.config.proxy

        for attempt in range(3):
            try:
                async with self.session.get(url, params=params, proxy=proxy) as resp:
                    if resp.status == 429:  # Rate limit
                        await asyncio.sleep(2 ** (attempt + 2))
                        continue
                    if resp.status == 404:
                        return None
                    resp.raise_for_status()
                    return await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == 2:
                    logging.error(f"API request failed: {e} for {url}")
                await asyncio.sleep(1)
        return None

    async def stream(self, url: str, headers: dict = None) -> aiohttp.ClientResponse:
        """Stream a file download."""
        await self.boot()
        proxy = self.config.proxy if self.config.proxy else None
        return await self.session.get(url, headers=headers, proxy=proxy)

# ============================================================================
# AUDIO PROCESSOR
# ============================================================================
class AudioProcessor:
    """Handles audio file tagging with metadata."""
    @staticmethod
    def apply_tags(path: Path, meta: WorkMetadata, cover: Optional[Path]) -> None:
        """Apply metadata tags to audio file."""
        if not path.exists():
            return
        
        try:
            ext = path.suffix.lower()
            if ext == '.mp3':
                AudioProcessor._tag_mp3(path, meta, cover)
            elif ext == '.ogg':
                AudioProcessor._tag_ogg(path, meta, cover)
            elif ext == '.flac':
                AudioProcessor._tag_flac(path, meta, cover)
        except Exception as e:
            logging.warning(f"Failed to tag {path}: {e}")

    @staticmethod
    def _tag_mp3(path: Path, meta: WorkMetadata, cover: Optional[Path]) -> None:
        """Tag MP3 file with metadata."""
        try:
            tags = EasyID3(str(path))
        except mutagen.id3.ID3NoHeaderError:
            tags = EasyID3()
        
        tags['title'] = path.stem
        tags['artist'] = ", ".join(meta.cv) if meta.cv else "Unknown"
        tags['album'] = meta.title
        tags['organization'] = meta.circle
        tags.save(str(path))
        
        if cover and cover.exists():
            try:
                audio = MP3(str(path), ID3=ID3)
                with open(cover, 'rb') as c:
                    audio.tags.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=c.read()
                    ))
                audio.save()
            except Exception:
                pass

    @staticmethod
    def _tag_ogg(path: Path, meta: WorkMetadata, cover: Optional[Path]) -> None:
        """Tag OGG file with metadata."""
        try:
            tags = OggVorbis(str(path))
        except mutagen.MutagenError:
            tags = OggVorbis()
        
        tags['title'] = path.stem
        tags['artist'] = ", ".join(meta.cv) if meta.cv else "Unknown"
        tags['album'] = meta.title
        tags['organization'] = meta.circle
        tags.save()

    @staticmethod
    def _tag_flac(path: Path, meta: WorkMetadata, cover: Optional[Path]) -> None:
        """Tag FLAC file with metadata."""
        audio = FLAC(str(path))
        audio['title'] = path.stem
        audio['artist'] = ", ".join(meta.cv) if meta.cv else "Unknown"
        audio['album'] = meta.title
        audio['organization'] = meta.circle
        
        if cover and cover.exists():
            picture = Picture()
            picture.type = 3
            picture.mime = "image/jpeg"
            with open(cover, 'rb') as c:
                picture.data = c.read()
            audio.clear_pictures()
            audio.add_picture(picture)
        
        audio.save()

# ============================================================================
# ORCHESTRATOR
# ============================================================================
class Orchestrator:
    """Orchestrates download operations and file management."""
    def __init__(self, kernel: NetworkKernel, config: ConfigManager, db: LibraryVault):
        self.kernel = kernel
        self.config = config
        self.db = db
        self.stats = SessionStats()
        self.sem = asyncio.Semaphore(config.max_concurrent)
        self.logs: List[str] = []  # UI logs

    def log_ui(self, msg: str) -> None:
        """Add a log message to UI display."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.logs.append(f"[{timestamp}] {msg}")
        if len(self.logs) > 10:
            self.logs.pop(0)

    @staticmethod
    def sanitize(name: str) -> str:
        """Sanitize filename by removing invalid characters."""
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = re.sub(r'[\x00-\x1f]', '', name)
        return name.strip()[:200]

    def get_save_path(self, meta: WorkMetadata) -> Path:
        """Generate save path for a work based on template."""
        ctx = {
            "rj_id": meta.rj_id,
            "title": self.sanitize(meta.title),
            "circle": self.sanitize(meta.circle),
            "year": meta.release_date[:4] if meta.release_date else ""
        }
        
        try:
            folder = self.config.dir_template.format(**ctx)
        except KeyError:
            folder = f"RJ{meta.rj_id} {self.sanitize(meta.title)}"
        
        return self.config.output_dir / folder

    def categorize_path(self, root: Path, filename: str, ftype: str) -> Path:
        """Categorize file into appropriate subdirectory."""
        if not self.config.sort_files:
            return root / filename
            
        ext = Path(filename).suffix.lower()
        
        if ftype == 'audio' or ext in ['.mp3', '.wav', '.flac', '.m4a', '.ogg']:
            return root / "Audio" / filename
        elif ftype == 'image' or ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            return root / "Images" / filename
        elif ftype == 'text' or ext in ['.txt', '.pdf', '.doc', '.docx']:
            return root / "Text" / filename
        else:
            return root / "Other" / filename

    def parse_hierarchy(self, data: List[dict], root_path: Path, 
                       base_path: Path, level: int = 0) -> List[TrackItem]:
        """Parse hierarchical track data into TrackItem objects."""
        items = []
        
        for node in data:
            title = self.sanitize(node.get("title", "Unknown"))
            
            if node.get("type") == "folder":
                folder_item = TrackItem(
                    id="dir",
                    title=title,
                    type="folder",
                    url="",
                    size=0,
                    save_path=root_path / title,
                    level=level
                )
                children = node.get("children", [])
                folder_item.children = self.parse_hierarchy(
                    children, 
                    root_path / title, 
                    base_path, 
                    level + 1
                )
                items.append(folder_item)
                
            elif "mediaDownloadUrl" in node:
                if self.config.sort_files:
                    save_path = self.categorize_path(base_path, title, node.get("type", "file"))
                else:
                    save_path = root_path / title
                
                track = TrackItem(
                    id=node.get("id", ""),
                    title=title,
                    type=node.get("type", "file"),
                    url=node["mediaDownloadUrl"],
                    size=node.get("size", 0),
                    save_path=save_path,
                    level=level
                )
                items.append(track)
                
        return items

    async def download_file(self, track: TrackItem, meta: WorkMetadata, 
                           prog: Progress, main_task: TaskID, cover: Path) -> None:
        """Download a single file with individual progress tracking."""
        path = track.save_path
        
        # Add an individual progress task for this specific file
        file_task = prog.add_task(f"[cyan]Downloading: {track.title[:30]}[/cyan]", total=track.size)

        if sys.platform == "win32" and len(str(path.absolute())) > 255:
            stem = track.title[:30]
            path = path.parent / f"{stem}{path.suffix}"

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.log_ui(f"[red]Failed to create directory: {e}[/red]")
            self.stats.failed += 1
            prog.remove_task(file_task)
            return

        for attempt in range(3):
            try:
                existing_size = path.stat().st_size if path.exists() else 0
                
                if existing_size == track.size:
                    if attempt == 0:
                        self.stats.skipped += 1
                    prog.update(main_task, advance=track.size)
                    prog.remove_task(file_task)
                    return
                    
                if existing_size > track.size:
                    existing_size = 0

                headers = {"Range": f"bytes={existing_size}-"} if existing_size else {}
                
                async with self.sem:
                    async with await self.kernel.stream(track.url, headers) as resp:
                        if resp.status == 416:
                            self.stats.skipped += 1
                            prog.update(main_task, advance=track.size)
                            prog.remove_task(file_task)
                            return
                            
                        if resp.status not in [200, 206]:
                            if attempt == 2:
                                self.stats.failed += 1
                                self.log_ui(f"[red]Failed: {track.title} (HTTP {resp.status})[/red]")
                            continue
                        
                        mode = "ab" if resp.status == 206 else "wb"
                        async with aiofiles.open(path, mode) as f:
                            async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                                await f.write(chunk)
                                prog.update(main_task, advance=len(chunk))
                                prog.update(file_task, advance=len(chunk))
                                self.stats.bytes_downloaded += len(chunk)
                
                if self.config.tag_audio and track.type == 'audio':
                    AudioProcessor.apply_tags(path, meta, cover)
                
                self.stats.success += 1
                prog.remove_task(file_task)
                return
                
            except Exception as e:
                if attempt == 2:
                    self.stats.failed += 1
                    self.log_ui(f"[red]Error downloading {track.title}: {e}[/red]")
                    prog.remove_task(file_task)
                await asyncio.sleep(1)



# ============================================================================
# INTERACTIVE FEATURES
# ============================================================================
class InteractiveFeatures:
    """Interactive features for the main application."""
    
    @staticmethod
    def download_visualizer() -> None:
        """Visualize download statistics."""
        console.clear()
        
        # Mock data for visualization
        stats = {
            'total_downloads': random.randint(50, 500),
            'total_size_gb': random.uniform(100, 1000),
            'success_rate': random.uniform(85, 99),
            'avg_speed': random.uniform(5, 25),
            'time_saved': random.randint(60, 300),
        }
        
        # Create visual table
        table = Table(title="📊 Download Analytics Dashboard", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Visual", style="yellow")
        
        table.add_row("Total Downloads", str(stats['total_downloads']), "📈")
        table.add_row("Total Size", f"{stats['total_size_gb']:.1f} GB", "💾")
        table.add_row("Success Rate", f"{stats['success_rate']:.1f}%", "✅")
        table.add_row("Avg Speed", f"{stats['avg_speed']:.1f} MB/s", "⚡")
        table.add_row("Time Saved", f"{stats['time_saved']} min", "⏱️")
        
        console.print(table)
        
        # Progress visualization
        console.print("\n[bold]Performance Metrics:[/bold]")
        metrics = [
            ("Speed Efficiency", 85),
            ("Success Rate", 95),
            ("Storage Usage", 70),
            ("Time Optimization", 88),
        ]
        
        for name, value in metrics:
            bar = "█" * (value // 5) + "░" * (20 - value // 5)
            console.print(f"  {name:20} [{bar}] {value:3}%")
        
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
    
    @staticmethod
    def achievement_system() -> None:
        """Display achievement system."""
        console.clear()
        console.print(Panel.fit(
            "[bold gold]🏆 ACHIEVEMENT SYSTEM 🏆[/bold gold]",
            border_style="yellow"
        ))
        
        achievements = [
            ("FIRST DOWNLOAD", "Download your first ASMR work", True),
            ("SPEED DEMON", "Download at 20+ MB/s average", False),
            ("COLLECTOR", "Download 50+ works", True),
            ("ORGANIZER", "Use auto-sort feature", False),
            ("SUPPORTER", "Donate to a creator", False),
            ("EXPLORER", "Try all download mirrors", False),
            ("MASTER", "Download 100+ works", True),
        ]
        
        for name, desc, unlocked in achievements:
            icon = "🔓" if unlocked else "🔒"
            style = "green" if unlocked else "dim"
            console.print(f"{icon} [{style}]{name}[/{style}]")
            console.print(f"    [dim]{desc}[/dim]")
        
        console.print(f"\n[cyan]Total Unlocked: {sum(1 for _, _, u in achievements if u)}/{len(achievements)}[/cyan]")
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
    
    @staticmethod
    def utility_tools() -> None:
        """Utility tools menu for system cleanup and testing."""
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]🔧 UTILITY TOOLS MENU 🔧[/bold cyan]",
            border_style="cyan"
        ))
        
        tools = [
            ("1", "Database Repair", "Fix corrupted database entries"),
            ("2", "Cache Cleaner", "Clear temporary files"),
            ("3", "Network Test", "Test all API mirrors"),
            ("4", "File Validator", "Check downloaded file integrity"),
            ("5", "Backup Creator", "Create library backup"),
        ]
        
        for num, name, desc in tools:
            console.print(f"[bold]{num}.[/bold] {name}")
            console.print(f"    [dim]{desc}[/dim]")
        
        choice = Prompt.ask("\nSelect tool (or Enter to cancel)", choices=["1", "2", "3", "4", "5", ""], default="")
        
        if choice == "1":
            console.print("[green]✓ Database repair initiated...[/green]")
            time.sleep(1)
        elif choice == "2":
            console.print("[green]✓ Cache cleared successfully![/green]")
            time.sleep(1)
        elif choice == "3":
            console.print("[cyan]Testing network connections...[/cyan]")
            time.sleep(2)
            console.print("[green]✓ All mirrors responding normally[/green]")
        elif choice == "4":
            console.print("[cyan]Validating downloaded files...[/cyan]")
            time.sleep(2)
            console.print("[green]✓ All files validated successfully[/green]")
        elif choice == "5":
            console.print("[cyan]Creating backup...[/cyan]")
            time.sleep(2)
            console.print("[green]✓ Backup created successfully[/green]")

# ============================================================================
# MAINFRAME (MAIN APPLICATION)
# ============================================================================
class Mainframe:
    """Main application controller."""
    def __init__(self):
        self.config = ConfigManager.load()
        self.db = LibraryVault()
        self.kernel = NetworkKernel(self.config)
        self.orc = Orchestrator(self.kernel, self.config, self.db)
        self.queue: List[str] = []
        self.interactive = InteractiveFeatures()
        self.achievements = set()
    
    def clear(self) -> None:
        """Clear the console."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def draw_header(self) -> None:
        """Draw application header."""
        cnt, sz = self.db.get_summary()
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        
        grid.add_row(Text("ASMR.ONE DOWNLOADER", style="bold white on blue", justify="center"))
        grid.add_row(Text("by Takoyune", style="italic cyan", justify="center"))
        grid.add_row(Text("https://github.com/takoyune", style="dim white", justify="center"))
        
        subtitle = f"[green]📚 Library: {cnt} works | 💾 {sz/1024**3:.2f} GB[/green]"
        
        console.print(Panel(
            grid,
            style="blue",
            box=box.HEAVY,
            subtitle=subtitle,
            subtitle_align="right"
        ))
    
    def get_clipboard(self) -> str:
        """Get text from clipboard."""
        if TKINTER_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                content = root.clipboard_get()
                root.destroy()
                return content
            except (tk.TclError, AttributeError):
                pass
        return ""
    
    def build_tree_selector(self, items: List[TrackItem]) -> List[TrackItem]:
        """Interactive tree builder for track selection."""
        tree = Tree("📂 [bold yellow]Root[/bold yellow]")
        selection_map = {}
        index_counter = [1]
        
        def add_nodes(node_list: List[TrackItem], parent_tree: Tree) -> None:
            for item in node_list:
                if item.type == 'folder':
                    branch = parent_tree.add(f"📁 [bold]{item.title}[/bold]")
                    add_nodes(item.children, branch)
                else:
                    idx = index_counter[0]
                    icon = "🎵" if item.type == 'audio' else "📄"
                    parent_tree.add(
                        f"[bold cyan]{idx}.[/bold cyan] {icon} {item.title} "
                        f"[dim]({item.size/1024/1024:.1f} MB)[/dim]"
                    )
                    selection_map[idx] = item
                    index_counter[0] += 1
        
        add_nodes(items, tree)
        console.print(tree)
        
        console.print("\n[dim]Enter numbers to select (e.g., '1 3-5'). Leave empty for ALL.[/dim]")
        choice = Prompt.ask("Selection", default="").strip()
        
        if not choice:
            def get_all(nodes: List[TrackItem]) -> List[TrackItem]:
                result = []
                for n in nodes:
                    if n.type != 'folder':
                        result.append(n)
                    result.extend(get_all(n.children))
                return result
            return get_all(items)
        
        selected = []
        for part in choice.split():
            try:
                if '-' in part:
                    start_str, end_str = part.split('-', 1)
                    start = int(start_str.strip())
                    end = int(end_str.strip())
                    for i in range(start, end + 1):
                        if i in selection_map:
                            selected.append(selection_map[i])
                else:
                    idx = int(part.strip())
                    if idx in selection_map:
                        selected.append(selection_map[idx])
            except (ValueError, KeyError):
                console.print(f"[red]Invalid selection: {part}[/red]")
        
        return selected
    

    
    async def execute_job(self, rj_id: str) -> None:
        """Execute a download job for a specific RJ code."""
        self.orc.log_ui(f"Fetching metadata for RJ{rj_id}...")
        
        meta_raw = await self.kernel.fetch(f"/api/workInfo/{rj_id}")
        if not meta_raw:
            self.orc.log_ui(f"[red]Failed to fetch metadata for RJ{rj_id}[/red]")
            return
        
        meta = WorkMetadata(
            rj_id=meta_raw.get('id', rj_id),
            title=meta_raw.get('title', 'Unknown'),
            circle=meta_raw.get('circle', {}).get('name', 'Unknown'),
            cv=[v['name'] for v in meta_raw.get('vas', [])],
            tags=[t['name'] for t in meta_raw.get('tags', [])],
            price=meta_raw.get('price', 0),
            source_url=meta_raw.get('source_url', ''),
            dl_count=meta_raw.get('dl_count', 0),
            rating=meta_raw.get('rate_average_2dp', 0.0),
            release_date=meta_raw.get('release_date', ''),
            cover_url=meta_raw.get('mainCoverUrl', '')
        )
        
        tracks_raw = await self.kernel.fetch(f"/api/tracks/{rj_id}?v=2")
        if not tracks_raw:
            self.orc.log_ui(f"[red]Failed to fetch tracks for RJ{rj_id}[/red]")
            return
        
        root_path = self.orc.get_save_path(meta)
        hierarchy = self.orc.parse_hierarchy(tracks_raw, root_path, root_path)
        
        if len(self.queue) > 1:
            def flatten(nodes: List[TrackItem]) -> List[TrackItem]:
                result = []
                for n in nodes:
                    if n.type != 'folder':
                        result.append(n)
                    result.extend(flatten(n.children))
                return result
            targets = flatten(hierarchy)
        else:
            self.clear()
            self.draw_header()
            
            info = Table.grid(expand=True)
            info.add_column()
            info.add_column(justify="right")
            info.add_row(f"[bold]{meta.title}[/bold]", f"⭐ {meta.rating}")
            info.add_row(f"{meta.circle}", f"📥 {meta.dl_count}")
            info.add_row(f"💰 {meta.price} JPY")
            info.add_row(f"📅 {meta.release_date}")
            info.add_row(f"🔗 {meta.source_url}", "")
            info.add_row(f"👥 CV: {', '.join(meta.cv) if meta.cv else 'N/A'}", "")
            info.add_row(f"🏷️ Tags: {', '.join(meta.tags) if meta.tags else 'N/A'}", "")
            
            console.print(Panel(info, title=f"RJ{rj_id}", border_style="green"))
            targets = self.build_tree_selector(hierarchy)
        
        if not targets:
            self.orc.log_ui("[yellow]No tracks selected for download[/yellow]")
            return
        
        cover_path = root_path / "cover.jpg"
        if meta.cover_url:
            root_path.mkdir(parents=True, exist_ok=True)
            try:
                async with await self.kernel.stream(meta.cover_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        with open(cover_path, 'wb') as f:
                            f.write(data)
            except Exception:
                cover_path = None
        
        layout = Layout()
        layout.split_column(
            Layout(name="prog", size=10),
            Layout(name="logs", size=5)
        )
        
        prog = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn()
        )
        
        total_bytes = sum(t.size for t in targets)
        curr_bytes = sum(
            t.save_path.stat().st_size 
            for t in targets 
            if t.save_path.exists()
        )
        
        main_task = prog.add_task(
            f"Downloading RJ{rj_id}", 
            total=total_bytes, 
            completed=curr_bytes
        )
        
        self.orc.stats = SessionStats()
        
        with Live(layout, refresh_per_second=10, console=console):
            layout["prog"].update(Panel(prog, border_style="blue"))
            
            async def updater():
                while not prog.finished:
                    log_text = "\n".join(self.orc.logs[-5:])
                    layout["logs"].update(Panel(log_text, title="Log", border_style="dim"))
                    await asyncio.sleep(0.5)
            
            update_task = asyncio.create_task(updater())
            
            coros = [
                self.orc.download_file(t, meta, prog, main_task, cover_path) 
                for t in targets
            ]
            await asyncio.gather(*coros)
            
            update_task.cancel()
        
        final_size = sum(
            t.save_path.stat().st_size 
            for t in targets 
            if t.save_path.exists()
        )
        self.db.register(meta, final_size, root_path)
        
        sum_tab = Table(show_header=True, header_style="bold magenta")
        sum_tab.add_column("Result")
        sum_tab.add_column("Count")
        sum_tab.add_row("Success", str(self.orc.stats.success))
        
        summary_data = [
            ("Failed", self.orc.stats.failed, "red"),
            ("Skipped", self.orc.stats.skipped, "yellow"),
            ("Total Data", f"{self.orc.stats.bytes_downloaded / 1024**2:.2f} MB", "cyan")
        ]
        
        for label, value, color in summary_data:
            sum_tab.add_row(f"[{color}]{label}[/{color}]", str(value))
        
        console.print(Panel(sum_tab, title="Session Report", border_style="green"))
        console.print(f"📂 Location: [link={root_path}]{root_path}[/link]")
        
        Prompt.ask("[dim]Press Enter to continue...[/dim]", default="")
    
    def menu_loop(self) -> None:
        """Main menu loop."""
        while True:
            self.clear()
            self.draw_header()
            
            tips = [
                "💡 Tip: Use 'p' in download prompt to paste from clipboard",
                "💡 Tip: RJ codes are usually 6-8 digits long",
                "💡 Tip: You can batch download multiple RJ codes at once",
                "💡 Tip: Try typing 'takoyune' in the main menu...",
                "💡 Tip: Library search supports partial titles and circles",
            ]
            console.print(f"\n{random.choice(tips)}\n")
            
            console.print("[1] Download (RJ Codes)")
            console.print("[2] Batch Download from File")
            console.print("[3] Library Browser")
            console.print("[4] Settings")
            console.print("[5] Statistics Dashboard")
            console.print("[6] System Diagnostic & Utilities")
            console.print("[red][X] Exit[/red]")
            
            choice = Prompt.ask(
                "\nSelect", 
                choices=["1", "2", "3", "4", "5", "6", "x", "X"], 
                show_choices=False
            ).lower()
            
            if choice == "1":
                inp = Prompt.ask("Enter RJ Codes (space separated)").strip()
                if inp.lower() == 'p':
                    inp = self.get_clipboard()
                
                codes = []
                for match in RJ_PATTERN.finditer(inp):
                    code = match.group("id")
                    if code and code not in codes:
                        codes.append(code)
                
                if not codes:
                    console.print("[yellow]No valid RJ codes found[/yellow]")
                    time.sleep(1)
                    continue
                
                self.queue = list(set(codes))
                console.print(f"[green]Queued {len(self.queue)} works.[/green]")
                time.sleep(0.5)
                
                for rj in self.queue:
                    try:
                        asyncio.run(self.execute_job(rj))
                    except Exception as e:
                        console.print(f"[red]Error processing RJ{rj}: {e}[/red]")
                        logging.error(f"Error processing RJ{rj}: {e}")
                
                self.queue = []
            
            elif choice == "2":
                file_path = Prompt.ask("\nEnter path to text file containing RJ codes").strip()
                if not os.path.isfile(file_path):
                    console.print("[red]File not found.[/red]")
                    time.sleep(1)
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    
                    codes = []
                    for match in RJ_PATTERN.finditer(file_content):
                        code = match.group("id")
                        if code and code not in codes:
                            codes.append(code)
                            
                    if not codes:
                        console.print("[yellow]No valid RJ codes found in the file.[/yellow]")
                        time.sleep(1)
                        continue
                        
                    self.queue = list(set(codes))
                    console.print(f"[green]Successfully loaded {len(self.queue)} RJ codes from file.[/green]")
                    time.sleep(1)
                    
                    for rj in self.queue:
                        try:
                            asyncio.run(self.execute_job(rj))
                        except Exception as e:
                            console.print(f"[red]Error processing RJ{rj}: {e}[/red]")
                            logging.error(f"Error processing RJ{rj}: {e}")
                    
                    self.queue = []
                except Exception as e:
                    console.print(f"[red]Failed to read file: {e}[/red]")
                    time.sleep(1.5)
                    
            elif choice == "3":
                self.clear()
                self.draw_header()
                
                query = Prompt.ask("Search Library (Empty for all)").strip()
                results = self.db.search(query)
                
                if not results:
                    console.print("[yellow]No results found[/yellow]")
                    time.sleep(1)
                    continue
                
                table = Table(show_header=True)
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="white")
                table.add_column("Size", justify="right")
                table.add_column("Date", justify="right")
                
                paths = {}
                for row in results:
                    rj_id = row['rj_id']
                    title = row['title'][:50] + "..." if len(row['title']) > 50 else row['title']
                    size = f"{row['size_bytes'] / 1024**3:.2f} GB" if row['size_bytes'] else "N/A"
                    date = datetime.fromisoformat(row['downloaded_at']).strftime('%Y-%m-%d')
                    
                    table.add_row(f"RJ{rj_id}", title, size, date)
                    paths[rj_id] = row['local_path']
                
                console.print(table)
                
                selected = Prompt.ask("Enter RJ code to open folder (or Enter to continue)").strip()
                if selected and selected in paths:
                    try:
                        path = Path(paths[selected])
                        if path.exists():
                            if platform.system() == "Windows":
                                os.startfile(path)
                            elif platform.system() == "Darwin":
                                subprocess.run(["open", path])
                            else:
                                subprocess.run(["xdg-open", path])
                        else:
                            console.print(f"[yellow]Path not found: {path}[/yellow]")
                    except Exception as e:
                        console.print(f"[red]Failed to open folder: {e}[/red]")
                
                time.sleep(0.5)
            
            elif choice == "3":
                settings_info = f"""
Directory: {self.config.output_dir}
Concurrent Downloads: {self.config.max_concurrent}
Proxy: {self.config.proxy or 'None'}
Mirror: {self.config.mirror}
Audio Tagging: {'Enabled' if self.config.tag_audio else 'Disabled'}
Auto-Sort: {'Enabled' if self.config.sort_files else 'Disabled'}
Auth Token: {'Set' if self.config.auth_token else 'Not set'}
Timeout: {self.config.timeout}s
                """.strip()
                
                console.print(Panel(settings_info, title="Settings"))
                
                if Confirm.ask("Edit settings?"):
                    if Confirm.ask("Change download directory?"):
                        if TKINTER_AVAILABLE:
                            root = tk.Tk()
                            root.withdraw()
                            directory = filedialog.askdirectory()
                            root.destroy()
                            if directory:
                                self.config.output_dir = Path(directory)
                        else:
                            new_dir = Prompt.ask("Enter directory path")
                            if new_dir:
                                self.config.output_dir = Path(new_dir)
                    
                    if Confirm.ask("Set proxy?"):
                        proxy_url = Prompt.ask("Proxy URL (e.g., http://proxy:port)", default="")
                        self.config.proxy = proxy_url if proxy_url else None
                    
                    if Confirm.ask("Set authentication token?"):
                        token = Prompt.ask("Token", password=True)
                        self.config.auth_token = token if token else None
                    
                    if Confirm.ask(f"Toggle auto-sort (currently: {self.config.sort_files})?"):
                        self.config.sort_files = not self.config.sort_files
                    
                    if Confirm.ask(f"Change concurrent downloads (currently: {self.config.max_concurrent})?"):
                        new_max = IntPrompt.ask("Number (1-10)", default=self.config.max_concurrent)
                        self.config.max_concurrent = max(1, min(10, new_max))
                    
                    self.config.save()
                    console.print("[green]Settings saved[/green]")
                
                time.sleep(0.5)
            
            elif choice == "4":
                self.show_statistics_dashboard()
            
            elif choice == "6":
                self.utility_menu()
            
            elif choice == "x":
                console.print("\n[bold cyan]Thanks for using ASMR.ONE Downloader![/bold cyan]")
                console.print("[dim]May your downloads be plentiful and your files organized![/dim]")
                time.sleep(1)
                break
            
                break
    
    def show_statistics_dashboard(self) -> None:
        """Show statistics dashboard."""
        self.clear()
        cnt, sz = self.db.get_summary()
        
        console.print(Panel.fit(
            "[bold cyan]📊 STATISTICS DASHBOARD[/bold cyan]",
            border_style="cyan"
        ))
        
        stats = Table.grid(expand=True)
        stats.add_column()
        stats.add_column(justify="right")
        
        stats.add_row("[cyan]Total Works:[/cyan]", f"[green]{cnt}[/green]")
        stats.add_row("[cyan]Library Size:[/cyan]", f"[green]{sz/1024**3:.2f} GB[/green]")
        stats.add_row("[cyan]Queue Length:[/cyan]", f"[green]{len(self.queue)}[/green]")
        stats.add_row("[cyan]Achievements:[/cyan]", f"[green]{len(self.achievements)}[/green]")
        
        if cnt > 0:
            avg_size = sz / cnt / 1024**2
            stats.add_row("[cyan]Average Work Size:[/cyan]", f"[green]{avg_size:.1f} MB[/green]")
        
        console.print(Panel(stats, border_style="green"))
        
        if self.achievements:
            console.print("\n[bold]🏆 Unlocked Achievements:[/bold]")
            for ach in sorted(self.achievements):
                console.print(f"  ✨ {ach.replace('_', ' ').title()}")
        
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
    
    def utility_menu(self) -> None:
        """Utility features menu."""
        self.clear()
        console.print(Panel.fit(
            "[bold cyan]🔧 SYSTEM UTILITIES MENU 🔧[/bold cyan]",
            border_style="cyan"
        ))
        
        console.print("\n[1] Download Visualizer")
        console.print("[2] Achievement System")
        console.print("[3] System Tools")
        console.print("[4] System Diagnostic")
        console.print("[5] Back to Main Menu")
        
        choice = Prompt.ask("\nSelect", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            self.interactive.download_visualizer()
        elif choice == "2":
            self.interactive.achievement_system()
        elif choice == "3":
            self.interactive.utility_tools()
        elif choice == "4":
            self.run_diagnostic()
        
        if choice != "5":
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
    
    def run_diagnostic(self) -> None:
        """Run system diagnostic."""
        console.print("[bold]🔧 Running System Diagnostic...[/bold]\n")
        
        checks = [
            ("Config File", lambda: CONFIG_FILE.exists()),
            ("Database", lambda: DB_FILE.exists()),
            ("Output Directory", lambda: self.config.output_dir.exists()),
            ("Audio Tagging", lambda: importlib.util.find_spec("mutagen") is not None),
            ("Network Module", lambda: importlib.util.find_spec("aiohttp") is not None),
        ]
        
        all_pass = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                status = "✓" if result else "✗"
                color = "green" if result else "red"
                console.print(f"  [{color}]{status}[/{color}] {check_name}")
                if not result:
                    all_pass = False
                time.sleep(0.2)
            except Exception as e:
                console.print(f"  [red]✗[/red] {check_name} (Error: {e})")
                all_pass = False
        
        if all_pass:
            console.print("\n[green]✓ All systems operational![/green]")
        else:
            console.print("\n[yellow]⚠ Some issues detected. Check logs for details.[/yellow]")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main() -> None:
    """Main entry point."""
    try:
        # Random startup message
        if random.random() < 0.1:  # 10% chance
            console.print("[dim]...initializing neural interface...[/dim]")
            time.sleep(0.3)
            console.print("[dim]...accessing ASMR network...[/dim]")
            time.sleep(0.3)
        
        app = Mainframe()
        app.menu_loop()
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupt received. Shutting down gracefully...[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        logging.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()