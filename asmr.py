import asyncio
import re
import sys
import json
import argparse
import sqlite3
import signal
from datetime import datetime
from pathlib import Path
from typing import Literal, List, Optional
from dataclasses import dataclass

import aiofiles
import aiohttp
from aiohttp import ClientConnectorError, ClientResponseError
import tkinter as tk
from tkinter import filedialog

# --- Dependencies Check ---
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import (
        Progress, SpinnerColumn, BarColumn, TextColumn, 
        DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
    )
    from rich.prompt import Confirm, Prompt, IntPrompt
    from rich.live import Live
    import mutagen
    from mutagen.flac import FLAC, Picture
    from mutagen.id3 import ID3, APIC
    from mutagen.mp3 import MP3
    from mutagen.easyid3 import EasyID3
except ImportError:
    print("❌ Error: Missing dependencies. Please run:")
    print("pip install rich mutagen aiohttp aiofiles")
    sys.exit(1)

try:
    import keyboard
    HOTKEYS = True
except ImportError:
    HOTKEYS = False

# --- Config & Constants ---
HOSTNAME = "https://api.asmr-200.com"
RJ_RE = re.compile(r"(?:RJ)?(?P<id>[\d]+)")
CHUNK_SIZE = 1024 * 1024  # 1MB Chunks
CONFIG_FILE = Path("config.json")
DB_FILE = Path("history.db")

console = Console()

