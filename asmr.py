import asyncio
import re
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Literal, List
from dataclasses import dataclass
import aiofiles
import aiohttp
import tkinter as tk
from tkinter import filedialog
from tqdm import tqdm
import keyboard

HOSTNAME = "https://api.asmr-200.com"
RJ_RE = re.compile(r"(?:RJ)?(?P<id>[\d]+)")
CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB chunks
MAX_CONCURRENT_DOWNLOADS = 3  # Limit concurrent downloads
CONFIG_FILE = Path("config.json")
LOG_FILE = Path("download_log.txt")
RETRY_ATTEMPTS = 3  # Number of retries for failed downloads
PAUSED = False  # Global pause state

@dataclass
class WorkTrack:
    filename: str
    url: str
    type: Literal["folder", "text", "image", "audio"]
    save_path: Path
    size: int | None = None
    folder_path: str = ""  # Store folder hierarchy
    status: str = "Pending"  # Track download status

    def is_hq(self) -> bool | None:
        if self.type != "audio":
            return None
        return self.filename.endswith(".flac") or self.filename.endswith(".wav") or self.filename.endswith(".mp3")

async def log_message(message: str):
    async with aiofiles.open(LOG_FILE, "a", encoding="utf-8") as f:
        await f.write(f"[{datetime.now().isoformat()}] {message}\n")

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config.json: {e}")
            sys.exit(1)
    return {"output_dir": str(Path.cwd()), "default_file_types": ["audio", "image", "text"], "hq_audio_only": False}

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config.json: {e}")

def create_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Origin": "https://asmr.one",
            "Referer": "https://asmr.one/",
            "Accept": "application/json"
        }
    )

def select_directory(current_dir: str) -> str:
    root = tk.Tk()
    root.withdraw()
    selected_dir = filedialog.askdirectory(
        initialdir=current_dir,
        title="Select Output Directory"
    )
    root.destroy()
    return selected_dir if selected_dir else current_dir

def transform_work_data(data: list[dict], base_folder: Path, parent_folder: str = "") -> list[WorkTrack]:
    if not data:
        return []
    current_data = []
    for item in data:
        folder_path = f"{parent_folder}/{item['title']}" if parent_folder else item["title"]
        match item["type"]:
            case "folder":
                folder_base = base_folder / item["title"]
                current_data.extend(transform_work_data(item["children"], folder_base, folder_path))
            case "text" | "image" | "audio":
                current_data.append(WorkTrack(
                    filename=item["title"],
                    url=item["mediaDownloadUrl"],
                    type=item["type"],
                    save_path=base_folder / item["title"],
                    size=item.get("size"),
                    folder_path=parent_folder
                ))
    return current_data

