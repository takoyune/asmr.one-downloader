<div align="center">
  <h1>🎙️ ASMR.ONE ダウンローダー</h1>
  <p><strong><a href="https://asmr.one">ASMR.ONE</a> 用の非同期ターミナルベースダウンローダー — 永続的、再開可能、帯域幅制限付き、フルスクリプト対応。</strong></p>

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

## 📋 目次

<div align="center">

| | | |
|:---:|:---:|:---:|
| [✨ 特徴](#-特徴) | [📦 要件](#-要件) | [🚀 インストール](#-インストール) |
| [▶️ アプリの実行](#️-アプリの実行) | [🖥️ インタラクティブメニュー](#️-使い方--インタラクティブメニュー) | [🔧 CLIフラグ](#-使い方--cliフラグ) |
| [⚙️ 設定](#️-設定) | [📁 プロジェクト構造](#-プロジェクト構造) | [🔍 トラブルシューティング](#-トラブルシューティング) |

</div>

---

## 🆕 v1.3.22072026 の新機能 (検索と言語の全面刷新)

スマートなオンライン検索、公式ウェブサイトを再現するタグフィルタリング、そして完全な多言語タグ/音声言語設定に焦点を当てた主要なQoL（Quality of Life）アップデートです。

### 🔍 オンライン検索 — 全面刷新
- **インタラクティブな検索サブメニュー** — 単一の検索ボックスではなく、オプション `[3] ASMR.ONE をオンラインで検索` が専用のサブメニューを開くようになりました。
  ```
  [1] 一般的なキーワード / タイトル検索
  [2] タグ検索 (例: 耳かき 睡眠 膝枕)
  [3] 声優 / CV検索 (例: 本渡楓)
  [4] サークル検索
  [5] カスタム構文フィルター ($tagw:, $rate:, $duration:)
  [B] メインメニューに戻る
  ```
- **検索結果テーブルのタグ列** — 検索結果に **タグ** 列が追加され、各作品の内容をすぐに確認できるようになりました。

### 🏷️ 公式ウェブサイトのタグ構文
- タグ検索で、ASMR.ONE ウェブサイトと全く同じフィルター形式を使用するようになりました： **`$tagw:TAG$`**
- スペース区切りで複数のタグをサポートしています (例: `耳かき 睡眠` → `$tagw:耳かき$ $tagw:睡眠$`)
- CLIフラグとしても利用可能です: `./asmr --tag "耳かき 睡眠"`

### 🌐 デュアル言語の優先設定
`config.json` と **設定** メニューに、2つの独立した言語優先リストが追加されました：

| 設定 | 目的 |
|---------|---------|
| `audio_language_priority` | 作品の優先する音声言語エディション (例: 日本語、英語、中国語) |
| `tag_language_priority` | 検索結果やファイルメタデータでタグを表示する言語 |

どちらも `ja-jp`、`en-us`、`zh-cn` を任意の順序でサポートしており、フォールバックチェーンが可能です。例:
```json
"audio_language_priority": ["ja-jp", "en-us", "zh-cn"],
"tag_language_priority": ["en-us"]
```
これにより、音声は日本語で、タグは英語で表示されます。`[6] 設定` からいつでも変更できます。

### ⌨️ 新しいCLIフラグ
| フラグ | 説明 |
|------|-------------|
| `--search QUERY` | ASMR.ONE をオンラインで検索し、インタラクティブな結果テーブルを取得します |
| `--tag TAGS` | 公式の `$tagw:TAG$` 構文を使用したタグ検索 |
| `--va NAME` | 声優 / CV名で検索 |
| `--circle NAME` | サークル名で検索 |

---

## 🔒 過去の主要なアップデート

<details>
<summary><strong>v1.2.07072026 (ライブラリとキューの安定性)</strong></summary>

### 🗄️ ダウンロードエンジン
- 設定可能な同時実行数による **非同期の同時ダウンロード** (デフォルト: 3ファイル並列)
- HTTP `Range` ヘッダーを使用した **再開サポート** — `.tmp` ファイルはセッション間で保持されます
- 各ファイルの失敗理由（HTTPステータス、例外タイプ）を記録する **3回の再試行ループ**
- 設定の `bandwidth_limit_mbps` を介した **トークンバケット帯域幅制限**
- **起動時のミラースピードテスト** — 全てのミラーに並行してpingを送信し、最速のものを自動的に選択します

### 📚 ライブラリとキュー
- 完了したすべてのダウンロードを記録する **SQLiteライブラリ** (`history.db`)
- **重複の検出** — 既に所有している作品は自動的にスキップされます
- **永続的なキュー** — 中断後も残ります; `--resume` で続行します
- **フォーマット優先順位の重複排除** — 同じトラックにWAVとMP3が存在する場合、優先されるフォーマットのみがダウンロードされます

### 🖥️ CLI と UI
- **`--list`** — ダウンロードせずに完全なフォルダ/ファイルツリーを表示します
- **`--dry-run`** — ダウンロードをシミュレートし、ファイルサイズを表示します
- **`--all`** — ファイル選択プロンプトをスキップします
- **`--batch`** — 作品コード (RJ/VJ) の `.txt` ファイルを読み込みます
- **セッションレポート** — 成功/失敗/スキップされた数、経過時間、平均速度
- キュー完了時の **Windows 完了ビープ音**

### 🎵 メタデータと整理
- `mutagen` を使用した **オーディオタグ付け** — MP3/FLAC/OGGのタイトル、アーティスト、アルバム、カバーアート
- `{rj_id}`, `{title}`, `{circle}`, `{year}` を使用した `dir_template` による **柔軟なフォルダ命名**
- `Audio/`, `Images/`, `Text/` サブディレクトリへの **オプションのファイル並べ替え**

</details>

---

## ✨ 特徴

### ダウンロードエンジン
- `asyncio` + `aiohttp` による **非同期の同時ダウンロード**。同時実行数は設定可能（デフォルト: 3ファイル並列）。
- **再開サポート** — HTTP `Range` ヘッダーを使用します。`.tmp` ファイルはセッション間で保持され、再開時に拡張されます。
- ファイルごとの **3回の再試行ループ**。失敗は理由とともに記録され、セッションレポートに表示されます。
- **トークンバケット帯域幅制限** — グローバルなダウンロード速度の上限を設定するには `bandwidth_limit_mbps` を設定します。`0` = 無制限。
- **起動時のミラースピードテスト** — 設定されたすべてのAPIミラーに並行してpingを送信し、最速のものを自動的に選択します。

### ライブラリとキュー
- **SQLiteライブラリ** (`history.db`) は完了したすべてのダウンロードを追跡します: 作品コード、タイトル、ローカルパス、ファイルサイズ、日付。
- **重複の検出** — 既に所有している作品は、キューに追加される前にスキップされます。
- **永続的なキュー** — ダウンロードキューはデータベース内に保存されます。中断されたセッションは再起動後も存続します。続行するには `--resume` を使用します。
- **フォーマット優先順位の重複排除** — 作品に複数のフォーマットバージョンが含まれている場合、優先されるフォーマットのみがダウンロードされます。

### オンライン検索
- **キーワード / タイトル検索** — ASMR.ONE を検索し、インタラクティブな番号付き結果テーブルを取得します。
- **タグ検索** — 公式ASMR.ONEウェブサイトの構文 (`$tagw:TAG$`) を使用し、複数のタグをサポートしています。
- **声優＆サークル検索** — CLIフラグまたはインタラクティブなサブメニューを介した専用のフィルター。
- **カスタム構文フィルター** — `$rate:`, `$duration:`, `$tagw:` およびその他の ASMR.ONE クエリ演算子を完全にサポート。
- **検索結果のタグ列** — 設定された言語（日本語、英語、または中国語）で表示されます。

### CLI と UI
- **`--search`** — コマンドラインからオンラインで検索します。
- **`--tag`** — 公式ウェブサイトの構文を使用したタグフィルター検索。
- **`--list`** — ダウンロードせずに完全なフォルダ/ファイルツリーを表示します。
- **`--dry-run`** — ダウンロードをシミュレートします; ファイルと合計サイズを表示し、何も書き込みません。
- **`--all`** — ファイル選択プロンプトをスキップし、すべてをダウンロードします。
- **`--batch`** — 作品コードの `.txt` ファイルを読み込みます。
- **セッションレポート** — 各ジョブの終了後: 成功/失敗/スキップされた数、経過時間、平均速度。
- **Windows 完了ビープ音** — 全てのキューが終了したときにシステムサウンドが鳴ります。

### メタデータと多言語対応
- **オーディオタグ付け** (`mutagen`) — タイトル、アーティスト、アルバム、カバーアートが MP3, FLAC, OGG に書き込まれます。
- **柔軟なフォルダ命名** — `{rj_id}`, `{title}`, `{circle}`, `{year}` を使用して設定可能な `dir_template`。
- **オプションのファイル並べ替え** — `sort_files` を有効にして `Audio/`, `Images/`, `Text/` に整理します。
- **デュアル言語優先設定** — 音声エディションとタグ表示の言語を個別に制御します。

---

## 📦 要件

- **Python 3.10 以上** — [python.org](https://www.python.org/downloads/)
- ANSIカラーをサポートするターミナル:
  - Windows: **Windows Terminal** (推奨)、VS Code ターミナル、または PowerShell 7+
  - macOS/Linux: モダンなターミナルエミュレーター
- **Git** (クローン用) — [git-scm.com](https://git-scm.com/)

Pythonパッケージ (`setup.bat` または `pip install -r requirements.txt` によって自動的にインストールされます):

| パッケージ | 目的 |
|---------|---------|
| `aiohttp` | ダウンロードとAPI呼び出しのための非同期HTTPクライアント |
| `aiofiles` | ダウンロードチャンクを書き込むための非同期ファイル I/O |
| `aiodns` | カスタム DNS リゾルバー (ISP レベルのブロックを回避) |
| `rich` | ターミナル UI — プログレスバー、テーブル、パネル、カラー |
| `mutagen` | オーディオメタデータタグ付け (MP3, FLAC, OGG) |
| `pydantic` | 設定の検証とスキーマの強制 |
| `requests` | 同期的な GitHub アップデートチェック |
| `packaging` | アップデート比較のためのバージョン文字列解析 |

---

## 🚀 インストール

### ステップ 1 — リポジトリをクローンする

```bash
git clone https://github.com/takoyune/asmr.one-downloader.git
cd asmr.one-downloader
```

または、GitHub から ZIP を直接ダウンロードし、任意のフォルダに解凍します。

### ステップ 2 — 依存関係をインストールする

**オプション A: 自動 (Windows)**

```bat
setup.bat
```

一度だけ実行します — 仮想環境を作成し、すべての依存関係をインストールします。以降の `./asmr` の起動では自動的にvenvが使用されます。

**オプション B: 手動 (Windows / Linux / macOS)**

```bash
# (オプションだが推奨) 仮想環境を作成する
python -m venv venv

# アクティブにする
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate

# 依存関係をインストールする
pip install -r requirements.txt
```

### ステップ 3 — インストールを確認する

```bash
python main.py --version
```

---

## ▶️ アプリの実行

### Windows

```powershell
./asmr              # インタラクティブメニューを開く
./asmr RJ123456     # 直接ダウンロードする
./asmr --help       # すべての利用可能なフラグ
```

> CMDユーザー: `asmr.bat` も同じように機能します。

### Linux / macOS

```bash
chmod +x asmr       # クローン後の一度だけのステップ

./asmr              # インタラクティブメニューを開く
./asmr RJ123456     # 直接ダウンロードする
./asmr --list RJ123456      # ファイルツリーをプレビューする
./asmr --dry-run RJ123456   # ダウンロードをシミュレートする
./asmr --help               # すべての利用可能なフラグ
```

---

## 🖥️ 使い方 — インタラクティブメニュー

引数なしで `./asmr` を起動します:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    ASMR.ONE DOWNLOADER                        ┃
┃                       by Takoyune                             ┃
┃               https://github.com/takoyune                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 📚 Library: 11 works ━┛

[1] Download (Work Codes) [作品コードでダウンロード]
[2] Batch Download from File [ファイルからの一括ダウンロード]
[3] Search ASMR.ONE Online [ASMR.ONE をオンラインで検索]
[4] Library Browser [ライブラリブラウザ]
[5] Queue Manager [キューマネージャー]
[6] Settings [設定]
[7] Statistics Dashboard [統計ダッシュボード]
[8] System Utilities [システムユーティリティ]
[X] Exit [終了]
```

#### [1] Download (Work Codes)
1つ以上の作品コードを入力します（例: `RJ123456 VJ01002074`）。アプリはメタデータを取得し、完全なファイルツリーを表示し、番号または範囲（例: `1 3-5 7`）で特定のファイルを選択できるようにします。空白のままにするとすべてがダウンロードされます。

#### [2] Batch Download from File
1行に1つの作品コード（RJまたはVJ）が含まれる `.txt` ファイルへのパスを入力します。すべてのコードが検証され、ライブラリと照合された後、キューに追加されます。

```
# バッチファイルの例 (my_list.txt)
RJ01234567
VJ01002074
RJ00112233
```

#### [3] Search ASMR.ONE Online
専用のモードを持つ検索サブメニューを開きます:
```
[1] 一般的なキーワード / タイトル検索
[2] タグ検索 (例: 耳かき 睡眠 膝枕)
[3] 声優 / CV検索 (例: 本渡楓)
[4] サークル検索
[5] カスタム構文フィルター ($tagw:, $rate:, $duration:, など)
[B] メインメニューに戻る
```
結果は、タイトル、サークル、CV、タグ（設定された言語）、および評価を含む番号付きのテーブルに表示されます。番号を入力するとすぐにキューに追加されます。

#### [4] Library Browser
ローカルのダウンロード履歴をタイトルまたはサークル名で検索します。ローカルフォルダのパスとファイルサイズを表示します。

#### [5] Queue Manager
現在キューにあるすべてのアイテム（保留 / アクティブ / エラーステータス）を表示します。新しいコードを追加したり、優先順位を変更したり、アイテムを削除したりできます。

#### [6] Settings
以下を含むすべての設定オプションを対話形式で編集します:
- ダウンロードディレクトリ、プロキシ、ミラー
- 同時ダウンロード数、帯域幅制限
- **Audio Language Priority** — 音声エディションの優先言語
- **Tag Language Priority** — タグ表示の言語 (`ja-jp`, `en-us`, `zh-cn`)
- フォーマット優先順位リストエディタ

#### [7] Statistics Dashboard
ライブラリの概要: 総作品数、ディスク上の総サイズ、キューの長さ、平均作品サイズ。

#### [8] System Utilities
- **Cache Cleaner** — `.tmp` ファイルをスキャンし、削除前にサマリーを表示します。
- **Network Diagnostics** — すべてのAPIミラーをレイテンシ付きでテストします。
- **Mirror Selector** — スピードテストを再実行し、アクティブなミラーを更新します。

---

## 🔧 使い方 — CLIフラグ

```
usage: ./asmr [-h] [-b FILE] [-a] [--list] [--export FILE] [--test]
              [--dry-run] [--resume] [--no-update-check] [--verbose]
              [--search QUERY] [--tag TAGS] [--va NAME] [--circle NAME] [-v]
              [rj_codes ...]
```

| フラグ | 短縮形 | 説明 |
|------|-------|-------------|
| `work_codes` | — | すぐにキューに入れてダウンロードするための1つ以上の作品コード (RJ または VJ) |
| `--batch FILE` | `-b` | 1行に1つの作品コードを含む `.txt` ファイルへのパス |
| `--all` | `-a` | ファイル選択プロンプトをスキップし、すべてのトラックをダウンロードします |
| `--list` | — | 各作品コードの完全なトラックツリーを出力して終了します |
| `--export FILE` | — | ライブラリを CSV または JSON にエクスポートします (例: `library.csv`) |
| `--test` | — | すべてのAPIミラーをテストし、レイテンシ情報を表示します |
| `--dry-run` | — | どのファイルがダウンロードされるか、および合計サイズを表示します。何も書き込みません |
| `--resume` | — | ミラーテストとアップデートチェックをスキップし、既存のキューをすぐに処理します |
| `--no-update-check` | — | このセッションでは GitHub アップデートチェックをスキップします |
| `--verbose` | — | `singularity.log` に DEBUG レベルのログを書き込みます |
| `--search QUERY` | — | ASMR.ONE をオンラインで検索し、インタラクティブな結果を表示します |
| `--tag TAGS` | `-t` | 公式ウェブサイト構文を使用したタグ検索 (スペース区切りのタグ) |
| `--va NAME` | — | 声優 / CV名で検索します |
| `--circle NAME` | — | サークル名で検索します |
| `--version` | `-v` | バージョンを出力して終了します |
| `--help` | `-h` | 使い方サマリーを表示します |

### CLI の例

```bash
# 1つの作品をダウンロードする
./asmr RJ01234567
./asmr VJ01002074

# 複数の作品をダウンロードし、ファイル選択をスキップする
./asmr --all RJ01234567 VJ01002074

# ダウンロードせずにファイルツリーをプレビューする
./asmr --list RJ01234567

# ダウンロードをシミュレートする (サイズを表示し、何も書き込まない)
./asmr --dry-run VJ01002074

# キーワードで検索する
./asmr --search "sleeping ASMR"

# 公式ウェブサイト構文を使用してタグで検索する
./asmr --tag "耳かき 睡眠"

# 声優で検索する
./asmr --va "本渡楓"

# サークルで検索する
./asmr --circle "ろまあぽ"

# ファイルからコードのバッチを実行する
./asmr --batch my_list.txt

# プロンプトなしでファイル内のすべてを一括ダウンロードする
./asmr --batch my_list.txt --all

# 中断されたセッションを再開する
./asmr --resume

# 失敗したダウンロードをデバッグする
./asmr --verbose RJ01234567
# その後、singularity.log を確認します
```

---

## ⚙️ 設定

`config.json` は初回起動時に自動的に作成されます。直接編集するか、インタラクティブメニューの **[6] Settings** から編集します。

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

| キー | デフォルト | 説明 |
|-----|---------|-------------|
| 📁 `output_dir` | `"Downloads"` | ダウンロードした作品が保存される場所 |
| ⚡ `max_concurrent` | `3` | 並行ファイルダウンロード数 (1–20) |
| 🌐 `proxy` | `null` | HTTP または SOCKS5 プロキシ URL |
| 🔗 `mirror` | auto | API ミラー URL — 起動時に自動的に設定されます |
| 🎵 `tag_audio` | `true` | メタデータタグを MP3 / FLAC / OGG に書き込みます |
| 📂 `sort_files` | `false` | `Audio/`, `Images/`, `Text/` サブフォルダに整理します |
| 🏷️ `dir_template` | `"{rj_id} {title}"` | フォルダ名のテンプレート |
| ⏱️ `timeout` | `60` | HTTP リクエストのタイムアウト（秒） |
| 🛡️ `dns` | `"1.1.1.1"` | DNS サーバー — ISP ブロックを回避するには `1.1.1.1` または `8.8.8.8` を使用します |
| 📶 `bandwidth_limit_mbps` | `0.0` | MB/s 単位の速度制限 — `0` = 無制限 |
| 🎵 `create_playlist` | `true` | ダウンロード後に `.m3u8` プレイリストファイルを生成します |
| 🌍 `audio_language_priority` | `["ja-jp","en-us","zh-cn"]` | 音声エディションの優先言語 |
| 🏷️ `tag_language_priority` | `["en-us"]` | 検索結果にタグを表示する言語 |
| 🎚️ `format_priority` | `["flac","wav","mp3",…]` | トラックに複数のバージョンがある場合の優先フォーマット |
| 🕐 `last_update_check` | `0.0` | 自動管理 — 24時間以内に実行された場合、GitHubチェックをスキップします |

### `dir_template` の例

| テンプレート | 結果のフォルダ名 |
|----------|--------------------|
| `"{rj_id} {title}"` | `RJ01234567 Some Work Title` |
| `"{circle} - {title}"` | `SomeCircle - Some Work Title` |
| `"{year}/{circle}/{title}"` | `2024/SomeCircle/Some Work Title` |

### 言語の優先順位の値

| 値 | 言語 |
|-------|----------|
| `ja-jp` | 日本語 |
| `en-us` | 英語 |
| `zh-cn` | 中国語 (簡体字) |

---

## 📁 プロジェクト構造

```
asmr.one-downloader/
│
├── main.py          # エントリポイント — CLIフラグ、事前チェック、アップデートチェック
├── asmr             # Linux / macOS ランチャー (実行: chmod +x asmr)
├── asmr.bat         # Windows CMD ランチャー
├── asmr.ps1         # Windows PowerShell ランチャー
├── setup.bat        # 初回セットアップ (venv 作成 + 依存関係インストール)
├── requirements.txt # Python 依存関係
├── config.json      # あなたの設定 (初回起動時に自動作成)
├── history.db       # SQLite — ライブラリとダウンロードキュー
├── singularity.log  # ローテーションされるログファイル
│
└── main/
    ├── app.py           # UI、メニュー、ジョブ実行、検索
    ├── orchestrator.py  # ダウンロードロジック、再試行、統計
    ├── network.py       # HTTP クライアント、ミラー管理
    ├── db.py            # すべてのデータベース操作
    ├── config.py        # 設定の読み込みと検証
    ├── models.py        # データ型 (WorkMetadata, TrackItem, など)
    ├── audio.py         # オーディオメタデータタグ付け
    └── constants.py     # ミラー、ログ設定、共有定数、タグのローカリゼーション
```

---

## 🔍 トラブルシューティング

### "All API mirrors are unreachable" (全てのAPIミラーに到達できません) または 接続エラー
**ASMR.ONE は東アジア (日本、中国など) 以外では積極的に地域ブロックされています。**
起動時のミラーテストが失敗した場合、接続がブロックされています。**Cloudflare WARP** を使用してください:

1. [https://one.one.one.one/](https://one.one.one.one/) からダウンロード
2. WARP 設定を開く → **Traffic and DNS (UDP)** を選択
3. 接続をオンにして、ダウンローダーを再起動します。

または、`config.json` の `proxy` フィールドを設定します (例: `"http://user:pass@ip:port"`)。

### ダウンロードが繰り返しハングする、またはタイムアウトする
- `config.json` の `timeout` を増やします (例: `120`)
- `max_concurrent` を `1` または `2` に減らします
- 別の DNS を試すか、プロキシを有効にします

### タグが間違った言語で表示される
`config.json` の `tag_language_priority` を好みの言語に設定します:
```json
"tag_language_priority": ["en-us"]          // 英語のみ
"tag_language_priority": ["ja-jp", "en-us"] // 日本語、フォールバックとして英語
```

### 再開時にプログレスバーが間違ったパーセンテージで開始される
これは既知の表示上の問題です。ダウンロードは正しいバイトオフセットから正しく再開されています — データが流れ込むと表示は自動的に修正されます。

### `singularity.log` がうるさすぎる
デフォルトでは、`INFO`, `WARNING`, および `ERROR` メッセージのみがログに記録されます。`--verbose` フラグを追加すると、`DEBUG` 出力 (すべてのHTTPリクエスト、バイトオフセット、再試行回数) が追加されます。積極的にデバッグする場合にのみ `--verbose` を使用してください。

### 起動時の不可解なメッセージによる "Fatal error" (致命的エラー)
プロジェクトルートにある `singularity.log` の完全なトレースバックを確認してください。

### ダウンロード後にファイルにタグ付けされない
`config.json` の `tag_audio` が `true` になっていることを確認してください。タグ付けは MP3, FLAC, OGG ファイルにのみ適用されます。WAV ファイルはタグ付けされません (標準のメタデータコンテナがないため)。

---

## 📝 ライセンス

MIT ライセンス — 詳細は [LICENSE](LICENSE) をご覧ください。

*Created by [Takoyune](https://github.com/takoyune)*