# --- Database ---
class HistoryDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS works (
                    rj_id TEXT PRIMARY KEY,
                    title TEXT,
                    downloaded_at TIMESTAMP
                )
            """)

    def add_work(self, rj_id: str, title: str):
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO works (rj_id, title, downloaded_at) VALUES (?, ?, ?)",
                (rj_id, title, datetime.now())
            )

    def exists(self, rj_id: str) -> bool:
        cursor = self.conn.execute("SELECT 1 FROM works WHERE rj_id = ?", (rj_id,))
        return cursor.fetchone() is not None

# --- Tagging ---
class AudioTagger:
    @staticmethod
    def tag_file(path: Path, meta: dict, cover_path: Optional[Path]):
        try:
            if not path.exists(): return
            ext = path.suffix.lower()
            title = path.stem
            artist = meta.get('name', 'ASMR Artist')
            album = meta.get('title', 'Unknown Album')
            
            if ext == '.mp3':
                try: tags = EasyID3(path)
                except: tags = EasyID3(); tags.save(path)
                tags['title'] = title; tags['artist'] = artist; tags['album'] = album
                tags.save()
                
                if cover_path and cover_path.exists():
                    audio = MP3(path, ID3=ID3)
                    try: audio.add_tags()
                    except: pass
                    with open(cover_path, 'rb') as img:
                        audio.tags.add(APIC(3, 'image/jpeg', 3, 'Cover', img.read()))
                    audio.save()

            elif ext == '.flac':
                audio = FLAC(path)
                audio['title'] = title; audio['artist'] = artist; audio['album'] = album
                if cover_path and cover_path.exists():
                    img = Picture(); img.type = 3; img.mime = "image/jpeg"
                    with open(cover_path, "rb") as f: img.data = f.read()
                    audio.add_picture(img)
                audio.save()
        except: pass

@dataclass
class WorkTrack:
    filename: str
    url: str
    type: str
    save_path: Path
    size: int = 0

# --- Main Logic ---
class ASMRDownloader:
    def __init__(self):
        self.config = self.load_config()
        self.db = HistoryDB()
        self.session = None
        self.semaphore = asyncio.Semaphore(self.config.get("max_concurrent", 3))
        self.paused = False

    def load_config(self):
        default = {"output_dir": str(Path.cwd() / "Downloads"), "max_concurrent": 3, "proxy": "", "tag_audio": True}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f: return {**default, **json.load(f)}
            except: pass
        return default

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    async def __aenter__(self):
        # Set longer timeout for unstable connections
        timeout = aiohttp.ClientTimeout(total=60, connect=30)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://asmr.one/",
            "Origin": "https://asmr.one"
        }
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        if HOTKEYS: asyncio.create_task(self.input_monitor())
        return self

    async def __aexit__(self, *args):
        if self.session: await self.session.close()

    async def input_monitor(self):
        while True:
            try:
                if keyboard.is_pressed('p'): self.paused = True
                elif keyboard.is_pressed('r'): self.paused = False
                await asyncio.sleep(0.1)
            except: break

    def sanitize(self, name):
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()[:200]

    async def fetch(self, url):
        proxy = self.config.get("proxy") or None
        # Clean up empty proxy string if it exists
        if proxy and not proxy.strip(): proxy = None

        try:
            async with self.session.get(url, proxy=proxy) as resp:
                if resp.status == 404: return None
                resp.raise_for_status()
                return await resp.json()
        except ClientConnectorError as e:
            console.print(f"\n[bold red]❌ Connection Error:[/bold red] Could not connect to {HOSTNAME}")
            console.print(f"[yellow]⚠️  Reason: {e}[/yellow]")
            console.print("[yellow]💡 Hint: Your ISP might be blocking this site. Try using a VPN or Proxy.[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]Error fetching data: {e}[/red]")
            return None

    def parse_tracks(self, data, root: Path) -> List[WorkTrack]:
        tracks = []
        for item in data:
            path = root / self.sanitize(item["title"])
            if item["type"] == "folder":
                tracks.extend(self.parse_tracks(item["children"], path))
            else:
                tracks.append(WorkTrack(item["title"], item["mediaDownloadUrl"], item["type"], path, item.get("size", 0)))
        return tracks

    # --- SELECTION UI ---
    def select_files_ui(self, tracks: List[WorkTrack]) -> List[WorkTrack]:
        console.print(f"\n📂 Detected [bold]{len(tracks)}[/bold] files.")
        console.print("[1] Download ALL")
        console.print("[2] Download AUDIO Only (.mp3, .wav, .flac)")
        console.print("[3] Manual Selection")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="1")
        
        if choice == "1":
            return tracks
        elif choice == "2":
            return [t for t in tracks if t.type == "audio"]
        elif choice == "3":
            table = Table(show_header=True, header_style="bold blue")
            table.add_column("#", style="dim", width=4)
            table.add_column("Filename")
            table.add_column("Size", justify="right")
            table.add_column("Type", style="magenta")

            for i, t in enumerate(tracks):
                size_mb = f"{t.size / 1024 / 1024:.2f} MB" if t.size else "??"
                table.add_row(str(i+1), t.filename, size_mb, t.type)
            
            console.print(table)
            console.print("[yellow]Enter numbers (e.g., 1 3 5) or ranges (e.g., 1-5)[/yellow]")
            
            selected_indices = set()
            inp = Prompt.ask("File numbers")
            
            for part in inp.split():
                try:
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        selected_indices.update(range(start, end + 1))
                    else:
                        selected_indices.add(int(part))
                except: pass
            
            return [tracks[i-1] for i in selected_indices if 0 < i <= len(tracks)]
        
        return []

    async def download_worker(self, track: WorkTrack, progress, task_id, cover: Path, meta: dict):
        while self.paused: await asyncio.sleep(0.5)
        
        path = track.save_path
        path.parent.mkdir(parents=True, exist_ok=True)
        
        existing = path.stat().st_size if path.exists() else 0
        if track.size and existing == track.size:
            progress.update(task_id, advance=track.size)
            return

        headers = {"Range": f"bytes={existing}-"} if existing else {}
        proxy = self.config.get("proxy") or None
        if proxy and not proxy.strip(): proxy = None
        
        try:
            async with self.semaphore:
                async with self.session.get(track.url, headers=headers, proxy=proxy, timeout=60) as resp:
                    if resp.status not in [200, 206]: return
                    if resp.status == 200: existing = 0
                    
                    mode = "ab" if existing else "wb"
                    async with aiofiles.open(path, mode) as f:
                        async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                            while self.paused: await asyncio.sleep(0.5)
                            await f.write(chunk)
                            progress.update(task_id, advance=len(chunk))
            
            if self.config["tag_audio"] and track.type == "audio":
                AudioTagger.tag_file(path, meta, cover)
        except Exception: pass

    async def process_work(self, rj_id: str):
        with console.status(f"[cyan]Fetching data for RJ{rj_id}...[/cyan]"):
            meta = await self.fetch(f"{HOSTNAME}/api/workInfo/{rj_id}")
            if not meta:
                # Error message already handled in fetch
                return

            tracks_data = await self.fetch(f"{HOSTNAME}/api/tracks/{rj_id}?v=2")
            if not tracks_data:
                console.print("[red]Could not fetch track list.[/red]")
                return

        title = self.sanitize(meta.get('title', 'Unknown'))
        out_dir = Path(self.config["output_dir"]) / f"RJ{rj_id} {title}"
        
        console.print(f"[green]Found:[/green] {title}")

        all_tracks = self.parse_tracks(tracks_data, out_dir)
        selected_tracks = self.select_files_ui(all_tracks)
        
        if not selected_tracks:
            console.print("[red]No files selected. Aborted.[/red]")
            return

        # Cover Download
        cover_path = out_dir / "cover.jpg"
        if meta.get("mainCoverUrl") and not cover_path.exists():
            out_dir.mkdir(parents=True, exist_ok=True)
            try:
                proxy = self.config.get("proxy") or None
                if proxy and not proxy.strip(): proxy = None
                async with self.session.get(meta["mainCoverUrl"], proxy=proxy) as r:
                    if r.status == 200: 
                        d = await r.read()
                        with open(cover_path, "wb") as f: f.write(d)
            except: pass

        # Download Execution
        total_size = sum(t.size for t in selected_tracks if t.size)
        console.print(f"\n[green]🚀 Starting download...[/green]")
        
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            console=console,
            transient=False 
        )

        with progress:
            main_task = progress.add_task("Total Progress", total=total_size)
            tasks = []
            for track in selected_tracks:
                tasks.append(self.download_worker(track, progress, main_task, cover_path, meta))
            await asyncio.gather(*tasks)

        self.db.add_work(rj_id, title)
        console.print(f"[bold green]✅ Done! Saved to:[/bold green] {out_dir}\n")

async def main():
    downloader = ASMRDownloader()

    async with downloader:
        while True:
            # UI HEADER
            console.print("[bold cyan]┌──────────────────────────────┐[/bold cyan]")
            console.print("[bold cyan]│ ASMR.ONE Downloader v4.2     │[/bold cyan]")
            console.print("[bold cyan]└──────────────────────────────┘[/bold cyan]")
            
            console.print("\n[1] Download via RJ Code")
            console.print("[2] Search & Download")
            console.print("[3] Settings (Set Proxy)")
            console.print("[q] Quit")
            
            choice = Prompt.ask("\nSelect Option", choices=["1", "2", "3", "q"], show_choices=False)

            if choice == "1":
                codes = Prompt.ask("Enter RJ Codes (e.g. RJ123456)").split()
                for code in codes:
                    if match := RJ_RE.search(code):
                        await downloader.process_work(match.group("id"))
                    else:
                        console.print(f"[red]Invalid code: {code}[/red]")
                Prompt.ask("Press Enter to return to menu...")

            elif choice == "2":
                q = Prompt.ask("Search Query")
                res = await downloader.fetch(f"{HOSTNAME}/api/search?query={q}&page=1&size=5")
                if res and res.get('works'):
                    table = Table(show_header=True)
                    table.add_column("RJ Code", style="cyan")
                    table.add_column("Title")
                    for w in res['works']:
                        table.add_row(f"RJ{w['id']}", w['title'][:50])
                    console.print(table)
                    
                    code = Prompt.ask("Enter RJ Code from list to download (or 'back')")
                    if match := RJ_RE.search(code):
                        await downloader.process_work(match.group("id"))
                else:
                    if res is None:
                        # Error message already printed by fetch
                        pass
                    else:
                        console.print("[red]No results found.[/red]")
                Prompt.ask("Press Enter to return to menu...")

            elif choice == "3":
                console.print(f"Current Output: [yellow]{downloader.config['output_dir']}[/yellow]")
                console.print(f"Current Proxy:  [yellow]{downloader.config['proxy'] or 'None'}[/yellow]")
                
                print("\n[1] Change Folder")
                print("[2] Set Proxy (Fix Connection Issues)")
                print("[3] Back")
                
                sub = Prompt.ask("Choice", choices=["1", "2", "3"], default="3")
                
                if sub == "1":
                    root = tk.Tk(); root.withdraw()
                    d = filedialog.askdirectory()
                    if d:
                        downloader.config['output_dir'] = d
                        downloader.save_config()
                        console.print("[green]Saved![/green]")
                    root.destroy()
                elif sub == "2":
                    console.print("Enter Proxy URL (e.g., http://127.0.0.1:7890)")
                    console.print("Leave empty to disable.")
                    p = Prompt.ask("Proxy URL")
                    downloader.config['proxy'] = p
                    downloader.save_config()
                    console.print("[green]Proxy Saved![/green]")

            elif choice == "q":
                console.print("Bye!")
                break
            
            console.print("─" * 30, style="dim")

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
