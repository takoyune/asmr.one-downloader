# 🎙️ ASMR.ONE Downloader

[![Version](https://img.shields.io/badge/version-1.2.07072026-blueviolet.svg)](#)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)

An asynchronous, terminal-based downloader for [ASMR.ONE](https://asmr.one). Downloads are persistent, resumable, bandwidth-throttled, and organized into a local SQLite library. Works from an interactive menu or entirely from the command line.

---

## 📋 Table of Contents

<div align="center">

| | | |
|:---:|:---:|:---:|
| [✨ Features](#-features) | [📦 Requirements](#-requirements) | [🚀 Installation](#-installation) |
| [▶️ Running the App](#️-running-the-app) | [🖥️ Interactive Menu](#️-usage--interactive-menu) | [🔧 CLI Flags](#-usage--cli-flags) |
| [⚙️ Configuration](#️-configuration) | [📁 Project Structure](#-project-structure) | [🔍 Troubleshooting](#-troubleshooting) | [📝 License](#-license) | |

</div>

---

## ✨ Features

### Download Engine
- **Async concurrent downloads** via `asyncio` + `aiohttp`. Configurable concurrency (default: 3 parallel files).
- **Resume support** — downloads use HTTP `Range` headers. A `.tmp` file is kept between sessions and extended on restart. No re-downloading from the beginning.
- **3-attempt retry loop** per file. After exhausting retries, the failure is recorded with its reason (HTTP status, exception type, or directory error) and displayed in the Session Report.
- **Token-bucket bandwidth limiter** — set `bandwidth_limit_mbps` in config to cap download speed globally. `0` means unlimited.
- **Mirror speed test on startup** — all configured API mirrors are pinged in parallel and the fastest is selected automatically.

### Library & Queue
- **SQLite library** (`history.db`) tracks every completed download: Work code (RJ/VJ), title, local path, file size, date.
- **Duplicate detection** — before anything is queued, the app checks the library. Already-owned works are skipped with a notice.
- **Persistent queue** — the download queue lives in the database, not in memory. Interrupted sessions survive a restart. Use `--resume` to continue.
- **Format priority deduplication** — when a work includes both WAV and MP3 versions of the same track, only the preferred format (per your `format_priority` list) is downloaded.

### CLI & UI
- **`--list`** — print the full folder/file tree of any work code (RJ/VJ) without downloading.
- **`--dry-run`** — simulate a download interactively: shows which files would be fetched and total size, writes nothing to disk.
- **`--all`** — skip the file-selection prompt and download everything.
- **`--batch`** — load a `.txt` file of work codes (RJ/VJ) and queue them all.
- **Session Report** — after each job: success/fail/skipped counts, elapsed time, average speed, and a per-file failure details table when errors occurred.
- **Retry prompt** — at the end of a batch, any failed work codes are collected and you are offered a single-key retry.
- **Windows completion beep** — a system notification sound plays when the full queue finishes.

### Metadata & Organization
- **Audio tagging** (`mutagen`) — title, artist, album, and cover art are written to MP3, FLAC, and OGG files after download.
- **Flexible folder naming** — configurable `dir_template` using `{rj_id}`, `{title}`, `{circle}`, `{year}`.
- **Optional file sorting** — enable `sort_files` to separate downloads into `Audio/`, `Images/`, `Text/` subdirectories.

---

## 📦 Requirements

- **Python 3.10 or higher** — download from [python.org](https://www.python.org/downloads/)
- A terminal with ANSI color support:
  - Windows: **Windows Terminal** (recommended), VS Code terminal, or PowerShell 7+
  - macOS/Linux: any modern terminal emulator
- **Git** (for cloning) — download from [git-scm.com](https://git-scm.com/)

Python packages (installed automatically by `setup.bat` or `pip install -r requirements.txt`):

| Package | Purpose |
|---------|---------|
| `aiohttp` | Async HTTP client for downloads and API calls |
| `aiofiles` | Async file I/O for writing download chunks |
| `aiodns` | Custom DNS resolver (bypasses ISP-level blocking) |
| `rich` | Terminal UI — progress bars, tables, panels, color |
| `mutagen` | Audio metadata tagging (MP3, FLAC, OGG) |
| `pydantic` | Config validation and schema enforcement |
| `requests` | Used for synchronous GitHub update check |
| `packaging` | Version string parsing for update comparison |

---

## 🚀 Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/takoyune/asmr.one-downloader.git
cd asmr.one-downloader
```

Or download the ZIP directly from GitHub:
1. Click the green **Code** button on the repository page
2. Select **Download ZIP**
3. Extract the ZIP to a folder of your choice
4. Open a terminal in that folder

### Step 2 — Install dependencies

**Option A: Automated (Windows)**

Run the provided setup script. It creates a virtual environment and installs all dependencies into it:

```bat
setup.bat
```

After it finishes, all future launches via `./asmr` will use the virtual environment automatically.

**Option B: Manual (Windows / Linux / macOS)**

If you prefer to manage your own environment:

```bash
# (Optional but recommended) Create a virtual environment
python -m venv venv

# Activate it
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3 — Verify the install

```bash
python main.py --version
```

You should see the current version printed. If you see a `ModuleNotFoundError`, re-run the install step or check that the correct virtual environment is active.

---

## ▶️ Running the App

### Windows

```powershell
./asmr              # Open interactive menu
./asmr RJ123456     # Download directly
./asmr --help       # All available flags
```

> CMD users: `asmr.bat` works the same way — just type `asmr RJ123456`

### Linux / macOS

An `asmr` shell launcher is already included in the repo. Just make it executable once after cloning:

```bash
chmod +x asmr
```

Then use it the exact same way as Windows:

```bash
./asmr                      # Open interactive menu
./asmr RJ123456             # Download directly
./asmr --list RJ123456      # Preview file tree without downloading
./asmr --dry-run RJ123456   # Simulate a download
./asmr --help               # All available flags
```

---

## 🖥️ Usage — Interactive Menu

Launch `./asmr` with no arguments:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃         ASMR.ONE DOWNLOADER            ┃
┃            by Takoyune                 ┃
┗━━━━━━━━━━━━━━━━━━━ 📚 Library: 3 works ━┛

[1] Download (Work Codes)
[2] Batch Download from File
[3] Library Browser
[4] Queue Manager
[5] Settings
[6] Statistics Dashboard
[7] System Utilities
[X] Exit
```

#### [1] Download (Work Codes)
Enter one or more work codes separated by spaces (e.g. `RJ123456 VJ01002074`). The app fetches metadata, presents the full file tree, and lets you select specific files by number or range (e.g. `1 3-5 7`). Leave the selection blank to download everything.

#### [2] Batch Download from File
Enter the path to a `.txt` file with one work code (RJ or VJ) per line. All codes are validated, checked against your library, and added to the queue. The queue then processes them in order.

```
# Example batch file (my_list.txt)
RJ01234567
VJ01002074
RJ00112233
```

#### [3] Library Browser
Search your local download history by title or circle name (partial matches supported). Shows the local folder path and file size for each result.

#### [4] Queue Manager
View all items currently in the queue (pending / active / error status). Add new codes, change download priority, or remove items before they start.

#### [5] Settings
Edit all configuration options interactively without touching `config.json` manually. Includes a `format_priority` list editor where you can add, remove, and reorder your preferred formats.

#### [6] Statistics Dashboard
Overview of your library: total works, total size on disk, queue length, and average work size.

#### [7] System Utilities
- **Cache Cleaner** — Scans for `.tmp` and `.asmr_selection.json` files. Shows a summary with sizes before asking for confirmation.
- **Network Diagnostics** — Tests all configured API mirrors and shows latency for each.
- **Mirror Selector** — Re-run the speed test and update the active mirror in config.

---

## 🔧 Usage — CLI Flags

Full reference:

```
usage: ./asmr [-h] [-b FILE] [-a] [--list] [--export FILE] [--test] 
              [--dry-run] [--resume] [--no-update-check] [--verbose] [-v]
              [rj_codes ...]
```

| Flag | Short | Description |
|------|-------|-------------|
| `work_codes` | — | One or more work codes (RJ or VJ) to queue and download immediately |
| `--batch FILE` | `-b` | Path to a `.txt` file containing work codes (RJ/VJ), one per line |
| `--all` | `-a` | Skip the file-selection prompt; download all tracks |
| `--list` | — | Print the full track tree for each work code and exit (no download) |
| `--export FILE` | — | Export the library to a CSV or JSON file (e.g., `library.csv`) |
| `--test` | — | Test all API mirrors and display detailed latency and error information |
| `--dry-run` | — | Show which files would be downloaded and total size; write nothing to disk |
| `--resume` | — | Skip mirror test and update check; process existing queue immediately |
| `--no-update-check` | — | Skip the GitHub update check this session |
| `--verbose` | — | Write DEBUG-level logs to `singularity.log` |
| `--version` | `-v` | Print version and exit |
| `--help` | `-h` | Show usage summary |

### CLI Examples

```bash
# Download a single work interactively (RJ or VJ)
./asmr RJ01234567
./asmr VJ01002074

# Download multiple works, skip file selection (get everything)
./asmr --all RJ01234567 VJ01002074

# Check what you'd download before committing
./asmr --dry-run VJ01002074

# Preview the file tree without downloading
./asmr --list VJ01002074

# Run a batch of codes from a file
./asmr --batch my_list.txt

# Batch download everything in the file without prompts
./asmr --batch my_list.txt --all

# Resume a previous session that was interrupted
./asmr --resume

# Quiet session, skip update check
./asmr --no-update-check RJ01234567

# Debug a failed download
./asmr --verbose RJ01234567
# Then check singularity.log for full HTTP logs
```

---

## ⚙️ Configuration

`config.json` is created automatically on first launch in the project root. You can edit it directly or change values through **Settings** in the interactive menu.

```json
{
    "output_dir": "Downloads",
    "max_concurrent": 3,
    "proxy": null,
    "mirror": "https://api.asmr.one",
    "tag_audio": true,
    "sort_files": false,
    "dir_template": "{rj_id} {title}",
    "timeout": 60,
    "dns": "1.1.1.1",
    "bandwidth_limit_mbps": 0.0,
    "format_priority": ["flac", "wav", "mp3", "m4a", "ogg"],
    "last_update_check": 0.0
}
```

| Key | Default | Description |
|-----|---------|-------------|
| 📁 `output_dir` | `"Downloads"` | Where downloaded works are saved |
| ⚡ `max_concurrent` | `3` | Parallel file downloads (1–20) |
| 🌐 `proxy` | `null` | HTTP or SOCKS5 proxy URL |
| 🔗 `mirror` | auto | API mirror URL — set automatically on startup |
| 🎵 `tag_audio` | `true` | Write metadata tags to MP3 / FLAC / OGG |
| 📂 `sort_files` | `false` | Organize into `Audio/`, `Images/`, `Text/` subfolders |
| 🏷️ `dir_template` | `"RJ{rj_id} {title}"` | Folder name template — supports `{rj_id}`, `{title}`, `{circle}`, `{year}` |
| ⏱️ `timeout` | `60` | HTTP request timeout in seconds |
| 🛡️ `dns` | `"1.1.1.1"` | DNS server — use `1.1.1.1` or `8.8.8.8` to bypass ISP blocks |
| 📶 `bandwidth_limit_mbps` | `0.0` | Speed cap in MB/s — `0` = unlimited |
| 🎚️ `format_priority` | `["flac","wav","mp3",…]` | Preferred format when a track has multiple versions |
| 🕐 `last_update_check` | `0.0` | Auto-managed — skips GitHub check if run within 24 h |


### `dir_template` Examples

| Template | Result folder name |
|----------|--------------------|
| `"RJ{rj_id} {title}"` | `RJ01234567 Some Work Title` |
| `"{circle} - {title}"` | `SomeCircle - Some Work Title` |
| `"{year}/{circle}/{title}"` | `2024/SomeCircle/Some Work Title` |

---

## 📁 Project Structure

```
asmr.one-downloader/
│
├── main.py          # Entry point — CLI flags, preflight check, update check
├── asmr             # Linux / macOS launcher  (run: chmod +x asmr)
├── asmr.bat         # Windows CMD launcher
├── asmr.ps1         # Windows PowerShell launcher
├── setup.bat        # First-time setup (creates venv + installs deps)
├── requirements.txt # Python dependencies
├── config.json      # Your settings (auto-created on first run)
├── history.db       # SQLite — library and download queue
├── singularity.log  # Rotating log file
│
└── main/
    ├── app.py           # UI, menus, job execution
    ├── orchestrator.py  # Download logic, retry, stats
    ├── network.py       # HTTP client, mirror management
    ├── db.py            # All database operations
    ├── config.py        # Config loading and validation
    ├── models.py        # Data types (WorkMetadata, TrackItem, etc.)
    ├── audio.py         # Audio metadata tagging
    └── constants.py     # Mirrors, log setup, shared constants
```

---

## 🔍 Troubleshooting

### "All API mirrors are unreachable" or Connection Errors
**ASMR.ONE is actively region-blocked outside of East Asia (Japan, China, etc.).** 
If the startup mirror test fails or you cannot connect, your connection is likely being blocked. We highly recommend using **Cloudflare WARP** to bypass this:

1. Download and install Cloudflare WARP from [https://one.one.one.one/](https://one.one.one.one/)
2. Open the WARP app settings (click the gear icon).
3. Make sure to choose **Traffic and DNS (UDP)** (do *not* just choose the 1.1.1.1 DNS option).
4. Turn on the connection switch and restart the downloader.

Alternatively, if you have your own proxy, you can set the `proxy` field in `config.json` (e.g. `"http://user:pass@ip:port"`).

### Downloads hang or time out repeatedly
- Increase `timeout` in `config.json` (e.g. `120`)
- Reduce `max_concurrent` to `1` or `2` to reduce connection pressure
- Try a different DNS or enable a proxy

### Progress bar starts at wrong percentage on resume
This is a known visual issue. The bar is initialized from file size on disk, not the database state. The download is still resuming correctly from the correct byte offset — the visual will correct itself as data flows in.

### `singularity.log` is too noisy
By default, only `INFO`, `WARNING`, and `ERROR` messages are logged. The `--verbose` flag adds `DEBUG` output (every HTTP request, byte offsets, retry attempts). Only use `--verbose` when actively debugging.

### "Fatal error" on startup with a cryptic message
Check `singularity.log` for the full traceback. The log file is in the project root directory.

### Files are not being tagged after download
Ensure `tag_audio` is `true` in `config.json`. Tagging only applies to MP3, FLAC, and OGG files. WAV files are not tagged (the WAV format has no standard metadata container).


---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

*Created by [Takoyune](https://github.com/takoyune)*