async def fetch_work_tracks(session: aiohttp.ClientSession, work_id: str, base_dir: Path) -> list[WorkTrack]:
    cache_file = base_dir / f"RJ{work_id}_tracks.json"
    if cache_file.exists():
        try:
            async with aiofiles.open(cache_file, "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
            print(f"Using cached tracks for RJ{work_id}")
            await log_message(f"Using cached tracks for RJ{work_id}")
        except Exception as e:
            print(f"Error reading cache file for RJ{work_id}: {e}. Fetching from API...")
            await log_message(f"Error reading cache file for RJ{work_id}: {e}")
            data = None
    else:
        data = None

    if not data:
        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with session.get(f"{HOSTNAME}/api/tracks/{work_id}?v=2", timeout=30) as response:
                    response.raise_for_status()
                    data = await response.json()
                    async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
                        await f.write(json.dumps(data))
                    print(f"Successfully fetched tracks from {HOSTNAME}")
                    await log_message(f"Successfully fetched tracks from {HOSTNAME} for RJ{work_id}")
                    break
            except aiohttp.ClientError as e:
                if attempt < RETRY_ATTEMPTS - 1:
                    print(f"Error fetching tracks for RJ{work_id}: {e}. Retrying ({attempt + 2}/{RETRY_ATTEMPTS})...")
                    await log_message(f"Error fetching tracks for RJ{work_id}: {e}. Retrying ({attempt + 2}/{RETRY_ATTEMPTS})...")
                    await asyncio.sleep(2)
                else:
                    print(f"Failed to fetch tracks for RJ{work_id} after {RETRY_ATTEMPTS} attempts: {e}")
                    await log_message(f"Failed to fetch tracks for RJ{work_id} after {RETRY_ATTEMPTS} attempts: {e}")
                    return []
    return transform_work_data(data, base_dir / f"RJ{work_id}")

async def fetch_work_metadata(session: aiohttp.ClientSession, work_id: str) -> dict:
    for attempt in range(RETRY_ATTEMPTS):
        try:
            async with session.get(f"{HOSTNAME}/api/workInfo/{work_id}", timeout=30) as response:
                response.raise_for_status()
                data = await response.json()
                print(f"Successfully fetched metadata from {HOSTNAME}")
                await log_message(f"Successfully fetched metadata from {HOSTNAME} for RJ{work_id}")
                return data
        except aiohttp.ClientError as e:
            if attempt < RETRY_ATTEMPTS - 1:
                print(f"Error fetching metadata for RJ{work_id}: {e}. Retrying ({attempt + 2}/{RETRY_ATTEMPTS})...")
                await log_message(f"Error fetching metadata for RJ{work_id}: {e}. Retrying ({attempt + 2}/{RETRY_ATTEMPTS})...")
                await asyncio.sleep(2)
            else:
                print(f"Failed to fetch metadata for RJ{work_id} after {RETRY_ATTEMPTS} attempts: {e}")
                await log_message(f"Failed to fetch metadata for RJ{work_id} after {RETRY_ATTEMPTS} attempts: {e}")
                return {}
    return {}

async def search_rj_ids(session: aiohttp.ClientSession, query: str, limit: int = 10) -> List[str]:
    rj_ids = []
    page = 1
    while True:
        try:
            async with session.get(f"{HOSTNAME}/api/search?query={query}&page={page}&size=50", timeout=30) as response:
                if response.status != 200:
                    await log_message(f"Search failed for query '{query}' at page {page}: {response.status}")
                    print(f"Search failed for query '{query}' at page {page}: {response.status}")
                    break
                data = await response.json()
                works = data.get("works", [])
                if not works:
                    break
                rj_ids.extend([work["id"] for work in works if "id" in work])
                if len(rj_ids) >= limit or len(works) < 50:
                    break
                page += 1
                await asyncio.sleep(1)
        except aiohttp.ClientError as e:
            print(f"Error searching for '{query}': {e}")
            await log_message(f"Error searching for '{query}': {e}")
            break
    return rj_ids[:limit]

async def download_track(session: aiohttp.ClientSession, track: WorkTrack, track_index: int) -> tuple[bool, float]:
    global PAUSED
    if await check_file_integrity(track):
        track.status = "Skipped"
        msg = f"{track.filename} already downloaded and intact. Skipping."
        await log_message(msg)
        print(msg)
        return True, 0

    downloaded_bytes = 0
    total_size = track.size or 0
    track.status = "Downloading"
    file_desc = track.filename[:30] + "..." if len(track.filename) > 30 else track.filename
    total_mb = total_size / 1024 / 1024 if total_size else None

    for attempt in range(RETRY_ATTEMPTS):
        try:
            msg = f"Starting download: {track.filename} ({track_index+1}/{MAX_CONCURRENT_DOWNLOADS})"
            print(msg)
            await log_message(msg)
            track.save_path.parent.mkdir(parents=True, exist_ok=True)
            
            existing_size = track.save_path.stat().st_size if track.save_path.exists() else 0
            headers = {"Range": f"bytes={existing_size}-"} if existing_size else {}
            
            with tqdm(total=total_size, desc=f"File {track_index+1}: {file_desc}", unit="B", unit_scale=True, unit_divisor=1024, 
                      position=track_index, leave=False, mininterval=0.1, smoothing=0.3) as pbar:
                async with session.get(track.url, headers=headers, timeout=60) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get("content-length", track.size or 0)) + existing_size
                    pbar.total = total_size  # Update total size in progress bar
                    mode = "ab" if existing_size else "wb"
                    async with aiofiles.open(track.save_path, mode) as fp:
                        async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                            while PAUSED:
                                await asyncio.sleep(0.1)
                            await fp.write(chunk)
                            downloaded_bytes += len(chunk)
                            pbar.update(len(chunk))
            track.status = "Completed"
            print(f"Completed download: {track.filename}")
            await log_message(f"Completed download: {track.filename}")
            return True, downloaded_bytes / 1024 / 1024
        except aiohttp.ClientResponseError as e:
            if attempt < RETRY_ATTEMPTS - 1:
                track.status = "Retrying"
                print(f"Error downloading {track.filename}: HTTP {e.status}, {e.message}. Retrying ({attempt + 2}/{RETRY_ATTEMPTS})...")
                await log_message(f"Error downloading {track.filename}: HTTP {e.status}, {e.message}. Retrying ({attempt + 2}/{RETRY_ATTEMPTS})...")
                await asyncio.sleep(2)
            else:
                track.status = "Error"
                print(f"Failed to download {track.filename} after {RETRY_ATTEMPTS} attempts: HTTP {e.status}, {e.message}")
                await log_message(f"Failed to download {track.filename} after {RETRY_ATTEMPTS} attempts: HTTP {e.status}, {e.message}")
                return False, 0
        except Exception as e:
            if attempt < RETRY_ATTEMPTS - 1:
                track.status = "Retrying"
                print(f"Unexpected error downloading {track.filename}: {e}. Retrying ({attempt + 2}/{RETRY_ATTEMPTS})...")
                await log_message(f"Unexpected error downloading {track.filename}: {e}. Retrying ({attempt + 2}/{RETRY_ATTEMPTS})...")
                await asyncio.sleep(2)
            else:
                track.status = "Error"
                print(f"Failed to download {track.filename} after {RETRY_ATTEMPTS} attempts: {e}")
                await log_message(f"Failed to download {track.filename} after {RETRY_ATTEMPTS} attempts: {e}")
                return False, 0
    track.status = "Error"
    return False, 0

