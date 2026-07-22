<div align="center">
  <h1>🎙️ ASMR.ONE Downloader</h1>
  <p><strong>An asynchronous, terminal-based downloader for <a href="https://asmr.one">ASMR.ONE</a> — persistent, resumable, bandwidth-throttled, and fully scriptable.</strong></p>

  ![Version](https://img.shields.io/badge/version-1.3.22072026-blueviolet.svg?style=for-the-badge)
  ![Python](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
  ![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)
  ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg?style=for-the-badge)
</div>

---

## 📋 Table of Contents

<div align="center">

| | | |
|:---:|:---:|:---:|
| [✨ Features](#-features) | [📦 Requirements](#-requirements) | [🚀 Installation](#-installation) |
| [▶️ Running the App](#️-running-the-app) | [🖥️ Interactive Menu](#️-usage--interactive-menu) | [🔧 CLI Flags](#-usage--cli-flags) |
| [⚙️ Configuration](#️-configuration) | [📁 Project Structure](#-project-structure) | [🔍 Troubleshooting](#-troubleshooting) |

</div>

---

## 🆕 What's New in v1.3.22072026 (Search & Language Overhaul)

A major quality-of-life update focused on smarter online search, tag filtering that mirrors the official website, and full multilingual tag/audio language configuration.

### 🔍 Online Search — Full Overhaul
- **Interactive Search Sub-Menu** — Instead of a single search box, Option `[3] Search ASMR.ONE Online` now opens a dedicated sub-menu:
  ```
  [1] General Keyword / Title Search
  [2] Tag Search (e.g., 耳かき 睡眠 膝枕)
  [3] Voice Actor / CV Search (e.g., 本渡楓)
  [4] Circle Search
  [5] Custom Syntax Filter ($tagw:, $rate:, $duration:)
  [B] Back to Main Menu
  ```
- **Tags Column in Results Table** — Search results now include a **Tags** column so you can immediately see what each work contains.

### 🏷️ Official Website Tag Syntax
- Tag searches now use the exact same filter format as the ASMR.ONE website: **`$tagw:TAG$`**
- Multiple tags are supported via space separation (e.g. `耳かき 睡眠` → `$tagw:耳かき$ $tagw:睡眠$`)
- Also available as CLI flag: `./asmr --tag "耳かき 睡眠"`

### 🌐 Dual Language Priority Settings
Two separate language priority lists are now available in `config.json` and the **Settings** menu:

| Setting | Purpose |
|---------|---------|
| `audio_language_priority` | Preferred spoken/audio language edition for works (e.g. Japanese, English, Chinese) |
| `tag_language_priority` | Language to display tags in search results and file metadata |

Both support `ja-jp`, `en-us`, and `zh-cn` in any order, with fallback chaining. For example:
```json
"audio_language_priority": ["ja-jp", "en-us", "zh-cn"],
"tag_language_priority": ["en-us"]
```
This renders audio in Japanese and tags in English. Change at any time through `[6] Settings`.

### ⌨️ New CLI Flags
| Flag | Description |
|------|-------------|
| `--search QUERY` | Search ASMR.ONE online and get an interactive result table |
| `--tag TAGS` | Tag search using official `$tagw:TAG$` syntax |
| `--va NAME` | Search by Voice Actor / CV name |
| `--circle NAME` | Search by Circle name |

---

## 🔒 Previous Major Updates

<details>
<summary><strong>v1.2.07072026 (Library & Queue Stability)</strong></summary>

### 🗄️ Download Engine
- **Async concurrent downloads** with configurable concurrency (default: 3 parallel files)
- **Resume support** using HTTP `Range` headers — `.tmp` files persist between sessions
- **3-attempt retry loop** per file with per-failure reason logging (HTTP status, exception type)
- **Token-bucket bandwidth limiter** via `bandwidth_limit_mbps` in config
- **Mirror speed test on startup** — all mirrors pinged in parallel, fastest selected automatically

### 📚 Library & Queue
- **SQLite library** (`history.db`) tracking every completed download
- **Duplicate detection** — already-owned works are skipped automatically
- **Persistent queue** — survives interruptions; continue with `--resume`
- **Format priority deduplication** — when WAV and MP3 exist for the same track, only the preferred format is downloaded

### 🖥️ CLI & UI
- **`--list`** — print full folder/file tree without downloading
- **`--dry-run`** — simulate a download and show file sizes
- **`--all`** — skip file-selection prompt
- **`--batch`** — load a `.txt` file of work codes (RJ/VJ)
- **Session Report** — success/fail/skipped counts, elapsed time, average speed
- **Windows completion beep** on queue finish

### 🎵 Metadata & Organization
- **Audio tagging** via `mutagen` — title, artist, album, cover art for MP3/FLAC/OGG
- **Flexible folder naming** via `dir_template` using `{rj_id}`, `{title}`, `{circle}`, `{year}`
- **Optional file sorting** into `Audio/`, `Images/`, `Text/` subdirectories

</details>

---

## ✨ Features

### Download Engine
- **Async concurrent downloads** via `asyncio` + `aiohttp`. Configurable concurrency (default: 3 parallel files).
- **Resume support** — downloads use HTTP `Range` headers. A `.tmp` file is kept between sessions and extended on restart.
- **3-attempt retry loop** per file. Failures are recorded with reason and displayed in the Session Report.
- **Token-bucket bandwidth limiter** — set `bandwidth_limit_mbps` to cap download speed globally. `0` = unlimited.
- **Mirror speed test on startup** — all configured API mirrors are pinged in parallel and the fastest is selected automatically.

### Library & Queue
- **SQLite library** (`history.db`) tracks every completed download: work code, title, local path, file size, date.
- **Duplicate detection** — already-owned works are skipped before queuing.
- **Persistent queue** — the download queue lives in the database. Interrupted sessions survive a restart. Use `--resume` to continue.
- **Format priority deduplication** — only the preferred format is downloaded when a work includes multiple format versions.

### Online Search
- **Keyword / Title search** — search ASMR.ONE and get an interactive numbered result table.
- **Tag search** — uses official ASMR.ONE website syntax (`$tagw:TAG$`), supports multiple tags.
- **Voice Actor & Circle search** — dedicated filters via CLI flags or the interactive sub-menu.
- **Custom syntax filter** — full support for `$rate:`, `$duration:`, `$tagw:`, and other ASMR.ONE query operators.
- **Tags column in search results** — displayed in your configured language (Japanese, English, or Chinese).

### CLI & UI
- **`--search`** — search online from the command line.
- **`--tag`** — tag filter search using official website syntax.
- **`--list`** — print full folder/file tree without downloading.
- **`--dry-run`** — simulate a download; shows files and total size, writes nothing.
- **`--all`** — skip file-selection prompt; download everything.
- **`--batch`** — load a `.txt` file of work codes.
- **Session Report** — after each job: success/fail/skipped counts, elapsed time, average speed.
- **Windows completion beep** — system sound plays when the full queue finishes.

### Metadata & Multilingual Support
- **Audio tagging** (`mutagen`) — title, artist, album, and cover art written to MP3, FLAC, and OGG.
- **Flexible folder naming** — configurable `dir_template` using `{rj_id}`, `{title}`, `{circle}`, `{year}`.
- **Optional file sorting** — enable `sort_files` to organize into `Audio/`, `Images/`, `Text/`.
- **Dual language priority config** — separately control the language for audio editions and tag display.

---

## 📦 Requirements

- **Python 3.10 or higher** — [python.org](https://www.python.org/downloads/)
- A terminal with ANSI color support:
  - Windows: **Windows Terminal** (recommended), VS Code terminal, or PowerShell 7+
  - macOS/Linux: any modern terminal emulator
- **Git** (for cloning) — [git-scm.com](https://git-scm.com/)

Python packages (installed automatically by `setup.bat` or `pip install -r requirements.txt`):

| Package | Purpose |
|---------|---------|
| `aiohttp` | Async HTTP client for downloads and API calls |
| `aiofiles` | Async file I/O for writing download chunks |
| `aiodns` | Custom DNS resolver (bypasses ISP-level blocking) |
| `rich` | Terminal UI — progress bars, tables, panels, color |
| `mutagen` | Audio metadata tagging (MP3, FLAC, OGG) |
| `pydantic` | Config validation and schema enforcement |
| `requests` | Synchronous GitHub update check |
| `packaging` | Version string parsing for update comparison |

---

## 🚀 Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/takoyune/asmr.one-downloader.git
cd asmr.one-downloader
```

Or download the ZIP directly from GitHub and extract to a folder of your choice.

### Step 2 — Install dependencies

**Option A: Automated (Windows)**

```bat
setup.bat
```

Runs once — creates a virtual environment and installs all dependencies. All future `./asmr` launches use the venv automatically.

**Option B: Manual (Windows / Linux / macOS)**

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

---

## ▶️ Running the App

### Windows

```powershell
./asmr              # Open interactive menu
./asmr RJ123456     # Download directly
./asmr --help       # All available flags
```

> CMD users: `asmr.bat` works the same way.

### Linux / macOS

```bash
chmod +x asmr       # One-time step after cloning

./asmr              # Open interactive menu
./asmr RJ123456     # Download directly
./asmr --list RJ123456      # Preview file tree
./asmr --dry-run RJ123456   # Simulate a download
./asmr --help               # All available flags
```

---

## 🖥️ Usage — Interactive Menu

Launch `./asmr` with no arguments:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    ASMR.ONE DOWNLOADER                        ┃
┃                       by Takoyune                             ┃
┃               https://github.com/takoyune                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 📚 Library: 11 works ━┛

[1] Download (Work Codes)
[2] Batch Download from File
[3] Search ASMR.ONE Online
[4] Library Browser
[5] Queue Manager
[6] Settings
[7] Statistics Dashboard
[8] System Utilities
[X] Exit
```

#### [1] Download (Work Codes)
Enter one or more work codes (e.g. `RJ123456 VJ01002074`). The app fetches metadata, presents the full file tree, and lets you select specific files by number or range (e.g. `1 3-5 7`). Leave blank to download everything.

#### [2] Batch Download from File
Enter a path to a `.txt` file with one work code (RJ or VJ) per line. All codes are validated, checked against your library, and queued.

```
# Example batch file (my_list.txt)
RJ01234567
VJ01002074
RJ00112233
```

#### [3] Search ASMR.ONE Online
Opens a search sub-menu with dedicated modes:
```
[1] General Keyword / Title Search
[2] Tag Search (e.g., 耳かき 睡眠 膝枕)
[3] Voice Actor / CV Search (e.g., 本渡楓)
[4] Circle Search
[5] Custom Syntax Filter ($tagw:, $rate:, $duration:, etc.)
[B] Back to Main Menu
```
Results display in a numbered table with title, circle, CV, tags (in your configured language), and rating. Enter numbers to queue immediately.

#### [4] Library Browser
Search your local download history by title or circle name. Shows the local folder path and file size.

#### [5] Queue Manager
View all items currently in the queue (pending / active / error status). Add new codes, change priority, or remove items.

#### [6] Settings
Edit all configuration options interactively, including:
- Download directory, proxy, mirror
- Concurrent downloads, bandwidth limit
- **Audio Language Priority** — preferred language for audio editions
- **Tag Language Priority** — language for tag display (`ja-jp`, `en-us`, `zh-cn`)
- Format priority list editor

#### [7] Statistics Dashboard
Overview of your library: total works, total size on disk, queue length, average work size.

#### [8] System Utilities
- **Cache Cleaner** — scans `.tmp` files, shows summary before deleting.
- **Network Diagnostics** — tests all API mirrors with latency.
- **Mirror Selector** — re-run speed test and update active mirror.

---

## 🔧 Usage — CLI Flags

```
usage: ./asmr [-h] [-b FILE] [-a] [--list] [--export FILE] [--test]
              [--dry-run] [--resume] [--no-update-check] [--verbose]
              [--search QUERY] [--tag TAGS] [--va NAME] [--circle NAME] [-v]
              [rj_codes ...]
```

| Flag | Short | Description |
|------|-------|-------------|
| `work_codes` | — | One or more work codes (RJ or VJ) to queue and download immediately |
| `--batch FILE` | `-b` | Path to a `.txt` file containing work codes, one per line |
| `--all` | `-a` | Skip the file-selection prompt; download all tracks |
| `--list` | — | Print the full track tree for each work code and exit |
| `--export FILE` | — | Export the library to CSV or JSON (e.g. `library.csv`) |
| `--test` | — | Test all API mirrors and display latency information |
| `--dry-run` | — | Show which files would be downloaded and total size; write nothing |
| `--resume` | — | Skip mirror test and update check; process existing queue immediately |
| `--no-update-check` | — | Skip the GitHub update check this session |
| `--verbose` | — | Write DEBUG-level logs to `singularity.log` |
| `--search QUERY` | — | Search ASMR.ONE online and display interactive results |
| `--tag TAGS` | `-t` | Tag search using official website syntax (space-separated tags) |
| `--va NAME` | — | Search by Voice Actor / CV name |
| `--circle NAME` | — | Search by Circle name |
| `--version` | `-v` | Print version and exit |
| `--help` | `-h` | Show usage summary |

### CLI Examples

```bash
# Download a single work
./asmr RJ01234567
./asmr VJ01002074

# Download multiple works, skip file selection
./asmr --all RJ01234567 VJ01002074

# Preview the file tree without downloading
./asmr --list RJ01234567

# Simulate a download (shows size, writes nothing)
./asmr --dry-run VJ01002074

# Search by keyword
./asmr --search "sleeping ASMR"

# Search by tag using official website syntax
./asmr --tag "耳かき 睡眠"

# Search by Voice Actor
./asmr --va "本渡楓"

# Search by Circle
./asmr --circle "ろまあぽ"

# Run a batch of codes from a file
./asmr --batch my_list.txt

# Batch download everything in the file without prompts
./asmr --batch my_list.txt --all

# Resume an interrupted session
./asmr --resume

# Debug a failed download
./asmr --verbose RJ01234567
# Then check singularity.log
```

---

## ⚙️ Configuration

`config.json` is created automatically on first launch. Edit it directly or through **[6] Settings** in the interactive menu.

```json
{
    "output_dir": "Downloads",
    "max_concurrent": 3,
    "proxy": null,
    "mirror": "https://api.asmr-200.com",
    "tag_audio": true,
    "sort_files": false,
    "dir_template": "{rj_id} {title}",
    "timeout": 60,
    "dns": "1.1.1.1",
    "bandwidth_limit_mbps": 0.0,
    "create_playlist": true,
    "audio_language_priority": ["ja-jp", "en-us", "zh-cn"],
    "tag_language_priority": ["en-us"],
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
| 🏷️ `dir_template` | `"{rj_id} {title}"` | Folder name template |
| ⏱️ `timeout` | `60` | HTTP request timeout in seconds |
| 🛡️ `dns` | `"1.1.1.1"` | DNS server — use `1.1.1.1` or `8.8.8.8` to bypass ISP blocks |
| 📶 `bandwidth_limit_mbps` | `0.0` | Speed cap in MB/s — `0` = unlimited |
| 🎵 `create_playlist` | `true` | Generate `.m3u8` playlist file after download |
| 🌍 `audio_language_priority` | `["ja-jp","en-us","zh-cn"]` | Preferred language for audio editions |
| 🏷️ `tag_language_priority` | `["en-us"]` | Language to display tags in search results |
| 🎚️ `format_priority` | `["flac","wav","mp3",…]` | Preferred format when a track has multiple versions |
| 🕐 `last_update_check` | `0.0` | Auto-managed — skips GitHub check if run within 24 h |

### `dir_template` Examples

| Template | Result folder name |
|----------|--------------------|
| `"{rj_id} {title}"` | `RJ01234567 Some Work Title` |
| `"{circle} - {title}"` | `SomeCircle - Some Work Title` |
| `"{year}/{circle}/{title}"` | `2024/SomeCircle/Some Work Title` |

### Language Priority Values

| Value | Language |
|-------|----------|
| `ja-jp` | Japanese |
| `en-us` | English |
| `zh-cn` | Chinese (Simplified) |

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
    ├── app.py           # UI, menus, job execution, search
    ├── orchestrator.py  # Download logic, retry, stats
    ├── network.py       # HTTP client, mirror management
    ├── db.py            # All database operations
    ├── config.py        # Config loading and validation
    ├── models.py        # Data types (WorkMetadata, TrackItem, etc.)
    ├── audio.py         # Audio metadata tagging
    └── constants.py     # Mirrors, log setup, shared constants, tag localization
```

---

## 🔍 Troubleshooting

### "All API mirrors are unreachable" or Connection Errors
**ASMR.ONE is actively region-blocked outside of East Asia (Japan, China, etc.).**
If the startup mirror test fails, your connection is being blocked. Use **Cloudflare WARP**:

1. Download from [https://one.one.one.one/](https://one.one.one.one/)
2. Open WARP settings → choose **Traffic and DNS (UDP)**
3. Turn on the connection and restart the downloader.

Or set the `proxy` field in `config.json` (e.g. `"http://user:pass@ip:port"`).

### Downloads hang or time out repeatedly
- Increase `timeout` in `config.json` (e.g. `120`)
- Reduce `max_concurrent` to `1` or `2`
- Try a different DNS or enable a proxy

### Tags appear in the wrong language
Set `tag_language_priority` in `config.json` to your preferred language:
```json
"tag_language_priority": ["en-us"]          // English only
"tag_language_priority": ["ja-jp", "en-us"] // Japanese, fallback to English
```

### Progress bar starts at wrong percentage on resume
This is a known visual issue. The download is still resuming correctly from the correct byte offset — the visual corrects itself as data flows in.

### `singularity.log` is too noisy
By default, only `INFO`, `WARNING`, and `ERROR` messages are logged. The `--verbose` flag adds `DEBUG` output (every HTTP request, byte offsets, retry attempts). Only use `--verbose` when actively debugging.

### "Fatal error" on startup with a cryptic message
Check `singularity.log` in the project root for the full traceback.

### Files are not being tagged after download
Ensure `tag_audio` is `true` in `config.json`. Tagging applies to MP3, FLAC, and OGG files only. WAV files are not tagged (no standard metadata container).

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

*Created by [Takoyune](https://github.com/takoyune)*
