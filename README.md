# 🎧 ASMR.one Downloader

A powerful and user-friendly **Python downloader** for [asmr.one](https://asmr.one).
Supports searching, selecting, and downloading ASMR works with **progress bars, retry logic, pause/resume, and file verification**.

---

## ✨ Features

* 🔑 **Download by RJ ID** — e.g., `RJ01330575`.
* 🔍 **Search mode** — search by keyword and limit results.
* 🎚️ **File selection** — choose by type (audio, image, text) or high-quality audio only (FLAC/WAV/MP3).
* 📊 **Progress bars** — real-time with speed display (via `tqdm`).
* 🔄 **Auto retry** — failed downloads retried up to 3 times.
* ✅ **File verification** — skips already-downloaded files (existence check).
* ⏯️ **Pause/Resume** — press `p` to pause, `r` to resume.
* 📝 **Logging** — errors & activity saved in `download_log.txt`.
* ⚙️ **Configurable** — change defaults via `config.json`.
* 💻 **Windows-friendly** — includes a `asmr.bat` for one-click usage.

---

## 📦 Requirements

* **Python 3.12.3+**
* **Git** (for cloning)
* **Windows 10/11** (tested)
  *(Linux/Mac may work with minor tweaks)*

---

## 🚀 Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/takoyune/asmr.one-downloader.git
   cd asmr.one-downloader
   ```

2. **Install dependencies**

   ```bash
   pip install aiohttp aiofiles tqdm keyboard
   ```

3. **Verify installation**

   ```bash
   pip show aiohttp aiofiles tqdm keyboard
   ```

   Recommended versions (or newer):

   * aiohttp `~3.10.5`
   * aiofiles `~23.2.1`
   * tqdm `~4.66.5`
   * keyboard `~0.13.5`

4. **Edit config (optional)**

   ```json
   {
     "output_dir": "C:\\ASMR",
     "default_file_types": ["audio", "image", "text"],
     "hq_audio_only": false
   }
   ```

---

## 🛠️ Usage

### 1️⃣ Run via Batch File (Windows)

Make sure `asmr.bat`, `asmr.py`, and `config.json` are in the same folder.
Example:

```cmd
asmr.bat RJ01330575
```

### 2️⃣ Run via Python

Navigate to the folder and run:

```cmd
python asmr.py RJ01330575
```

🔎 **Search Mode**

```cmd
python asmr.py -s "whisper" 10
```

* `"whisper"` = keyword
* `10` = number of results

📖 **Help**

```cmd
python asmr.py -h
```

---

## 📊 Example Output

```
Current output directory: C:\ASMR
Change output directory? (y/n): n
=== Processing RJ01330575 ===
Fetching metadata...
Title: [Title of RJ01330575]
Fetching tracks...
Found 10 files.
Available files:
  1. 05_トラック5：問題児とラブホテル.wav (audio, 521.30 MB, Not downloaded)
  2. 07_トラック7：こ〇も彼女と子作りえっち.wav (audio, 396.84 MB, Not downloaded)
Options:
1. Download all remaining/incomplete files
2. Download default file types from config
3. Select by file type (audio, image, text)
4. Select specific files by index
5. Download only high-quality audio
Enter your choice (1-5): 1
Starting download for 10 files...
File 1: 05_トラック5：問題児とラブホテル.wav... 100%|██████████ | 521M/521M [05:00<00:00, 1.80MB/s]
Summary:
- Files downloaded: 10
- Total size: 1206.05 MB
- Time taken: 300.00 seconds
- Avg speed: 4.02 MB/s
```

---

## 🐞 Troubleshooting

* **Download fails (403/416)**

  * Check `download_log.txt` for details.
  * Test API: `https://api.asmr-200.com/api/tracks/01330575?v=2`.
  * Ensure stable internet (try `ping api.asmr-200.com`).

* **Dependencies missing**

  ```bash
  pip install --force-reinstall aiohttp aiofiles tqdm keyboard
  python -m pip install --upgrade pip
  ```

* **Files not downloading**

  * Verify `config.json` has correct `output_dir`.
  * Check if existing files are 0 bytes.

* **Pause/Resume not working**

  * Run CMD as Administrator (required by `keyboard` module).

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

## 📄 License

This project is licensed under the **MIT License**.
See the [LICENSE](LICENSE) file for details.
