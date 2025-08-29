# ASMR.one Downloader

A Python script to download ASMR content from [asmr.one](https://asmr.one) with a user-friendly interface, progress bars, retry logic, and file verification. Supports downloading by RJ ID, searching by keywords, and selecting specific file types (audio, image, text).

## Features
- **Download by RJ ID**: Fetch and download ASMR files using RJ codes (e.g., `RJ01330575`).
- **Search Mode**: Search for ASMR works by keywords and download up to a specified limit.
- **File Type Selection**: Choose specific file types (audio, image, text) or high-quality audio (FLAC/WAV/MP3).
- **Progress Bars**: Real-time download progress with speed display using `tqdm`.
- **Retry Logic**: Automatically retries failed downloads up to 3 times.
- **File Verification**: Checks if files exist on disk (no size check for faster verification).
- **Pause/Resume**: Pause downloads with `p` and resume with `r`.
- **Logging**: Saves download logs to `download_log.txt` for debugging.
- **Configurable**: Customize output directory and default file types via `config.json`.
- **Windows Support**: Includes a batch file (`asmr.bat`) for easy execution on Windows.

## Prerequisites
- **Python 3.12.3** or later (check with `python --version`).
- **Git** (for cloning the repo, check with `git --version`).
- Windows system (tested on Windows 10/11).

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/takoyune/asmr.one-downloader.git
   cd asmr.one-downloader
   ```

2. **Install Dependencies**:
   Install required Python packages:
   ```bash
   pip install aiohttp aiofiles tqdm keyboard
   ```

3. **Verify Dependencies**:
   Check installed packages:
   ```bash
   pip show aiohttp aiofiles tqdm keyboard
   ```
   Expected versions (or newer):
   - `aiohttp`: ~3.10.5
   - `aiofiles`: ~23.2.1
   - `tqdm`: ~4.66.5
   - `keyboard`: ~0.13.5

4. **Prepare Config File**:
   A default `config.json` is included:
   ```json
   {
     "output_dir": "C:\\ASMR",
     "default_file_types": ["audio", "image", "text"],
     "hq_audio_only": false
   }
   ```
   - Update `output_dir` to your preferred download folder.
   - Modify `default_file_types` if needed (e.g., `["audio"]` for audio only).

## Usage
### Option 1: Using the Batch File (Windows)
1. Ensure `asmr.bat`, `asmr.py`, and `config.json` are in the same directory (e.g., `C:\ASMR`).
2. Run the batch file with RJ IDs:
   ```cmd
   asmr.bat RJ01330575
   ```
3. Follow the interactive prompts to:
   - Change the output directory (optional).
   - Select files to download (all, specific types, or by index).
   - Monitor progress with `tqdm` bars.
   - Pause (`p`) or resume (`r`) downloads.

### Option 2: Using Python Directly
1. Navigate to the project directory:
   ```cmd
   cd C:\ASMR
   ```
2. Run with RJ IDs:
   ```cmd
   python asmr.py RJ01330575
   ```
3. For search mode:
   ```cmd
   python asmr.py -s "whisper" 10
   ```
   - `"whisper"`: Search query.
   - `10`: Limit to 10 RJ IDs.

4. For help:
   ```cmd
   python asmr.py -h
   ```

### Example Output
For `RJ01330575` with 10 files:
```
Current output directory: C:\ASMR
Change output directory? (y/n): n
=== Processing RJ01330575 ===
Fetching metadata...
Title: [Title of RJ01330575]
Fetching tracks...
Found 10 files.
Available files (checked against local metadata):
A. RJ01330575
   1. 05_トラック5：問題児とラブホテル.wav (audio, 521.30 MB, Not downloaded)
   2. 07_トラック7：こ〇も彼女と子作りえっち.wav (audio, 396.84 MB, Not downloaded)
   ...
Options:
1. Download all remaining/incomplete files
2. Download default file types from config (audio, image, text)
3. Select by file type (audio, image, text)
4. Select specific files by index
5. Download only high-quality audio (FLAC/WAV/MP3)
Enter your choice (1-5): 1
Selected 10 files to download (Total: 1206.05 MB):
- 05_トラック5：問題児とラブホテル.wav (audio, 521.30 MB)
...
Starting download for 10 files (Attempt 1/3, Press 'p' to pause, 'r' to resume):
File 1: 05_トラック5：問題児とラブホテル.wav... 100%|██████████ | 521M/521M [05:00<00:00, 1.80MB/s]
Summary for RJ01330575:
- Files selected: 10
- Files downloaded (verified on disk): 10
- Total size: 1206.05 MB
- Time taken: 300.00 seconds
- Average speed: 4.02 MB/s
```

## Troubleshooting
- **Download Fails (HTTP 403/416)**:
  - Check `download_log.txt` for errors like `HTTP 416, Requested Range Not Satisfiable`.
  - Test the API in a browser: `https://api.asmr-200.com/api/tracks/01330575?v=2`.
  - Ensure a stable internet connection (`ping api.asmr-200.com`).
- **Missing Dependencies**:
  - Reinstall: `pip install --force-reinstall aiohttp aiofiles tqdm keyboard`.
  - Update `pip`: `python -m pip install --upgrade pip`.
- **Files Not Downloading**:
  - Verify `config.json` has a valid `output_dir`.
  - Check if files exist but are empty (0 bytes) in the output directory.
- **Pause/Resume Not Working**:
  - Ensure the `keyboard` module is installed and has admin privileges (run CMD as administrator).

## Notes
- This tool uses the `asmr-200.com` API, which may require a stable internet connection. Some regions may need a proxy for `asmr-100.com` (not implemented in this version).
- Files are verified by existence on disk, not size, for faster checks. Be aware this might miss corrupted files.
- Respect [asmr.one](https://asmr.one)'s terms of service. This tool is for personal use only.
- Thanks to [asmr.one](https://asmr.one) for providing the API.[](https://github.com/thiliapr/asmr-one-downloader)

## Contributing
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`.
3. Commit changes: `git commit -m "Add feature-name"`.
4. Push to the branch: `git push origin feature-name`.
5. Open a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
