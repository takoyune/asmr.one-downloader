<div align="center">
  <h1>🎙️ ASMR.ONE 下載器</h1>
  <p><strong>一個基於終端的 <a href="https://asmr.one">ASMR.ONE</a> 非同步下載器 — 持久化、支援斷點續傳、頻寬限速且完全支援腳本化。</strong></p>

  ![Version](https://img.shields.io/badge/version-1.3.22072026-blueviolet.svg?style=for-the-badge)
  ![Python](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
  ![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)
  ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg?style=for-the-badge)
</div>

<p align="center">
  <a href="README.md">English</a> •
  <a href="README_ja.md">日本語</a> •
  <a href="README_zh-CN.md">简体中文</a> •
  <a href="README_zh-TW.md">繁體中文</a> •
  <a href="README_ko.md">한국어</a>
</p>

---

## 📋 目錄

<div align="center">

| | | |
|:---:|:---:|:---:|
| [✨ 特性](#-特性) | [📦 需求](#-需求) | [🚀 安裝](#-安裝) |
| [▶️ 執行程式](#️-執行程式) | [🖥️ 互動式選單](#️-使用--互動式選單) | [🔧 CLI參數](#-使用--cli參數) |
| [⚙️ 設定](#️-設定) | [📁 專案結構](#-專案結構) | [🔍 疑難排解](#-疑難排解) |

</div>

---

## 🆕 v1.3.22072026 更新說明 (搜尋與語言全面大改)

一次重大的體驗升級，專注於更智慧的線上搜尋、與官方網站一致的標籤過濾以及完整的多語言標籤/音訊語言設定。

### 🔍 線上搜尋 — 全面重構
- **互動式搜尋子選單** — 選項 `[3] Search ASMR.ONE Online` 不再是單一的搜尋框，而是開啟一個專用的子選單：
  ```
  [1] 通用關鍵字 / 標題搜尋
  [2] 標籤搜尋 (例如：耳かき 睡眠 膝枕)
  [3] 聲優 / CV 搜尋 (例如：本渡楓)
  [4] 社團搜尋
  [5] 自訂語法過濾 ($tagw:, $rate:, $duration:)
  [B] 返回主選單
  ```
- **結果表格新增標籤列** — 搜尋結果現在包含一個 **標籤** 列，您可以立即查看每部作品包含的內容。

### 🏷️ 官方網站標籤語法
- 標籤搜尋現在使用與 ASMR.ONE 網站完全相同的過濾格式： **`$tagw:TAG$`**
- 支援透過空格分隔的多個標籤 (例如：`耳かき 睡眠` → `$tagw:耳かき$ $tagw:睡眠$`)
- 也可用作 CLI 參數： `./asmr --tag "耳かき 睡眠"`

### 🌐 雙語言優先順序設定
現在可以在 `config.json` 和 **Settings** (設定) 選單中使用兩個獨立的語言優先順序列表：

| 設定 | 用途 |
|---------|---------|
| `audio_language_priority` | 作品的首選音訊/語音語言版本 (例如：日語，英語，中文) |
| `tag_language_priority` | 在搜尋結果和檔案中繼資料中顯示標籤的語言 |

兩者都支援 `ja-jp`、`en-us` 和 `zh-cn` 的任意順序組合，具有後備鏈功能。例如：
```json
"audio_language_priority": ["ja-jp", "en-us", "zh-cn"],
"tag_language_priority": ["en-us"]
```
這將優先下載日語版本的音訊並以英語顯示標籤。您可以隨時透過 `[6] Settings` 進行變更。

### ⌨️ 新增 CLI 參數
| 參數 | 說明 |
|------|-------------|
| `--search QUERY` | 線上搜尋 ASMR.ONE 並獲取互動式結果表格 |
| `--tag TAGS` | 使用官方 `$tagw:TAG$` 語法的標籤搜尋 |
| `--va NAME` | 按聲優 / CV 名稱搜尋 |
| `--circle NAME` | 按社團名稱搜尋 |

---

## 🔒 歷史重大更新

<details>
<summary><strong>v1.2.07072026 (庫與佇列穩定性)</strong></summary>

### 🗄️ 下載引擎
- 具有可配置並行數的 **非同步並行下載** (預設：3個並行檔案)
- 使用 HTTP `Range` 請求標頭的 **斷點續傳支援** — `.tmp` 檔案在會話之間保留
- 每個檔案的 **3次重試迴圈**，並記錄每次失敗原因 (HTTP 狀態碼，例外類型)
- 透過設定檔中的 `bandwidth_limit_mbps` 實現 **權杖桶頻寬限速**
- **啟動時鏡像測速** — 並行 ping 所有鏡像，自動選擇最快的一個

### 📚 庫與佇列
- 追蹤每次完成下載的 **SQLite 庫** (`history.db`)
- **重複檢測** — 自動跳過已擁有的作品
- **持久化佇列** — 即使中斷也能保留；使用 `--resume` 恢復
- **格式優先順序去重** — 當同一音軌同時存在 WAV 和 MP3 時，僅下載首選格式

### 🖥️ CLI 與 UI
- **`--list`** — 列印完整的資料夾/檔案樹而不下載
- **`--dry-run`** — 模擬下載並顯示檔案大小
- **`--all`** — 跳過檔案選擇提示
- **`--batch`** — 載入包含作品代碼 (RJ/VJ) 的 `.txt` 檔案
- **會話報告** — 成功/失敗/跳過計數、經過的時間、平均速度
- 佇列完成時的 **Windows 提示音**

### 🎵 中繼資料與整理
- 透過 `mutagen` 加上 **音訊標籤** — MP3/FLAC/OGG 的標題、藝術家、專輯、封面
- 使用 `{rj_id}`, `{title}`, `{circle}`, `{year}` 的 `dir_template` 進行 **靈活的資料夾命名**
- 將檔案整理到 `Audio/`, `Images/`, `Text/` 子目錄的 **可選檔案分類**

</details>

---

## ✨ 特性

### 下載引擎
- **非同步並行下載** (基於 `asyncio` + `aiohttp`)。並行數可配置 (預設：3個並行檔案)。
- **斷點續傳支援** — 下載使用 HTTP `Range` 請求標頭。保留 `.tmp` 檔案，並在重新啟動時擴展。
- 每個檔案的 **3次重試迴圈**。故障與原因會被記錄，並顯示在會話報告中。
- **權杖桶頻寬限速** — 設定 `bandwidth_limit_mbps` 全域限制下載速度。`0` = 無限制。
- **啟動時鏡像測速** — 並行 ping 所有配置的 API 鏡像，自動選擇最快的鏡像。

### 庫與佇列
- **SQLite 庫** (`history.db`) 追蹤每次完成的下載：作品代碼，標題，本地路徑，檔案大小，日期。
- **重複檢測** — 在加入佇列前跳過已擁有的作品。
- **持久化佇列** — 下載佇列存在於資料庫中。中斷的會話重啟後仍然有效。使用 `--resume` 繼續。
- **格式優先順序去重** — 當作品包含多個格式版本時，僅下載首選格式。

### 線上搜尋
- **關鍵字 / 標題搜尋** — 搜尋 ASMR.ONE 並獲取帶編號的互動式結果表格。
- **標籤搜尋** — 使用官方 ASMR.ONE 網站語法 (`$tagw:TAG$`)，支援多個標籤。
- **聲優與社團搜尋** — 透過 CLI 參數或互動式子選單進行專用過濾。
- **自訂語法過濾** — 完全支援 `$rate:`, `$duration:`, `$tagw:` 等 ASMR.ONE 查詢運算子。
- **搜尋結果的標籤列** — 以您配置的語言 (日語，英語或中文) 顯示。

### CLI 與 UI
- **`--search`** — 從命令列進行線上搜尋。
- **`--tag`** — 使用官方網站語法進行標籤過濾搜尋。
- **`--list`** — 列印完整的資料夾/檔案樹而不下載。
- **`--dry-run`** — 模擬下載；顯示檔案和總大小，不寫入任何內容。
- **`--all`** — 跳過檔案選擇提示；下載全部。
- **`--batch`** — 載入包含作品代碼的 `.txt` 檔案。
- **會話報告** — 每個作業完成後：成功/失敗/跳過計數、經過的時間、平均速度。
- **Windows 提示音** — 完整佇列結束時播放系統聲音。

### 中繼資料與多語言支援
- **音訊標籤** (`mutagen`) — 寫入 MP3、FLAC 和 OGG 的標題、藝術家、專輯和封面。
- **靈活的資料夾命名** — 使用 `{rj_id}`, `{title}`, `{circle}`, `{year}` 可配置的 `dir_template`。
- **可選檔案分類** — 啟用 `sort_files` 可分類為 `Audio/`, `Images/`, `Text/`。
- **雙語言優先順序配置** — 分別控制音訊版本和標籤顯示的語言。

---

## 📦 需求

- **Python 3.10 或更高版本** — [python.org](https://www.python.org/downloads/)
- 支援 ANSI 顏色的終端機：
  - Windows：**Windows Terminal** (推薦)、VS Code 終端機或 PowerShell 7+
  - macOS/Linux：任何現代終端機模擬器
- **Git** (用於複製) — [git-scm.com](https://git-scm.com/)

Python 套件 (透過 `setup.bat` 或 `pip install -r requirements.txt` 自動安裝)：

| 套件 | 用途 |
|---------|---------|
| `aiohttp` | 用於下載和 API 呼叫的非同步 HTTP 用戶端 |
| `aiofiles` | 寫入下載區塊的非同步檔案 I/O |
| `aiodns` | 自訂 DNS 解析器 (繞過 ISP 級封鎖) |
| `rich` | 終端 UI — 進度條，表格，面板，顏色 |
| `mutagen` | 音訊中繼資料標籤 (MP3, FLAC, OGG) |
| `pydantic` | 配置驗證和模式執行 |
| `requests` | 同步 GitHub 更新檢查 |
| `packaging` | 解析版本字串進行更新對比 |

---

## 🚀 安裝

### 第一步 — 複製存放庫

```bash
git clone https://github.com/takoyune/asmr.one-downloader.git
cd asmr.one-downloader
```

或直接從 GitHub 下載 ZIP 壓縮檔並解壓到您選擇的資料夾中。

### 第二步 — 安裝依賴

**選項 A: 自動化 (Windows)**

```bat
setup.bat
```

只執行一次 — 建立虛擬環境並安裝所有依賴。以後啟動 `./asmr` 將自動使用該 venv。

**選項 B: 手動 (Windows / Linux / macOS)**

```bash
# (可選但推薦) 建立一個虛擬環境
python -m venv venv

# 啟動它
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 第三步 — 驗證安裝

```bash
python main.py --version
```

---

## ▶️ 執行程式

### Windows

```powershell
./asmr              # 開啟互動式選單
./asmr RJ123456     # 直接下載
./asmr --help       # 所有可用的參數
```

> CMD 使用者: `asmr.bat` 用法相同。

### Linux / macOS

```bash
chmod +x asmr       # 複製後的一次性操作

./asmr              # 開啟互動式選單
./asmr RJ123456     # 直接下載
./asmr --list RJ123456      # 預覽檔案樹
./asmr --dry-run RJ123456   # 模擬下載
./asmr --help               # 所有可用的參數
```

---

## 🖥️ 使用 — 互動式選單

不帶任何參數啟動 `./asmr`：

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    ASMR.ONE DOWNLOADER                        ┃
┃                       by Takoyune                             ┃
┃               https://github.com/takoyune                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 📚 Library: 11 works ━┛

[1] Download (Work Codes) [下載 (作品代碼)]
[2] Batch Download from File [從檔案批次下載]
[3] Search ASMR.ONE Online [線上搜尋 ASMR.ONE]
[4] Library Browser [庫瀏覽器]
[5] Queue Manager [佇列管理器]
[6] Settings [設定]
[7] Statistics Dashboard [統計儀表板]
[8] System Utilities [系統實用工具]
[X] Exit [退出]
```

#### [1] Download (Work Codes)
輸入一個或多個作品代碼 (例如：`RJ123456 VJ01002074`)。程式獲取中繼資料，顯示完整的檔案樹，並讓您透過數字或範圍 (例如：`1 3-5 7`) 選擇特定檔案。留空則下載全部內容。

#### [2] Batch Download from File
輸入一個包含作品代碼 (RJ 或 VJ) 的 `.txt` 檔案的路徑，每行一個。所有代碼都將被驗證，與您的庫核對並進入佇列。

```
# 批次檔案範例 (my_list.txt)
RJ01234567
VJ01002074
RJ00112233
```

#### [3] Search ASMR.ONE Online
開啟具有專用模式的搜尋子選單：
```
[1] 通用關鍵字 / 標題搜尋
[2] 標籤搜尋 (例如：耳かき 睡眠 膝枕)
[3] 聲優 / CV 搜尋 (例如：本渡楓)
[4] 社團搜尋
[5] 自訂語法過濾 ($tagw:, $rate:, $duration:, 等等)
[B] 返回主選單
```
結果顯示在帶編號的表格中，包含標題、社團、CV、標籤（您配置的語言）和評分。輸入編號即可立即加入佇列。

#### [4] Library Browser
按標題或社團名稱搜尋您的本地下載歷史記錄。顯示本地資料夾路徑和檔案大小。

#### [5] Queue Manager
查看佇列中當前的所有項目 (待處理 / 活躍 / 錯誤狀態)。添加新代碼、變更優先順序或刪除項目。

#### [6] Settings
互動式編輯所有設定選項，包括：
- 下載目錄，代理，鏡像
- 並行下載數，頻寬限制
- **音訊語言優先順序** — 首選的音訊語言版本
- **標籤語言優先順序** — 標籤顯示的語言 (`ja-jp`, `en-us`, `zh-cn`)
- 格式優先順序列表編輯器

#### [7] Statistics Dashboard
您的庫的概覽：作品總數、磁碟總大小、佇列長度、平均作品大小。

#### [8] System Utilities
- **清理快取** — 掃描 `.tmp` 檔案，並在刪除前顯示摘要。
- **網路診斷** — 測試所有 API 鏡像並顯示延遲。
- **鏡像選擇器** — 重新執行速度測試並更新活動的鏡像。

---

## 🔧 使用 — CLI參數

```
usage: ./asmr [-h] [-b FILE] [-a] [--list] [--export FILE] [--test]
              [--dry-run] [--resume] [--no-update-check] [--verbose]
              [--search QUERY] [--tag TAGS] [--va NAME] [--circle NAME] [-v]
              [rj_codes ...]
```

| 參數 | 縮寫 | 說明 |
|------|-------|-------------|
| `work_codes` | — | 一個或多個要立即加入佇列和下載的作品代碼 (RJ 或 VJ) |
| `--batch FILE` | `-b` | 包含作品代碼的 `.txt` 檔案的路徑，每行一個 |
| `--all` | `-a` | 跳過檔案選擇提示；下載所有音軌 |
| `--list` | — | 列印每個作品代碼的完整音軌樹並退出 |
| `--export FILE` | — | 將庫匯出為 CSV 或 JSON (例如 `library.csv`) |
| `--test` | — | 測試所有 API 鏡像並顯示延遲資訊 |
| `--dry-run` | — | 顯示將要下載的檔案和總大小；不寫入任何內容 |
| `--resume` | — | 跳過鏡像測試和更新檢查；立即處理現有佇列 |
| `--no-update-check` | — | 在此會話中跳過 GitHub 更新檢查 |
| `--verbose` | — | 將 DEBUG 級別的日誌寫入 `singularity.log` |
| `--search QUERY` | — | 線上搜尋 ASMR.ONE 並顯示互動式結果 |
| `--tag TAGS` | `-t` | 使用官方網站語法的標籤搜尋 (空格分隔的標籤) |
| `--va NAME` | — | 按聲優 / CV 名稱搜尋 |
| `--circle NAME` | — | 按社團名稱搜尋 |
| `--version` | `-v` | 列印版本並退出 |
| `--help` | `-h` | 顯示使用摘要 |

### CLI 範例

```bash
# 下載單部作品
./asmr RJ01234567
./asmr VJ01002074

# 下載多部作品，跳過檔案選擇
./asmr --all RJ01234567 VJ01002074

# 在不下載的情況下預覽檔案樹
./asmr --list RJ01234567

# 模擬下載 (顯示大小，不寫入)
./asmr --dry-run VJ01002074

# 按關鍵字搜尋
./asmr --search "sleeping ASMR"

# 使用官方網站語法按標籤搜尋
./asmr --tag "耳かき 睡眠"

# 按聲優搜尋
./asmr --va "本渡楓"

# 按社團搜尋
./asmr --circle "ろまあぽ"

# 從檔案執行一批代碼
./asmr --batch my_list.txt

# 批次下載檔案中的所有內容，無提示
./asmr --batch my_list.txt --all

# 恢復中斷的會話
./asmr --resume

# 除錯失敗的下載
./asmr --verbose RJ01234567
# 然後檢查 singularity.log
```

---

## ⚙️ 設定

第一次啟動時自動建立 `config.json`。直接編輯它或透過互動式選單中的 **[6] Settings** 進行編輯。

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

| 鍵 | 預設值 | 說明 |
|-----|---------|-------------|
| 📁 `output_dir` | `"Downloads"` | 下載作品保存的位置 |
| ⚡ `max_concurrent` | `3` | 並行下載的檔案數 (1–20) |
| 🌐 `proxy` | `null` | HTTP 或 SOCKS5 代理 URL |
| 🔗 `mirror` | auto | API 鏡像 URL — 啟動時自動設定 |
| 🎵 `tag_audio` | `true` | 將中繼資料標籤寫入 MP3 / FLAC / OGG |
| 📂 `sort_files` | `false` | 整理到 `Audio/`, `Images/`, `Text/` 子資料夾 |
| 🏷️ `dir_template` | `"{rj_id} {title}"` | 資料夾名稱模板 |
| ⏱️ `timeout` | `60` | HTTP 請求超時 (秒) |
| 🛡️ `dns` | `"1.1.1.1"` | DNS 伺服器 — 使用 `1.1.1.1` 或 `8.8.8.8` 繞過 ISP 封鎖 |
| 📶 `bandwidth_limit_mbps` | `0.0` | 速度上限 (MB/s) — `0` = 無限制 |
| 🎵 `create_playlist` | `true` | 下載後生成 `.m3u8` 播放列表檔案 |
| 🌍 `audio_language_priority` | `["ja-jp","en-us","zh-cn"]` | 音訊版本的首選語言 |
| 🏷️ `tag_language_priority` | `["en-us"]` | 搜尋結果中顯示標籤的語言 |
| 🎚️ `format_priority` | `["flac","wav","mp3",…]` | 當某音軌有多個版本時的首選格式 |
| 🕐 `last_update_check` | `0.0` | 自動管理 — 若在24小時內執行則跳過 GitHub 檢查 |

### `dir_template` 範例

| 模板 | 結果資料夾名 |
|----------|--------------------|
| `"{rj_id} {title}"` | `RJ01234567 Some Work Title` |
| `"{circle} - {title}"` | `SomeCircle - Some Work Title` |
| `"{year}/{circle}/{title}"` | `2024/SomeCircle/Some Work Title` |

### 語言優先順序的值

| 值 | 語言 |
|-------|----------|
| `ja-jp` | 日語 |
| `en-us` | 英語 |
| `zh-cn` | 簡體中文 |

---

## 📁 專案結構

```
asmr.one-downloader/
│
├── main.py          # 進入點 — CLI 參數，啟動檢查，更新檢查
├── asmr             # Linux / macOS 啟動器 (執行: chmod +x asmr)
├── asmr.bat         # Windows CMD 啟動器
├── asmr.ps1         # Windows PowerShell 啟動器
├── setup.bat        # 首次設定 (建立 venv + 安裝依賴)
├── requirements.txt # Python 依賴
├── config.json      # 您的設定 (首次執行時自動建立)
├── history.db       # SQLite — 庫和下載佇列
├── singularity.log  # 循環日誌檔案
│
└── main/
    ├── app.py           # UI，選單，作業執行，搜尋
    ├── orchestrator.py  # 下載邏輯，重試，統計
    ├── network.py       # HTTP 用戶端，鏡像管理
    ├── db.py            # 所有資料庫操作
    ├── config.py        # 配置載入與驗證
    ├── models.py        # 資料類型 (WorkMetadata, TrackItem, 等等)
    ├── audio.py         # 音訊中繼資料標記
    └── constants.py     # 鏡像，日誌設定，共用常數，標籤在地化
```

---

## 🔍 疑難排解

### "All API mirrors are unreachable" (所有API鏡像不可達) 或 連線錯誤
**ASMR.ONE 在東亞 (日本，中國等) 之外被主動限制區域。**
如果啟動時的鏡像測試失敗，您的連線可能已被封鎖。請使用 **Cloudflare WARP**：

1. 從 [https://one.one.one.one/](https://one.one.one.one/) 下載
2. 開啟 WARP 設定 → 選擇 **Traffic and DNS (UDP)**
3. 開啟連線，然後重啟下載器。

或在 `config.json` 中設定 `proxy` 欄位 (例如：`"http://user:pass@ip:port"`)。

### 下載反覆掛起或超時
- 增加 `config.json` 中的 `timeout` (例如：`120`)
- 減少 `max_concurrent` 至 `1` 或 `2`
- 嘗試更換 DNS 或啟用代理

### 標籤顯示語言錯誤
將 `config.json` 中的 `tag_language_priority` 設定為您首選的語言：
```json
"tag_language_priority": ["en-us"]          // 僅英語
"tag_language_priority": ["ja-jp", "en-us"] // 日語，失敗則回退到英語
```

### 恢復下載時進度條百分比起點錯誤
這是一個已知的顯示問題。下載實際上是從正確的位元組偏移量正確恢復的 — 隨著資料的流入，顯示會自動修正。

### `singularity.log` 噪音太大
預設情況下，僅記錄 `INFO`, `WARNING` 和 `ERROR` 訊息。`--verbose` 參數會加入 `DEBUG` 輸出 (每個 HTTP 請求，位元組偏移量，重試嘗試次數)。僅在積極除錯時使用 `--verbose`。

### 啟動時出現含糊訊息的 "Fatal error" (致命錯誤)
請檢查專案根目錄中的 `singularity.log` 以獲取完整的追蹤日誌。

### 檔案下載後未被標記
確保 `config.json` 中的 `tag_audio` 為 `true`。標記僅適用於 MP3, FLAC 和 OGG 檔案。WAV 檔案不會被標記 (沒有標準的中繼資料容器)。

---

## 📝 授權條款

MIT 授權條款 — 詳見 [LICENSE](LICENSE)。

*由 [Takoyune](https://github.com/takoyune) 建立*
