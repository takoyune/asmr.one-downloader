# ASMR.ONE Downloader

A powerful and user-friendly **Python downloader** for [asmr.one](https://asmr.one).
Supports searching, selecting, and downloading ASMR works with **progress bars, retry logic, pause/resume, and file verification**.

---

## ✨ Features

🎨 **Visual & UI**

- **Rich Terminal UI:** Beautiful panels, tables, and live progress bars (powered by rich).

- **Single-Line Progress:** Clean, non-cluttered downloading experience.

- **Interactive Menu:** Easy-to-use menu system for selecting modes and settings.

🛠️ **Core Functionality**

- 🎵 **Auto-Tagging:** Automatically embeds Cover Art, Title, Artist, and Album metadata into .mp3 and .flac files.

- 📂 **Smart File Selector:** Choose to download All Files, Audio Only, or Manually Select specific tracks.

- 💾 **History Database:** Keeps track of downloaded works (RJ Codes) in a local history.db to prevent duplicates.

- ⏯️ **Smart Resume:** Resumes interrupted downloads exactly where they left off.

- 🛡️ **Connection Fixes:** Built-in Proxy/VPN support to handle ISP blocks and connection errors.

---

## 📦 Requirements

* **Python 3.12.3+**
* **Git** (for cloning)
* **Windows 10/11** (tested)
  *(Linux/Mac may work with minor tweaks)*

### Python Dependencies
```bash
pip install rich mutagen aiohttp aiofiles keyboard
````

> ⚠️ `keyboard` is optional.
> If not installed, hotkeys (P / R) will be disabled automatically.

---

## 🚀 Installation

```bash
git clone https://github.com/takoyune/asmr.one-downloader
cd asmr.one-downloader
pip install -r requirements.txt
```

Or install manually:

```bash
pip install rich mutagen aiohttp aiofiles keyboard
```

---

## ▶️ Usage

### 1️⃣ Run easy way

Make sure `asmr.bat`, `asmr.py`, and `config.json` are in the same folder.
Example:

```cmd
asmr
```

### 2️⃣ Run via Python

Navigate to the folder and run:

```cmd
python asmr.py
```

🔎 **Search Mode**

```cmd
asmr -s "whisper" 10
```

* `"whisper"` = keyword
* `10` = number of results

📖 **Help**

```cmd
python asmr.py -h
```

----

### Main Menu

```
┌─────────────────────────┐
│ ASMR.ONE Downloader     │
└─────────────────────────┘

[1] Download via RJ Code
[2] Search & Download
[3] Settings (Set Proxy)
[q] Quit

Select Option:
```
1️⃣ **Download via RJ Code**

 * Enter one or multiple codes (e.g., ```RJ012345``` ```999999```).

 * The tool will fetch metadata and cover art automatically.

2️⃣ **Search Mode**

 * Type a keyword (e.g., "Whisper", "Ear Cleaning").

 * Select the work you want from the results table.

3️⃣ **Settings (Proxy Fix)**

 * Connection Error? If your ISP blocks the site, go here.

 * Set a proxy URL (e.g., ```http://127.0.0.1:7890```) or change the download folder.

---

## 📥 Download Options

When a work is detected, you can choose:

1. **Download ALL files**
2. **Audio only** (`.mp3`, `.wav`, `.flac`)
3. **Manual selection** (by index or range)

Example:

```
1 3 5
1-6
```

---

## ⌨️ Hotkeys (During Download)

| Key | Action          |
| --- | --------------- |
| `P` | Pause download  |
| `R` | Resume download |

---


## 🌐 Proxy Support (IMPORTANT)

If your ISP blocks access:

1. Go to **Settings**
2. Set proxy, for example:

```
http://127.0.0.1:7890
```

Leave empty to disable proxy.

---

## 📁 Configuration File

`config.json` is created automatically.

Example:

```json
{
  "output_dir": "D:/ASMR",
  "max_concurrent": 3,
  "proxy": "",
  "tag_audio": true
}
```

---

## 🗄️ Download History

All downloaded works are saved in:

```
history.db
```

Prevents accidental re-downloads.

---

## 🧠 Technical Details

* Async downloads via **aiohttp**
* Progress UI powered by **Rich**
* Audio metadata handled by **Mutagen**
* Resume support via HTTP `Range`
* SQLite database for history tracking

---

## ⚠️ Disclaimer

This tool is for **educational and personal use only**.
Please support content creators by purchasing official releases.

---

## 📌 Notes

* Uses the `asmr-200.com` API (may require VPN/proxy in some regions).
* File check is **existence-only** (size not verified).
* For personal use only — respect [asmr.one](https://asmr.one)’s ToS.

---

## 🤝 Contributing

1. Fork this repo.
2. Create a branch: `git checkout -b feature-name`.
3. Commit changes: `git commit -m "Add feature-name"`.
4. Push branch: `git push origin feature-name`.
5. Open a Pull Request.

---

## 👤 Author

**[Takoyune](https://github.com/takoyune)**

## 📄 License

This project is licensed under the **MIT License**.
See the [LICENSE](LICENSE) file for details.