async def check_file_integrity(track: WorkTrack) -> bool:
    return track.save_path.exists()

async def monitor_pause_resume():
    global PAUSED
    PAUSED = False  # Reset PAUSED at start
    while True:
        try:
            if keyboard.is_pressed('p'):
                PAUSED = True
                print("Downloads paused. Press 'r' to resume.")
                await log_message("Downloads paused")
                while PAUSED and not keyboard.is_pressed('r'):
                    await asyncio.sleep(0.1)
                if keyboard.is_pressed('r'):
                    PAUSED = False
                    print("Downloads resumed.")
                    await log_message("Downloads resumed")
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in pause/resume monitor: {e}")
            await log_message(f"Error in pause/resume monitor: {e}")

async def select_files_to_download(tracks: List[WorkTrack], config: dict, work_id: str) -> List[WorkTrack]:
    if not tracks:
        print("No files found to download.")
        return []
    
    config_file_types = config.get("default_file_types", ["audio", "image", "text"])
    print("\nAvailable files (checked against local metadata):")
    print(f"A. RJ{work_id}")

    folder_dict = {}
    for track in tracks:
        folder = track.folder_path or ""
        if folder not in folder_dict:
            folder_dict[folder] = []
        folder_dict[folder].append(track)
    
    integrity_status = []
    for track in tracks:
        status = await check_file_integrity(track)
        integrity_status.append(status)
        if status:
            track.status = "Skipped"
    
    file_index = 1
    folder_index = 0
    index_map = {}
    for folder, folder_tracks in sorted(folder_dict.items(), key=lambda x: x[0] or ""):
        if folder:
            folder_index += 1
            print(f"   {chr(96 + folder_index)}. {folder}")
        for track in folder_tracks:
            size_str = f"{track.size / 1024 / 1024:.2f} MB" if track.size else "Unknown size"
            status_str = "Downloaded" if integrity_status[tracks.index(track)] else "Not downloaded"
            indent = "      " if folder else "   "
            print(f"{indent}{file_index}. {track.filename} ({track.type}, {size_str}, {status_str})")
            index_map[file_index] = track
            file_index += 1
    
    print("\nOptions:")
    print("1. Download all remaining/incomplete files")
    print(f"2. Download default file types from config ({', '.join(config_file_types)})")
    print("3. Select by file type (audio, image, text)")
    print("4. Select specific files by index")
    print("5. Download only high-quality audio (FLAC/WAV/MP3)")
    while True:
        choice = input("Enter your choice (1-5): ").strip()
        if choice in ["1", "2", "3", "4", "5"]:
            break
        print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")

    selected_tracks = []
    if choice == "1":
        selected_tracks = [track for i, track in enumerate(tracks) if not integrity_status[i]]
    elif choice == "2":
        selected_tracks = [track for i, track in enumerate(tracks) if track.type in config_file_types and not integrity_status[i]]
    elif choice == "3":
        while True:
            file_type = input("Enter file type (audio, image, text): ").strip().lower()
            if file_type in ["audio", "image", "text"]:
                break
            print("Invalid file type. Please enter audio, image, or text.")
        selected_tracks = [track for i, track in enumerate(tracks) if track.type == file_type and not integrity_status[i]]
    elif choice == "4":
        while True:
            indices = input("Enter file indices (e.g., 1,3,5 or 1-3): ").strip()
            try:
                selected_indices = set()
                for part in indices.split(","):
                    if "-" in part:
                        start, end = map(int, part.split("-"))
                        if start < 1 or end > len(tracks):
                            raise ValueError("Index out of range")
                        selected_indices.update(range(start, end + 1))
                    else:
                        idx = int(part)
                        if idx < 1 or idx > len(tracks):
                            raise ValueError("Index out of range")
                        selected_indices.add(idx)
                break
            except ValueError as e:
                print(f"Invalid input: {e}. Please try again.")
        selected_tracks = [index_map[i] for i in selected_indices if not integrity_status[tracks.index(index_map[i])]]
    elif choice == "5":
        selected_tracks = [track for i, track in enumerate(tracks) if track.type == "audio" and track.is_hq() and not integrity_status[i]]

    if not selected_tracks:
        print(f"No files selected for RJ{work_id}. Skipping.")
        await log_message(f"No files selected for RJ{work_id}. Skipping.")
        return []
    
    total_size = sum(track.size or 0 for track in selected_tracks) / 1024 / 1024
    print(f"\nSelected {len(selected_tracks)} files to download (Total: {total_size:.2f} MB):")
    for track in selected_tracks:
        size_str = f"{track.size / 1024 / 1024:.2f} MB" if track.size else "Unknown size"
        print(f"- {track.filename} ({track.type}, {size_str})")
    print(f"\nRemaining {len(selected_tracks)} files to download:")
    for track in selected_tracks:
        size_str = f"{track.size / 1024 / 1024:.2f} MB" if track.size else "Unknown size"
        print(f"- {track.filename} ({track.type}, {size_str})")
    
    return selected_tracks

