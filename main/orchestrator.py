import os
import re
import sys
import time
import urllib.parse
import asyncio
import logging
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import List, Any

from rich.progress import Progress, TaskID
from main.progress import ProgressReporter

from main.constants import CHUNK_SIZE
from main.models import WorkMetadata, TrackItem, SessionStats
from main.config import ConfigManager
from main.db import LibraryVault
from main.network import NetworkKernel
from main.audio import AudioProcessor


class Orchestrator:
    """Orchestrates download operations and file management."""
    def __init__(self, kernel: NetworkKernel, config: ConfigManager, db: LibraryVault):
        self.kernel = kernel
        self.config = config
        self.db = db
        self.stats = SessionStats()
        self.sem = asyncio.Semaphore(config.max_concurrent)
        self.logs: List[str] = []  # UI logs
        self._tokens = 0.0
        self._last_token_update = time.time()
        self._token_lock = asyncio.Lock()

    async def _consume_bandwidth(self, chunk_size: int) -> None:
        """Global token-bucket bandwidth throttler."""
        limit_bytes_per_sec = self.config.bandwidth_limit_mbps * 1024 * 1024
        if limit_bytes_per_sec <= 0:
            return

        # Compute sleep time under the lock, but sleep OUTSIDE it
        # so other concurrent downloads are not blocked during the wait.
        async with self._token_lock:
            now = time.time()
            elapsed = now - self._last_token_update
            self._tokens = min(
                self._tokens + elapsed * limit_bytes_per_sec,
                limit_bytes_per_sec
            )
            self._last_token_update = now
            sleep_time = max(0.0, (chunk_size - self._tokens) / limit_bytes_per_sec)
            self._tokens = max(0.0, self._tokens - chunk_size)

        if sleep_time > 0:
            await asyncio.sleep(sleep_time)

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
                
                import yarl
                raw_url = node["mediaDownloadUrl"]
                
                track = TrackItem(
                    id=node.get("id", ""),
                    title=title,
                    type=node.get("type", "file"),
                    url=yarl.URL(raw_url, encoded=True),
                    size=node.get("size", 0),
                    save_path=save_path,
                    level=level
                )
                items.append(track)
                
        # Deduplicate identical files (by stem) using format_priority
        if self.config.format_priority:
            deduped = []
            file_groups = {}
            for item in items:
                if item.type == "folder":
                    deduped.append(item)
                else:
                    stem = Path(item.title).stem
                    file_groups.setdefault(stem, []).append(item)
            
            for stem, group in file_groups.items():
                if len(group) == 1:
                    deduped.append(group[0])
                else:
                    # Sort group by priority. If extension not in priority list, treat as lowest priority
                    def get_priority(it: TrackItem) -> int:
                        ext = Path(it.title).suffix.lstrip('.').lower()
                        try:
                            return self.config.format_priority.index(ext)
                        except ValueError:
                            return 999
                    group.sort(key=get_priority)
                    deduped.append(group[0])
                    
            items = deduped

        return items

    async def download_file(self, track: TrackItem, meta: WorkMetadata, 
                           prog: ProgressReporter, main_task: Any, cover: Path) -> None:
        """Download a single file with individual progress tracking."""
        path = track.save_path
        logging.debug(f"[RJ{meta.rj_id}] Starting download loop for {track.title} -> {path}")
        
        # Add an individual progress task for this specific file
        file_task = prog.add_task(f"[cyan]Downloading: {track.title[:30]}[/cyan]", total=track.size)

        # Use prefix \\?\ on Windows for paths > 250 chars
        if sys.platform == "win32" and len(str(path.absolute())) > 250:
            path = Path("\\\\?\\" + str(path.resolve()))
            
        tmp_path = Path(str(path) + ".tmp")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.log_ui(f"[red]Failed to create directory: {e}[/red]")
            logging.exception(f"Failed to create directory {path.parent} for {track.title}")
            self.stats.failed += 1
            self.stats.failures.append((track.title, f"Directory error: {e}"))
            prog.remove_task(file_task)
            return

        for attempt in range(20):
            try:
                db_state = self.db.file_state_get(meta.rj_id, str(path))
                if db_state and db_state['status'] == 'completed' and path.exists():
                    if attempt == 0:
                        self.stats.skipped += 1
                        logging.debug(f"[RJ{meta.rj_id}] File {track.title} already completed in DB and exists on disk. Skipping.")
                    prog.update_task(main_task, advance=track.size)
                    prog.remove_task(file_task)
                    return

                # If the final file exists and is the correct size, we're done
                if path.exists() and path.stat().st_size == track.size:
                    if attempt == 0:
                        self.stats.skipped += 1
                    prog.update_task(main_task, advance=track.size)
                    prog.remove_task(file_task)
                    return

                existing_size = tmp_path.stat().st_size if tmp_path.exists() else 0
                
                if existing_size > track.size:
                    existing_size = 0
                    tmp_path.unlink()

                headers = {"Range": f"bytes={existing_size}-"} if existing_size else {}
                if existing_size:
                    logging.debug(f"[RJ{meta.rj_id}] Resuming {track.title} from byte {existing_size}")
                
                async with self.sem:
                    async with await self.kernel.stream(track.url, headers) as resp:
                        if resp.status == 416:
                            # Range not satisfiable, start over
                            existing_size = 0
                            headers = {}
                            if tmp_path.exists():
                                tmp_path.unlink()
                            # It will retry on the next attempt loop iteration
                            raise Exception("HTTP 416 Range Not Satisfiable")
                            
                        if resp.status not in [200, 206]:
                            if attempt == 19:
                                self.stats.failed += 1
                                reason = f"HTTP {resp.status}"
                                self.stats.failures.append((track.title, reason))
                                msg = f"Failed: {track.title} ({reason}) - URL: {track.url}"
                                self.log_ui(f"[red]{msg}[/red]")
                                logging.error(msg)
                            continue
                        
                        mode = "ab" if resp.status == 206 else "wb"
                        async with aiofiles.open(tmp_path, mode) as f:
                            async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                                await self._consume_bandwidth(len(chunk))
                                await f.write(chunk)
                                prog.update_task(main_task, advance=len(chunk))
                                prog.update_task(file_task, advance=len(chunk))
                                self.stats.bytes_downloaded += len(chunk)
                
                # Verify download completed successfully
                if tmp_path.exists():
                    actual_size = tmp_path.stat().st_size
                    if track.size > 0 and actual_size != track.size:
                        raise Exception(
                            f"File size mismatch. Expected {track.size}, got {actual_size}"
                        )
                    # Rename .tmp -> final path (track.size == 0 means server didn't report size)
                    if path.exists():
                        path.unlink()
                    tmp_path.rename(path)
                    logging.debug(f"[RJ{meta.rj_id}] Successfully downloaded {track.title}")
                else:
                    raise Exception(f"Temp file missing after download for {track.title}")
                
                if self.config.tag_audio and track.type == 'audio':
                    await asyncio.to_thread(AudioProcessor.apply_tags, path, meta, cover)
                
                self.db.file_state_update(meta.rj_id, str(path), track.size, track.size, 'completed')
                self.stats.success += 1
                prog.remove_task(file_task)
                return
                
            except Exception as e:
                logging.warning(f"Attempt {attempt+1}/20 failed for {track.title}: {e}")
                if attempt == 19:
                    self.stats.failed += 1
                    reason = f"{type(e).__name__}: {e}"
                    self.stats.failures.append((track.title, reason))
                    msg = f"Failed: {track.title} ({type(e).__name__})"
                    self.log_ui(f"[red]{msg}[/red]")
                    prog.remove_task(file_task)
                    return
                await asyncio.sleep(1)

