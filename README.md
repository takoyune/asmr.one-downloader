# 🎙️ ASMR.ONE DOWNLOADER

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Aesthetics: Premium](https://img.shields.io/badge/Aesthetics-Premium-magenta.svg)](#)

A high-performance, asynchronous CLI tool designed for downloading and organizing content from ASMR.ONE. Built with a focus on speed, management, and a premium terminal experience.

---

## ✨ Key Features

*   **⚡ Ultra-Fast Asynchronous Downloads**: Powered by `asyncio` and `aiohttp` for high-concurrency file transfers.
*   **📊 Dynamic Progress Visualization**: Real-time tracking of individual files with a sleek, multi-bar progress interface.
*   **📂 Batch Processing**: Queuing multiple RJ codes via the terminal or by loading a list from a local `.txt` file.
*   **🎵 Intelligent Metadata Tagging**: Automatically applies high-quality metadata (Title, Artist, Album, Cover Art) to MP3, FLAC, and OGG files using `mutagen`.
*   **📚 Library Vault**: Persistent download history and local path management using a built-in SQLite database.
*   **🛡️ System Utilities**: Integrated tools for cache cleaning, database repair, and network diagnostics.
*   **🎨 Cyberpunk UI**: A beautiful, color-coded terminal interface powered by the `rich` library.

---

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.8 or higher.
*   (Recommended) A terminal that supports ANSI colors (like Windows Terminal, VS Code, or iTerm2).

### 2. Installation
The easiest way to set up the environment is to use the provided setup script:

```bash
# Run the setup script to create a virtual environment and install dependencies
./setup.bat
```

Alternatively, manual installation:
```bash
pip install -r requirements.txt
```

### 3. Running the App
Launch the downloader using the batch file or by running the script directly:

```bash
./asmr.bat
# OR
python main.py
```

---

## 🛠️ Usage

1.  **Main Menu**: Navigate using numeric keys (1-6).
2.  **Download**: Enter RJ codes (e.g., `RJ123456`) separated by spaces.
3.  **Batch Load**: Select option `[2]` and point the app to a `.txt` file containing your list of codes.
4.  **Utilities**: Use option `[6]` to clear cache or run system diagnostics.

---

## 💻 Tech Stack

*   **Language**: Python 3.10+
*   **Networking**: `aiohttp`, `aiofiles`
*   **UI/UX**: `rich`
*   **Metadata**: `mutagen`
*   **Storage**: `sqlite3`

---

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

*Created with ❤️ by Takoyune*