async def process_work(work_id: str, base_dir: Path, config: dict) -> tuple[int, float, float]:
    start_time = datetime.now()
    downloaded_files = 0
    total_size_downloaded = 0
    max_retries = 3  # Max retry attempts for failed files
    async with create_session() as session:
        print(f"\n=== Processing RJ{work_id} ===")
        await log_message(f"Processing RJ{work_id}")
        try:
            print("Fetching metadata...")
            await log_message(f"Fetching metadata for RJ{work_id}")
            work_metadata = await fetch_work_metadata(session, work_id)
            if not work_metadata:
                print(f"Skipping RJ{work_id} due to metadata fetch failure.")
                await log_message(f"Skipping RJ{work_id} due to metadata fetch failure.")
                return 0, 0, 0
            title = work_metadata.get('title', 'Unknown')
            print(f"Title: {title}")
            await log_message(f"Title: {title}")
            print(f"Fetching tracks...")
            work_tracks = await fetch_work_tracks(session, work_id, base_dir)
            if not work_tracks:
                print(f"No tracks found for RJ{work_id}. Skipping.")
                await log_message(f"No tracks found for RJ{work_id}. Skipping.")
                return 0, 0, 0
            print(f"Found {len(work_tracks)} files.")
            await log_message(f"Found {len(work_tracks)} files for RJ{work_id}")

            selected_tracks = await select_files_to_download(work_tracks, config, work_id)
            if not selected_tracks:
                print(f"No files selected for download. Skipping RJ{work_id}.")
                await log_message(f"No files selected for RJ{work_id}. Skipping.")
                return 0, 0, 0

            retry_count = 0
            while selected_tracks and retry_count < max_retries:
                print(f"\nStarting download for {len(selected_tracks)} files (Attempt {retry_count + 1}/{max_retries}, Press 'p' to pause, 'r' to resume):")
                await log_message(f"Starting download for {len(selected_tracks)} files for RJ{work_id} (Attempt {retry_count + 1}/{max_retries})")
                asyncio.create_task(monitor_pause_resume())
                semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
                async def limited_download(track, index):
                    nonlocal downloaded_files, total_size_downloaded
                    try:
                        async with semaphore:
                            success, size_mb = await download_track(session, track, index)
                            if success:
                                downloaded_files += 1
                                total_size_downloaded += size_mb
                    except Exception as e:
                        print(f"Error in limited_download for {track.filename}: {e}")
                        await log_message(f"Error in limited_download for {track.filename}: {e}")

                tasks = [limited_download(track, i % MAX_CONCURRENT_DOWNLOADS) for i, track in enumerate(selected_tracks)]
                await asyncio.gather(*tasks)

                # Check which files are still missing
                retry_tracks = []
                for track in selected_tracks:
                    if not await check_file_integrity(track):
                        retry_tracks.append(track)
                        print(f"File {track.filename} not found. Scheduling for retry.")
                        await log_message(f"File {track.filename} not found. Scheduling for retry.")
                
                selected_tracks = retry_tracks
                retry_count += 1
                if selected_tracks and retry_count < max_retries:
                    print(f"\nRetrying {len(selected_tracks)} failed files...")
                    await log_message(f"Retrying {len(selected_tracks)} failed files for RJ{work_id}")
                elif selected_tracks:
                    print(f"\nFailed to download {len(selected_tracks)} files after {max_retries} attempts:")
                    for track in selected_tracks:
                        print(f"- {track.filename} ({track.type}, {track.size / 1024 / 1024:.2f} MB)")
                    await log_message(f"Failed to download {len(selected_tracks)} files for RJ{work_id} after {max_retries} attempts")

            # Final verification of downloaded files
            verified_downloaded = 0
            failed_files = []
            for track in work_tracks:
                if await check_file_integrity(track):
                    verified_downloaded += 1
                elif track in selected_tracks:
                    failed_files.append(track)
        
        except Exception as e:
            msg = f"Error processing RJ{work_id}: {str(e)}"
            print(msg)
            await log_message(msg)
            return 0, 0, 0
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        avg_speed = total_size_downloaded / duration if duration > 0 and total_size_downloaded > 0 else 0
        print(f"\nSummary for RJ{work_id}:")
        print(f"- Files selected: {len(work_tracks)}")
        print(f"- Files downloaded (verified on disk): {verified_downloaded}")
        print(f"- Total size: {total_size_downloaded:.2f} MB")
        print(f"- Time taken: {duration:.2f} seconds")
        print(f"- Average speed: {avg_speed:.2f} MB/s")
        if failed_files:
            print(f"- Failed files ({len(failed_files)}):")
            for track in failed_files:
                size_str = f"{track.size / 1024 / 1024:.2f} MB" if track.size else "Unknown size"
                print(f"  - {track.filename} ({track.type}, {size_str})")
        await log_message(f"Summary for RJ{work_id}: {len(work_tracks)} selected, {verified_downloaded} downloaded, {total_size_downloaded:.2f} MB, {duration:.2f} seconds, {avg_speed:.2f} MB/s")
        if failed_files:
            await log_message(f"Failed files for RJ{work_id}: {[track.filename for track in failed_files]}")
        return verified_downloaded, total_size_downloaded, avg_speed

