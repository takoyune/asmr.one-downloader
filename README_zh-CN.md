<div align="center">
  <h1>🎙️ ASMR.ONE 下载器</h1>
  <p><strong>一个基于终端的 <a href="https://asmr.one">ASMR.ONE</a> 异步下载器 — 持久化、支持断点续传、带宽限速且完全支持脚本化。</strong></p>

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

## 📋 目录

<div align="center">

| | | |
|:---:|:---:|:---:|
| [✨ 特性](#-特性) | [📦 要求](#-要求) | [🚀 安装](#-安装) |
| [▶️ 运行程序](#️-运行程序) | [🖥️ 交互式菜单](#️-使用--交互式菜单) | [🔧 CLI参数](#-使用--cli参数) |
| [⚙️ 配置](#️-配置) | [📁 项目结构](#-项目结构) | [🔍 故障排除](#-故障排除) |

</div>

---

## 🆕 v1.3.22072026 更新说明 (搜索与语言全面大改)

一次重大的体验升级，专注于更智能的在线搜索、与官方网站一致的标签过滤以及完整的多语言标签/音频语言配置。

### 🔍 在线搜索 — 全面重构
- **交互式搜索子菜单** — 选项 `[3] Search ASMR.ONE Online` 不再是单一的搜索框，而是打开一个专用的子菜单：
  ```
  [1] 通用关键字 / 标题搜索
  [2] 标签搜索 (例如：耳かき 睡眠 膝枕)
  [3] 声优 / CV 搜索 (例如：本渡楓)
  [4] 社团搜索
  [5] 自定义语法过滤 ($tagw:, $rate:, $duration:)
  [B] 返回主菜单
  ```
- **结果表格新增标签列** — 搜索结果现在包含一个 **标签** 列，您可以立即查看每部作品包含的内容。

### 🏷️ 官方网站标签语法
- 标签搜索现在使用与 ASMR.ONE 网站完全相同的过滤格式： **`$tagw:TAG$`**
- 支持通过空格分隔的多个标签 (例如：`耳かき 睡眠` → `$tagw:耳かき$ $tagw:睡眠$`)
- 也可用作 CLI 参数： `./asmr --tag "耳かき 睡眠"`

### 🌐 双语言优先级设置
现在可以在 `config.json` 和 **Settings** (设置) 菜单中使用两个独立的语言优先级列表：

| 设置 | 用途 |
|---------|---------|
| `audio_language_priority` | 作品的首选音频/语音语言版本 (例如：日语，英语，中文) |
| `tag_language_priority` | 在搜索结果和文件元数据中显示标签的语言 |

两者都支持 `ja-jp`、`en-us` 和 `zh-cn` 的任意顺序组合，具有后备链功能。例如：
```json
"audio_language_priority": ["ja-jp", "en-us", "zh-cn"],
"tag_language_priority": ["en-us"]
```
这将优先下载日语版本的音频并以英语显示标签。您可以随时通过 `[6] Settings` 进行更改。

### ⌨️ 新增 CLI 参数
| 参数 | 说明 |
|------|-------------|
| `--search QUERY` | 在线搜索 ASMR.ONE 并获取交互式结果表格 |
| `--tag TAGS` | 使用官方 `$tagw:TAG$` 语法的标签搜索 |
| `--va NAME` | 按声优 / CV 名称搜索 |
| `--circle NAME` | 按社团名称搜索 |

---

## 🔒 历史重大更新

<details>
<summary><strong>v1.2.07072026 (库与队列稳定性)</strong></summary>

### 🗄️ 下载引擎
- 具有可配置并发数的 **异步并发下载** (默认：3个并行文件)
- 使用 HTTP `Range` 请求头的 **断点续传支持** — `.tmp` 文件在会话之间保留
- 每个文件的 **3次重试循环**，并记录每次失败原因 (HTTP 状态码，异常类型)
- 通过配置文件中的 `bandwidth_limit_mbps` 实现 **令牌桶带宽限速**
- **启动时镜像测速** — 并行 ping 所有镜像，自动选择最快的一个

### 📚 库与队列
- 跟踪每次完成下载的 **SQLite 库** (`history.db`)
- **重复检测** — 自动跳过已拥有的作品
- **持久化队列** — 即使中断也能保留；使用 `--resume` 恢复
- **格式优先级去重** — 当同一音轨同时存在 WAV 和 MP3 时，仅下载首选格式

### 🖥️ CLI 与 UI
- **`--list`** — 打印完整的文件夹/文件树而不下载
- **`--dry-run`** — 模拟下载并显示文件大小
- **`--all`** — 跳过文件选择提示
- **`--batch`** — 加载包含作品代码 (RJ/VJ) 的 `.txt` 文件
- **会话报告** — 成功/失败/跳过计数、经过的时间、平均速度
- 队列完成时的 **Windows 提示音**

### 🎵 元数据与整理
- 通过 `mutagen` 添加 **音频标签** — MP3/FLAC/OGG 的标题、艺术家、专辑、封面
- 使用 `{rj_id}`, `{title}`, `{circle}`, `{year}` 的 `dir_template` 进行 **灵活的文件夹命名**
- 将文件整理到 `Audio/`, `Images/`, `Text/` 子目录的 **可选文件分类**

</details>

---

## ✨ 特性

### 下载引擎
- **异步并发下载** (基于 `asyncio` + `aiohttp`)。并发数可配置 (默认：3个并行文件)。
- **断点续传支持** — 下载使用 HTTP `Range` 请求头。保留 `.tmp` 文件，并在重新启动时扩展。
- 每个文件的 **3次重试循环**。故障与原因会被记录，并显示在会话报告中。
- **令牌桶带宽限速** — 设置 `bandwidth_limit_mbps` 全局限制下载速度。`0` = 无限制。
- **启动时镜像测速** — 并行 ping 所有配置的 API 镜像，自动选择最快的镜像。

### 库与队列
- **SQLite 库** (`history.db`) 追踪每次完成的下载：作品代码，标题，本地路径，文件大小，日期。
- **重复检测** — 在加入队列前跳过已拥有的作品。
- **持久化队列** — 下载队列存在于数据库中。中断的会话重启后仍然有效。使用 `--resume` 继续。
- **格式优先级去重** — 当作品包含多个格式版本时，仅下载首选格式。

### 在线搜索
- **关键字 / 标题搜索** — 搜索 ASMR.ONE 并获取带编号的交互式结果表格。
- **标签搜索** — 使用官方 ASMR.ONE 网站语法 (`$tagw:TAG$`)，支持多个标签。
- **声优与社团搜索** — 通过 CLI 参数或交互式子菜单进行专用过滤。
- **自定义语法过滤** — 完全支持 `$rate:`, `$duration:`, `$tagw:` 等 ASMR.ONE 查询运算符。
- **搜索结果的标签列** — 以您配置的语言 (日语，英语或中文) 显示。

### CLI 与 UI
- **`--search`** — 从命令行进行在线搜索。
- **`--tag`** — 使用官方网站语法进行标签过滤搜索。
- **`--list`** — 打印完整的文件夹/文件树而不下载。
- **`--dry-run`** — 模拟下载；显示文件和总大小，不写入任何内容。
- **`--all`** — 跳过文件选择提示；下载全部。
- **`--batch`** — 加载包含作品代码的 `.txt` 文件。
- **会话报告** — 每个作业完成后：成功/失败/跳过计数、经过的时间、平均速度。
- **Windows 提示音** — 完整队列结束时播放系统声音。

### 元数据与多语言支持
- **音频标签** (`mutagen`) — 写入 MP3、FLAC 和 OGG 的标题、艺术家、专辑和封面。
- **灵活的文件夹命名** — 使用 `{rj_id}`, `{title}`, `{circle}`, `{year}` 可配置的 `dir_template`。
- **可选文件分类** — 启用 `sort_files` 可分类为 `Audio/`, `Images/`, `Text/`。
- **双语言优先级配置** — 分别控制音频版本和标签显示的语言。

---

## 📦 要求

- **Python 3.10 或更高版本** — [python.org](https://www.python.org/downloads/)
- 支持 ANSI 颜色的终端：
  - Windows：**Windows Terminal** (推荐)、VS Code 终端或 PowerShell 7+
  - macOS/Linux：任何现代终端模拟器
- **Git** (用于克隆) — [git-scm.com](https://git-scm.com/)

Python 包 (通过 `setup.bat` 或 `pip install -r requirements.txt` 自动安装)：

| 包 | 用途 |
|---------|---------|
| `aiohttp` | 用于下载和 API 调用的异步 HTTP 客户端 |
| `aiofiles` | 写入下载区块的异步文件 I/O |
| `aiodns` | 自定义 DNS 解析器 (绕过 ISP 级封锁) |
| `rich` | 终端 UI — 进度条，表格，面板，颜色 |
| `mutagen` | 音频元数据标签 (MP3, FLAC, OGG) |
| `pydantic` | 配置验证和模式执行 |
| `requests` | 同步 GitHub 更新检查 |
| `packaging` | 解析版本字符串进行更新对比 |

---

## 🚀 安装

### 第一步 — 克隆仓库

```bash
git clone https://github.com/takoyune/asmr.one-downloader.git
cd asmr.one-downloader
```

或直接从 GitHub 下载 ZIP 压缩包并解压到您选择的文件夹中。

### 第二步 — 安装依赖

**选项 A: 自动化 (Windows)**

```bat
setup.bat
```

只运行一次 — 创建虚拟环境并安装所有依赖。以后启动 `./asmr` 将自动使用该 venv。

**选项 B: 手动 (Windows / Linux / macOS)**

```bash
# (可选但推荐) 创建一个虚拟环境
python -m venv venv

# 激活它
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 第三步 — 验证安装

```bash
python main.py --version
```

---

## ▶️ 运行程序

### Windows

```powershell
./asmr              # 打开交互式菜单
./asmr RJ123456     # 直接下载
./asmr --help       # 所有可用的参数
```

> CMD 用户: `asmr.bat` 用法相同。

### Linux / macOS

```bash
chmod +x asmr       # 克隆后的一次性操作

./asmr              # 打开交互式菜单
./asmr RJ123456     # 直接下载
./asmr --list RJ123456      # 预览文件树
./asmr --dry-run RJ123456   # 模拟下载
./asmr --help               # 所有可用的参数
```

---

## 🖥️ 使用 — 交互式菜单

不带任何参数启动 `./asmr`：

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    ASMR.ONE DOWNLOADER                        ┃
┃                       by Takoyune                             ┃
┃               https://github.com/takoyune                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 📚 Library: 11 works ━┛

[1] Download (Work Codes) [下载 (作品代码)]
[2] Batch Download from File [从文件批量下载]
[3] Search ASMR.ONE Online [在线搜索 ASMR.ONE]
[4] Library Browser [库浏览器]
[5] Queue Manager [队列管理器]
[6] Settings [设置]
[7] Statistics Dashboard [统计仪表板]
[8] System Utilities [系统实用工具]
[X] Exit [退出]
```

#### [1] Download (Work Codes)
输入一个或多个作品代码 (例如：`RJ123456 VJ01002074`)。程序获取元数据，显示完整的文件树，并让您通过数字或范围 (例如：`1 3-5 7`) 选择特定文件。留空则下载全部内容。

#### [2] Batch Download from File
输入一个包含作品代码 (RJ 或 VJ) 的 `.txt` 文件的路径，每行一个。所有代码都将被验证，与您的库核对并进入队列。

```
# 批处理文件示例 (my_list.txt)
RJ01234567
VJ01002074
RJ00112233
```

#### [3] Search ASMR.ONE Online
打开具有专用模式的搜索子菜单：
```
[1] 通用关键字 / 标题搜索
[2] 标签搜索 (例如：耳かき 睡眠 膝枕)
[3] 声优 / CV 搜索 (例如：本渡楓)
[4] 社团搜索
[5] 自定义语法过滤 ($tagw:, $rate:, $duration:, 等等)
[B] 返回主菜单
```
结果显示在带编号的表格中，包含标题、社团、CV、标签（您配置的语言）和评分。输入编号即可立即加入队列。

#### [4] Library Browser
按标题或社团名称搜索您的本地下载历史记录。显示本地文件夹路径和文件大小。

#### [5] Queue Manager
查看队列中当前的所有项目 (待处理 / 活跃 / 错误状态)。添加新代码、更改优先级或删除项目。

#### [6] Settings
交互式编辑所有配置选项，包括：
- 下载目录，代理，镜像
- 并发下载数，带宽限制
- **音频语言优先级** — 首选的音频语言版本
- **标签语言优先级** — 标签显示的语言 (`ja-jp`, `en-us`, `zh-cn`)
- 格式优先级列表编辑器

#### [7] Statistics Dashboard
您的库的概览：作品总数、磁盘总大小、队列长度、平均作品大小。

#### [8] System Utilities
- **清理缓存** — 扫描 `.tmp` 文件，并在删除前显示摘要。
- **网络诊断** — 测试所有 API 镜像并显示延迟。
- **镜像选择器** — 重新运行速度测试并更新活动的镜像。

---

## 🔧 使用 — CLI参数

```
usage: ./asmr [-h] [-b FILE] [-a] [--list] [--export FILE] [--test]
              [--dry-run] [--resume] [--no-update-check] [--verbose]
              [--search QUERY] [--tag TAGS] [--va NAME] [--circle NAME] [-v]
              [rj_codes ...]
```

| 参数 | 缩写 | 说明 |
|------|-------|-------------|
| `work_codes` | — | 一个或多个要立即加入队列和下载的作品代码 (RJ 或 VJ) |
| `--batch FILE` | `-b` | 包含作品代码的 `.txt` 文件的路径，每行一个 |
| `--all` | `-a` | 跳过文件选择提示；下载所有音轨 |
| `--list` | — | 打印每个作品代码的完整音轨树并退出 |
| `--export FILE` | — | 将库导出为 CSV 或 JSON (例如 `library.csv`) |
| `--test` | — | 测试所有 API 镜像并显示延迟信息 |
| `--dry-run` | — | 显示将要下载的文件和总大小；不写入任何内容 |
| `--resume` | — | 跳过镜像测试和更新检查；立即处理现有队列 |
| `--no-update-check` | — | 在此会话中跳过 GitHub 更新检查 |
| `--verbose` | — | 将 DEBUG 级别的日志写入 `singularity.log` |
| `--search QUERY` | — | 在线搜索 ASMR.ONE 并显示交互式结果 |
| `--tag TAGS` | `-t` | 使用官方网站语法的标签搜索 (空格分隔的标签) |
| `--va NAME` | — | 按声优 / CV 名称搜索 |
| `--circle NAME` | — | 按社团名称搜索 |
| `--version` | `-v` | 打印版本并退出 |
| `--help` | `-h` | 显示使用摘要 |

### CLI 示例

```bash
# 下载单部作品
./asmr RJ01234567
./asmr VJ01002074

# 下载多部作品，跳过文件选择
./asmr --all RJ01234567 VJ01002074

# 在不下载的情况下预览文件树
./asmr --list RJ01234567

# 模拟下载 (显示大小，不写入)
./asmr --dry-run VJ01002074

# 按关键字搜索
./asmr --search "sleeping ASMR"

# 使用官方网站语法按标签搜索
./asmr --tag "耳かき 睡眠"

# 按声优搜索
./asmr --va "本渡楓"

# 按社团搜索
./asmr --circle "ろまあぽ"

# 从文件运行一批代码
./asmr --batch my_list.txt

# 批量下载文件中的所有内容，无提示
./asmr --batch my_list.txt --all

# 恢复中断的会话
./asmr --resume

# 调试失败的下载
./asmr --verbose RJ01234567
# 然后检查 singularity.log
```

---

## ⚙️ 配置

第一次启动时自动创建 `config.json`。直接编辑它或通过交互式菜单中的 **[6] Settings** 进行编辑。

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

| 键 | 默认值 | 说明 |
|-----|---------|-------------|
| 📁 `output_dir` | `"Downloads"` | 下载作品保存的位置 |
| ⚡ `max_concurrent` | `3` | 并行下载的文件数 (1–20) |
| 🌐 `proxy` | `null` | HTTP 或 SOCKS5 代理 URL |
| 🔗 `mirror` | auto | API 镜像 URL — 启动时自动设置 |
| 🎵 `tag_audio` | `true` | 将元数据标签写入 MP3 / FLAC / OGG |
| 📂 `sort_files` | `false` | 整理到 `Audio/`, `Images/`, `Text/` 子文件夹 |
| 🏷️ `dir_template` | `"{rj_id} {title}"` | 文件夹名称模板 |
| ⏱️ `timeout` | `60` | HTTP 请求超时 (秒) |
| 🛡️ `dns` | `"1.1.1.1"` | DNS 服务器 — 使用 `1.1.1.1` 或 `8.8.8.8` 绕过 ISP 封锁 |
| 📶 `bandwidth_limit_mbps` | `0.0` | 速度上限 (MB/s) — `0` = 无限制 |
| 🎵 `create_playlist` | `true` | 下载后生成 `.m3u8` 播放列表文件 |
| 🌍 `audio_language_priority` | `["ja-jp","en-us","zh-cn"]` | 音频版本的首选语言 |
| 🏷️ `tag_language_priority` | `["en-us"]` | 搜索结果中显示标签的语言 |
| 🎚️ `format_priority` | `["flac","wav","mp3",…]` | 当某音轨有多个版本时的首选格式 |
| 🕐 `last_update_check` | `0.0` | 自动管理 — 若在24小时内运行则跳过 GitHub 检查 |

### `dir_template` 示例

| 模板 | 结果文件夹名 |
|----------|--------------------|
| `"{rj_id} {title}"` | `RJ01234567 Some Work Title` |
| `"{circle} - {title}"` | `SomeCircle - Some Work Title` |
| `"{year}/{circle}/{title}"` | `2024/SomeCircle/Some Work Title` |

### 语言优先级的值

| 值 | 语言 |
|-------|----------|
| `ja-jp` | 日语 |
| `en-us` | 英语 |
| `zh-cn` | 简体中文 |

---

## 📁 项目结构

```
asmr.one-downloader/
│
├── main.py          # 入口点 — CLI 参数，启动检查，更新检查
├── asmr             # Linux / macOS 启动器 (运行: chmod +x asmr)
├── asmr.bat         # Windows CMD 启动器
├── asmr.ps1         # Windows PowerShell 启动器
├── setup.bat        # 首次设置 (创建 venv + 安装依赖)
├── requirements.txt # Python 依赖
├── config.json      # 您的设置 (首次运行时自动创建)
├── history.db       # SQLite — 库和下载队列
├── singularity.log  # 循环日志文件
│
└── main/
    ├── app.py           # UI，菜单，作业执行，搜索
    ├── orchestrator.py  # 下载逻辑，重试，统计
    ├── network.py       # HTTP 客户端，镜像管理
    ├── db.py            # 所有数据库操作
    ├── config.py        # 配置加载与验证
    ├── models.py        # 数据类型 (WorkMetadata, TrackItem, 等等)
    ├── audio.py         # 音频元数据标记
    └── constants.py     # 镜像，日志设置，共享常量，标签本地化
```

---

## 🔍 故障排除

### "All API mirrors are unreachable" (所有API镜像不可达) 或 连接错误
**ASMR.ONE 在东亚 (日本，中国等) 之外被主动限制区域。**
如果启动时的镜像测试失败，您的连接可能已被屏蔽。请使用 **Cloudflare WARP**：

1. 从 [https://one.one.one.one/](https://one.one.one.one/) 下载
2. 打开 WARP 设置 → 选择 **Traffic and DNS (UDP)**
3. 开启连接，然后重启下载器。

或在 `config.json` 中设置 `proxy` 字段 (例如：`"http://user:pass@ip:port"`)。

### 下载反复挂起或超时
- 增加 `config.json` 中的 `timeout` (例如：`120`)
- 减少 `max_concurrent` 至 `1` 或 `2`
- 尝试更换 DNS 或启用代理

### 标签显示语言错误
将 `config.json` 中的 `tag_language_priority` 设置为您首选的语言：
```json
"tag_language_priority": ["en-us"]          // 仅英语
"tag_language_priority": ["ja-jp", "en-us"] // 日语，失败则回退到英语
```

### 恢复下载时进度条百分比起点错误
这是一个已知的显示问题。下载实际上是从正确的字节偏移量正确恢复的 — 随着数据的流入，显示会自动修正。

### `singularity.log` 噪音太大
默认情况下，仅记录 `INFO`, `WARNING` 和 `ERROR` 消息。`--verbose` 参数会添加 `DEBUG` 输出 (每个 HTTP 请求，字节偏移量，重试尝试次数)。仅在积极调试时使用 `--verbose`。

### 启动时出现含糊信息的 "Fatal error" (致命错误)
请检查项目根目录中的 `singularity.log` 以获取完整的追踪日志。

### 文件下载后未被标记
确保 `config.json` 中的 `tag_audio` 为 `true`。标记仅适用于 MP3, FLAC 和 OGG 文件。WAV 文件不会被标记 (没有标准的元数据容器)。

---

## 📝 许可证

MIT 许可证 — 详见 [LICENSE](LICENSE)。

*由 [Takoyune](https://github.com/takoyune) 创建*