async def main():
    parser = argparse.ArgumentParser(description="ASMR Downloader for asmr.one", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    parser.add_argument("-c", "--config", action="store_true", help="Show or edit config.json")
    parser.add_argument("-s", "--search", nargs=2, metavar=("QUERY", "LIMIT"), help="Search mode with query and limit")
    parser.add_argument("rj_ids", nargs="*", help="RJ IDs to download (e.g., RJ387142)")
    
    args = parser.parse_args()

    if args.help:
        print("ASMR Downloader Usage:")
        print("  Run in manual mode: .\\asmr RJXXXXX [RJYYYYY ...]")
        print("  Run in search mode: .\\asmr -s \"query\" limit")
        print("  Show/edit config: .\\asmr -c")
        print("  Show help: .\\asmr -h")
        print("\nOptions:")
        print("  -h, --help        Show this help message and exit")
        print("  -c, --config      Show or edit config.json")
        print("  -s, --search      Search mode with query and limit (e.g., -s \"whisper\" 10)")
        sys.exit(0)

    if args.config:
        config = load_config()
        print("\nCurrent config.json:")
        print(json.dumps(config, indent=2))
        edit = input("\nEdit config? (y/n): ").strip().lower()
        if edit == "y":
            print("Select new output directory:")
            new_output_dir = select_directory(config["output_dir"])
            new_file_types = input(f"Default file types [{', '.join(config['default_file_types'])}]: ").strip()
            new_file_types = new_file_types.split(",") if new_file_types else config["default_file_types"]
            new_hq_audio = input(f"HQ audio only [{config['hq_audio_only']}]: ").strip().lower()
            new_hq_audio = new_hq_audio == "true" if new_hq_audio else config["hq_audio_only"]
            config.update({
                "output_dir": new_output_dir,
                "default_file_types": [t.strip() for t in new_file_types if t.strip() in ["audio", "image", "text"]],
                "hq_audio_only": new_hq_audio
            })
            save_config(config)
            print("Config updated.")
        sys.exit(0)

    config = load_config()
    base_dir = Path(config.get("output_dir", Path.cwd()))
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory {base_dir}: {e}")
        sys.exit(1)

    total_files = 0
    total_size = 0
    total_speed = 0
    start_time = datetime.now()

    if args.search:
        query, limit = args.search
        try:
            limit = int(limit)
            if limit <= 0:
                raise ValueError("Search limit must be positive")
        except ValueError:
            print("Search limit must be a positive number.")
            sys.exit(1)
        async with create_session() as session:
            print(f"Searching for '{query}' (limit: {limit})...")
            await log_message(f"Searching for '{query}' with limit {limit}")
            rj_ids = await search_rj_ids(session, query, limit)
            print(f"Found {len(rj_ids)} RJ IDs.")
            await log_message(f"Found {len(rj_ids)} RJ IDs for query '{query}'")
            for work_id in rj_ids:
                files, size, speed = await process_work(work_id, base_dir, config)
                total_files += files
                total_size += size
                total_speed += speed
    else:
        print(f"Current output directory: {base_dir}")
        change_dir = input("Change output directory? (y/n): ").strip().lower()
        if change_dir == "y":
            new_dir = select_directory(str(base_dir))
            config["output_dir"] = new_dir
            base_dir = Path(new_dir)
            save_config(config)
            print(f"Output directory changed to: {base_dir}")
        
        mode = "1" if args.rj_ids else None
        if not mode:
            print("\nMode selection:")
            print("1. Manual RJ IDs")
            print("2. Search (Collecting Mode)")
            while True:
                mode = input("Enter mode (1 or 2): ").strip()
                if mode in ["1", "2"]:
                    break
                print("Invalid mode. Please enter 1 or 2.")

        if mode == "1":
            rj_ids = args.rj_ids if args.rj_ids else input("Enter RJ IDs (e.g., RJ387142 RJ385913): ").strip().split()
            if not rj_ids:
                print("No RJ IDs provided. Exiting.")
                sys.exit(1)
            for rj in rj_ids:
                match = RJ_RE.search(rj)
                if match is None:
                    print(f"Invalid RJ ID: {rj}")
                    await log_message(f"Invalid RJ ID: {rj}")
                    continue
                work_id = match.group("id")
                files, size, speed = await process_work(work_id, base_dir, config)
                total_files += files
                total_size += size
                total_speed += speed
        else:
            query = input("Enter search query (e.g., whisper): ").strip()
            while True:
                try:
                    limit = int(input("Enter search limit (max RJ IDs, e.g., 10): ").strip())
                    if limit > 0:
                        break
                    print("Search limit must be a positive number.")
                except ValueError:
                    print("Search limit must be a number.")
            async with create_session() as session:
                print(f"Searching for '{query}' (limit: {limit})...")
                await log_message(f"Searching for '{query}' with limit {limit}")
                rj_ids = await search_rj_ids(session, query, limit)
                print(f"Found {len(rj_ids)} RJ IDs.")
                await log_message(f"Found {len(rj_ids)} RJ IDs for query '{query}'")
                for work_id in rj_ids:
                    files, size, speed = await process_work(work_id, base_dir, config)
                    total_files += files
                    total_size += size
                    total_speed += speed

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    avg_speed = total_size / duration if duration > 0 and total_size > 0 else 0
    print("\nOverall Summary:")
    print(f"- Total files downloaded: {total_files}")
    print(f"- Total size: {total_size:.2f} MB")
    print(f"- Time taken: {duration:.2f} seconds")
    print(f"- Average speed: {avg_speed:.2f} MB/s")
    await log_message(f"Overall Summary: {total_files} files, {total_size:.2f} MB, {duration:.2f} seconds, {avg_speed:.2f} MB/s")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error in main: {e}")
        sys.exit(1)