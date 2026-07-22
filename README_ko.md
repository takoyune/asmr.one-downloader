<div align="center">
  <h1>🎙️ ASMR.ONE 다운로더</h1>
  <p><strong><a href="https://asmr.one">ASMR.ONE</a>을 위한 비동기식 터미널 기반 다운로더 — 영구적, 이어받기 가능, 대역폭 제한 지원 및 완전한 스크립트화 가능.</strong></p>

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

## 📋 목차

<div align="center">

| | | |
|:---:|:---:|:---:|
| [✨ 주요 기능](#-주요-기능) | [📦 요구 사항](#-요구-사항) | [🚀 설치](#-설치) |
| [▶️ 앱 실행](#️-앱-실행) | [🖥️ 대화형 메뉴](#️-사용법--대화형-메뉴) | [🔧 CLI 플래그](#-사용법--cli-플래그) |
| [⚙️ 설정](#️-설정) | [📁 프로젝트 구조](#-프로젝트-구조) | [🔍 문제 해결](#-문제-해결) |

</div>

---

## 🆕 v1.3.22072026의 새로운 기능 (검색 및 언어 전면 개편)

더욱 스마트해진 온라인 검색, 공식 웹사이트와 동일한 태그 필터링, 완벽한 다국어 태그/오디오 언어 설정에 중점을 둔 주요 편의성(QoL) 업데이트입니다.

### 🔍 온라인 검색 — 전면 개편
- **대화형 검색 하위 메뉴** — 단일 검색 상자 대신, `[3] Search ASMR.ONE Online` 옵션이 전용 하위 메뉴를 엽니다:
  ```
  [1] 일반 키워드 / 제목 검색
  [2] 태그 검색 (예: 耳かき 睡眠 膝枕)
  [3] 성우 / CV 검색 (예: 本渡楓)
  [4] 서클 검색
  [5] 사용자 지정 구문 필터 ($tagw:, $rate:, $duration:)
  [B] 메인 메뉴로 돌아가기
  ```
- **검색 결과 테이블의 태그 열** — 검색 결과에 **태그** 열이 추가되어 각 작품의 내용을 바로 확인할 수 있습니다.

### 🏷️ 공식 웹사이트 태그 구문
- 태그 검색은 이제 ASMR.ONE 웹사이트와 정확히 동일한 필터 형식을 사용합니다: **`$tagw:TAG$`**
- 공백으로 구분하여 여러 태그를 지원합니다 (예: `耳かき 睡眠` → `$tagw:耳かき$ $tagw:睡眠$`)
- CLI 플래그로도 사용 가능: `./asmr --tag "耳かき 睡眠"`

### 🌐 이중 언어 우선순위 설정
`config.json` 및 **Settings**(설정) 메뉴에서 두 개의 별도 언어 우선순위 목록을 사용할 수 있습니다:

| 설정 | 목적 |
|---------|---------|
| `audio_language_priority` | 작품의 선호하는 오디오/음성 언어 에디션 (예: 일본어, 영어, 중국어) |
| `tag_language_priority` | 검색 결과 및 파일 메타데이터에 태그를 표시할 언어 |

두 설정 모두 `ja-jp`, `en-us`, `zh-cn`을 임의의 순서로 지원하며 폴백(대체) 체인을 갖습니다. 예:
```json
"audio_language_priority": ["ja-jp", "en-us", "zh-cn"],
"tag_language_priority": ["en-us"]
```
이렇게 설정하면 오디오는 일본어 에디션을 최우선으로 다운로드하고, 태그는 영어로 표시합니다. 언제든지 `[6] Settings`를 통해 변경할 수 있습니다.

### ⌨️ 새로운 CLI 플래그
| 플래그 | 설명 |
|------|-------------|
| `--search QUERY` | ASMR.ONE을 온라인으로 검색하고 대화형 결과 테이블 가져오기 |
| `--tag TAGS` | 공식 `$tagw:TAG$` 구문을 사용한 태그 검색 |
| `--va NAME` | 성우 / CV 이름으로 검색 |
| `--circle NAME` | 서클 이름으로 검색 |

---

## 🔒 이전 주요 업데이트

<details>
<summary><strong>v1.2.07072026 (라이브러리 및 큐 안정성)</strong></summary>

### 🗄️ 다운로드 엔진
- 구성 가능한 동시성을 갖춘 **비동기 동시 다운로드** (기본값: 파일 3개 병렬)
- HTTP `Range` 헤더를 사용한 **이어받기 지원** — 세션 간에 `.tmp` 파일이 유지됨
- 실패 원인(HTTP 상태, 예외 유형) 로깅과 함께 파일당 **3회 재시도 루프**
- 설정의 `bandwidth_limit_mbps`를 통한 **토큰 버킷 대역폭 제한기**
- **시작 시 미러 속도 테스트** — 모든 미러를 병렬로 핑(ping)하여 가장 빠른 것을 자동으로 선택

### 📚 라이브러리 및 큐
- 완료된 모든 다운로드를 추적하는 **SQLite 라이브러리** (`history.db`)
- **중복 감지** — 이미 소유한 작품은 자동으로 건너뜀
- **영구적인 큐** — 중단되어도 유지됨; `--resume`으로 계속 진행
- **형식 우선순위 중복 제거** — 동일한 트랙에 WAV와 MP3가 모두 존재할 경우 선호하는 형식만 다운로드

### 🖥️ CLI 및 UI
- **`--list`** — 다운로드하지 않고 전체 폴더/파일 트리 출력
- **`--dry-run`** — 다운로드 시뮬레이션 및 파일 크기 표시
- **`--all`** — 파일 선택 프롬프트 건너뛰기
- **`--batch`** — 작품 코드(RJ/VJ)가 포함된 `.txt` 파일 불러오기
- **세션 보고서** — 성공/실패/건너뜀 횟수, 경과 시간, 평균 속도
- 큐 완료 시 **Windows 완료 비프음**

### 🎵 메타데이터 및 정리
- `mutagen`을 통한 **오디오 태깅** — MP3/FLAC/OGG용 제목, 아티스트, 앨범, 커버 아트
- `{rj_id}`, `{title}`, `{circle}`, `{year}`를 사용하는 `dir_template`을 통한 **유연한 폴더 이름 지정**
- 파일을 `Audio/`, `Images/`, `Text/` 하위 디렉터리로 정리하는 **선택적 파일 분류**

</details>

---

## ✨ 주요 기능

### 다운로드 엔진
- **비동기 동시 다운로드** (`asyncio` + `aiohttp` 기반). 동시성 구성 가능 (기본값: 파일 3개 병렬).
- **이어받기 지원** — 다운로드 시 HTTP `Range` 헤더를 사용합니다. `.tmp` 파일이 세션 간에 유지되며 다시 시작할 때 확장됩니다.
- 파일당 **3회 재시도 루프**. 실패는 원인과 함께 기록되며 세션 보고서에 표시됩니다.
- **토큰 버킷 대역폭 제한기** — `bandwidth_limit_mbps`를 설정하여 전역 다운로드 속도를 제한합니다. `0` = 무제한.
- **시작 시 미러 속도 테스트** — 구성된 모든 API 미러를 병렬로 핑(ping)하고 가장 빠른 미러를 자동으로 선택합니다.

### 라이브러리 및 큐
- **SQLite 라이브러리** (`history.db`)는 완료된 모든 다운로드를 추적합니다: 작품 코드, 제목, 로컬 경로, 파일 크기, 날짜.
- **중복 감지** — 이미 소유한 작품은 큐에 추가하기 전에 건너뜁니다.
- **영구적인 큐** — 다운로드 큐는 데이터베이스에 존재합니다. 중단된 세션은 다시 시작해도 유지됩니다. `--resume`을 사용하여 계속 진행하세요.
- **형식 우선순위 중복 제거** — 작품에 여러 형식 버전이 포함된 경우 선호하는 형식만 다운로드됩니다.

### 온라인 검색
- **키워드 / 제목 검색** — ASMR.ONE을 검색하고 번호가 매겨진 대화형 결과 테이블을 얻습니다.
- **태그 검색** — 공식 ASMR.ONE 웹사이트 구문 (`$tagw:TAG$`)을 사용하며 여러 태그를 지원합니다.
- **성우 및 서클 검색** — CLI 플래그 또는 대화형 하위 메뉴를 통한 전용 필터.
- **사용자 지정 구문 필터** — `$rate:`, `$duration:`, `$tagw:` 및 기타 ASMR.ONE 쿼리 연산자를 완벽하게 지원합니다.
- **검색 결과의 태그 열** — 구성된 언어(일본어, 영어 또는 중국어)로 표시됩니다.

### CLI 및 UI
- **`--search`** — 명령줄에서 온라인으로 검색합니다.
- **`--tag`** — 공식 웹사이트 구문을 사용한 태그 필터 검색.
- **`--list`** — 다운로드하지 않고 전체 폴더/파일 트리를 출력합니다.
- **`--dry-run`** — 다운로드를 시뮬레이션합니다; 파일 및 총 크기를 표시하며 아무것도 쓰지 않습니다.
- **`--all`** — 파일 선택 프롬프트를 건너뛰고 모두 다운로드합니다.
- **`--batch`** — 작품 코드가 포함된 `.txt` 파일을 불러옵니다.
- **세션 보고서** — 각 작업 후: 성공/실패/건너뜀 횟수, 경과 시간, 평균 속도.
- **Windows 완료 비프음** — 전체 큐가 완료되면 시스템 소리가 재생됩니다.

### 메타데이터 및 다국어 지원
- **오디오 태깅** (`mutagen`) — MP3, FLAC, OGG에 제목, 아티스트, 앨범 및 커버 아트가 기록됩니다.
- **유연한 폴더 이름 지정** — `{rj_id}`, `{title}`, `{circle}`, `{year}`를 사용하여 구성 가능한 `dir_template`.
- **선택적 파일 분류** — `sort_files`를 활성화하여 `Audio/`, `Images/`, `Text/`로 정리합니다.
- **이중 언어 우선순위 구성** — 오디오 에디션과 태그 표시에 사용할 언어를 별도로 제어합니다.

---

## 📦 요구 사항

- **Python 3.10 이상** — [python.org](https://www.python.org/downloads/)
- ANSI 색상을 지원하는 터미널:
  - Windows: **Windows Terminal** (권장), VS Code 터미널 또는 PowerShell 7+
  - macOS/Linux: 최신 터미널 에뮬레이터
- **Git** (클론용) — [git-scm.com](https://git-scm.com/)

Python 패키지 (`setup.bat` 또는 `pip install -r requirements.txt`에 의해 자동으로 설치됨):

| 패키지 | 목적 |
|---------|---------|
| `aiohttp` | 다운로드 및 API 호출을 위한 비동기 HTTP 클라이언트 |
| `aiofiles` | 다운로드 청크 쓰기를 위한 비동기 파일 I/O |
| `aiodns` | 사용자 지정 DNS 확인자 (ISP 수준 차단 우회) |
| `rich` | 터미널 UI — 진행률 표시줄, 테이블, 패널, 색상 |
| `mutagen` | 오디오 메타데이터 태깅 (MP3, FLAC, OGG) |
| `pydantic` | 구성 유효성 검사 및 스키마 적용 |
| `requests` | 동기식 GitHub 업데이트 확인 |
| `packaging` | 업데이트 비교를 위한 버전 문자열 구문 분석 |

---

## 🚀 설치

### 1단계 — 리포지토리 클론

```bash
git clone https://github.com/takoyune/asmr.one-downloader.git
cd asmr.one-downloader
```

또는 GitHub에서 직접 ZIP을 다운로드하고 원하는 폴더에 압축을 풉니다.

### 2단계 — 종속성 설치

**옵션 A: 자동화 (Windows)**

```bat
setup.bat
```

한 번만 실행하면 가상 환경을 만들고 모든 종속성을 설치합니다. 이후의 모든 `./asmr` 실행은 venv를 자동으로 사용합니다.

**옵션 B: 수동 (Windows / Linux / macOS)**

```bash
# (선택 사항이지만 권장) 가상 환경 만들기
python -m venv venv

# 활성화하기
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate

# 종속성 설치
pip install -r requirements.txt
```

### 3단계 — 설치 확인

```bash
python main.py --version
```

---

## ▶️ 앱 실행

### Windows

```powershell
./asmr              # 대화형 메뉴 열기
./asmr RJ123456     # 직접 다운로드
./asmr --help       # 사용 가능한 모든 플래그
```

> CMD 사용자: `asmr.bat`도 같은 방식으로 작동합니다.

### Linux / macOS

```bash
chmod +x asmr       # 클론 후 한 번만 실행하는 단계

./asmr              # 대화형 메뉴 열기
./asmr RJ123456     # 직접 다운로드
./asmr --list RJ123456      # 파일 트리 미리보기
./asmr --dry-run RJ123456   # 다운로드 시뮬레이션
./asmr --help               # 사용 가능한 모든 플래그
```

---

## 🖥️ 사용법 — 대화형 메뉴

인수 없이 `./asmr` 실행:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    ASMR.ONE DOWNLOADER                        ┃
┃                       by Takoyune                             ┃
┃               https://github.com/takoyune                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 📚 Library: 11 works ━┛

[1] Download (Work Codes) [다운로드 (작품 코드)]
[2] Batch Download from File [파일에서 일괄 다운로드]
[3] Search ASMR.ONE Online [ASMR.ONE 온라인 검색]
[4] Library Browser [라이브러리 브라우저]
[5] Queue Manager [큐 관리자]
[6] Settings [설정]
[7] Statistics Dashboard [통계 대시보드]
[8] System Utilities [시스템 유틸리티]
[X] Exit [종료]
```

#### [1] Download (Work Codes)
하나 이상의 작품 코드(예: `RJ123456 VJ01002074`)를 입력합니다. 앱은 메타데이터를 가져오고 전체 파일 트리를 표시하며 번호 또는 범위(예: `1 3-5 7`)로 특정 파일을 선택할 수 있게 해줍니다. 비워두면 모든 항목을 다운로드합니다.

#### [2] Batch Download from File
한 줄에 하나의 작품 코드(RJ 또는 VJ)가 있는 `.txt` 파일의 경로를 입력합니다. 모든 코드는 유효성이 검사되고, 라이브러리와 대조 확인된 후 큐에 추가됩니다.

```
# 일괄 파일 예시 (my_list.txt)
RJ01234567
VJ01002074
RJ00112233
```

#### [3] Search ASMR.ONE Online
전용 모드가 있는 검색 하위 메뉴를 엽니다:
```
[1] 일반 키워드 / 제목 검색
[2] 태그 검색 (예: 耳かき 睡眠 膝枕)
[3] 성우 / CV 검색 (예: 本渡楓)
[4] 서클 검색
[5] 사용자 지정 구문 필터 ($tagw:, $rate:, $duration: 등)
[B] 메인 메뉴로 돌아가기
```
결과는 제목, 서클, CV, 태그(구성된 언어로 표시됨) 및 등급이 포함된 번호가 매겨진 테이블에 표시됩니다. 번호를 입력하면 즉시 큐에 추가됩니다.

#### [4] Library Browser
제목이나 서클 이름으로 로컬 다운로드 기록을 검색합니다. 로컬 폴더 경로와 파일 크기를 표시합니다.

#### [5] Queue Manager
현재 큐에 있는 모든 항목(대기 중 / 활성 / 오류 상태)을 확인합니다. 새 코드를 추가하거나 우선순위를 변경하거나 항목을 제거할 수 있습니다.

#### [6] Settings
다음을 포함한 모든 설정 옵션을 대화형으로 편집합니다:
- 다운로드 디렉터리, 프록시, 미러
- 동시 다운로드 수, 대역폭 제한
- **오디오 언어 우선순위** — 오디오 에디션의 선호 언어
- **태그 언어 우선순위** — 태그 표시 언어 (`ja-jp`, `en-us`, `zh-cn`)
- 형식 우선순위 목록 편집기

#### [7] Statistics Dashboard
라이브러리 개요: 총 작품 수, 디스크의 총 크기, 큐 길이, 평균 작품 크기.

#### [8] System Utilities
- **캐시 클리너** — `.tmp` 파일을 검색하고 삭제하기 전에 요약을 표시합니다.
- **네트워크 진단** — 대기 시간과 함께 모든 API 미러를 테스트합니다.
- **미러 선택기** — 속도 테스트를 다시 실행하고 활성 미러를 업데이트합니다.

---

## 🔧 사용법 — CLI 플래그

```
usage: ./asmr [-h] [-b FILE] [-a] [--list] [--export FILE] [--test]
              [--dry-run] [--resume] [--no-update-check] [--verbose]
              [--search QUERY] [--tag TAGS] [--va NAME] [--circle NAME] [-v]
              [rj_codes ...]
```

| 플래그 | 약어 | 설명 |
|------|-------|-------------|
| `work_codes` | — | 즉시 큐에 추가하고 다운로드할 하나 이상의 작품 코드 (RJ 또는 VJ) |
| `--batch FILE` | `-b` | 작품 코드가 한 줄에 하나씩 포함된 `.txt` 파일 경로 |
| `--all` | `-a` | 파일 선택 프롬프트를 건너뛰고 모든 트랙 다운로드 |
| `--list` | — | 각 작품 코드의 전체 트랙 트리를 출력하고 종료 |
| `--export FILE` | — | 라이브러리를 CSV 또는 JSON으로 내보내기 (예: `library.csv`) |
| `--test` | — | 모든 API 미러를 테스트하고 대기 시간 정보 표시 |
| `--dry-run` | — | 다운로드될 파일과 총 크기 표시; 아무것도 쓰지 않음 |
| `--resume` | — | 미러 테스트 및 업데이트 확인 건너뛰기; 기존 큐 즉시 처리 |
| `--no-update-check` | — | 이 세션에서 GitHub 업데이트 확인 건너뛰기 |
| `--verbose` | — | `singularity.log`에 DEBUG 수준 로그 기록 |
| `--search QUERY` | — | ASMR.ONE을 온라인으로 검색하고 대화형 결과 표시 |
| `--tag TAGS` | `-t` | 공식 웹사이트 구문을 사용한 태그 검색 (공백으로 구분된 태그) |
| `--va NAME` | — | 성우 / CV 이름으로 검색 |
| `--circle NAME` | — | 서클 이름으로 검색 |
| `--version` | `-v` | 버전을 출력하고 종료 |
| `--help` | `-h` | 사용법 요약 표시 |

### CLI 예시

```bash
# 단일 작품 다운로드
./asmr RJ01234567
./asmr VJ01002074

# 여러 작품 다운로드, 파일 선택 건너뛰기
./asmr --all RJ01234567 VJ01002074

# 다운로드하지 않고 파일 트리 미리보기
./asmr --list RJ01234567

# 다운로드 시뮬레이션 (크기 표시, 쓰기 없음)
./asmr --dry-run VJ01002074

# 키워드로 검색
./asmr --search "sleeping ASMR"

# 공식 웹사이트 구문을 사용하여 태그로 검색
./asmr --tag "耳かき 睡眠"

# 성우로 검색
./asmr --va "本渡楓"

# 서클로 검색
./asmr --circle "ろまあぽ"

# 파일에서 코드 일괄 실행
./asmr --batch my_list.txt

# 프롬프트 없이 파일의 모든 항목 일괄 다운로드
./asmr --batch my_list.txt --all

# 중단된 세션 재개
./asmr --resume

# 실패한 다운로드 디버깅
./asmr --verbose RJ01234567
# 그런 다음 singularity.log 확인
```

---

## ⚙️ 설정

첫 실행 시 `config.json`이 자동으로 생성됩니다. 직접 편집하거나 대화형 메뉴의 **[6] Settings**를 통해 편집할 수 있습니다.

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

| 키 | 기본값 | 설명 |
|-----|---------|-------------|
| 📁 `output_dir` | `"Downloads"` | 다운로드한 작품이 저장되는 위치 |
| ⚡ `max_concurrent` | `3` | 병렬 파일 다운로드 수 (1–20) |
| 🌐 `proxy` | `null` | HTTP 또는 SOCKS5 프록시 URL |
| 🔗 `mirror` | auto | API 미러 URL — 시작 시 자동으로 설정됨 |
| 🎵 `tag_audio` | `true` | MP3 / FLAC / OGG에 메타데이터 태그 쓰기 |
| 📂 `sort_files` | `false` | `Audio/`, `Images/`, `Text/` 하위 폴더로 정리 |
| 🏷️ `dir_template` | `"{rj_id} {title}"` | 폴더 이름 템플릿 |
| ⏱️ `timeout` | `60` | HTTP 요청 시간 초과(초) |
| 🛡️ `dns` | `"1.1.1.1"` | DNS 서버 — ISP 차단을 우회하려면 `1.1.1.1` 또는 `8.8.8.8` 사용 |
| 📶 `bandwidth_limit_mbps` | `0.0` | 속도 제한(MB/s) — `0` = 무제한 |
| 🎵 `create_playlist` | `true` | 다운로드 후 `.m3u8` 재생 목록 파일 생성 |
| 🌍 `audio_language_priority` | `["ja-jp","en-us","zh-cn"]` | 오디오 에디션의 선호 언어 |
| 🏷️ `tag_language_priority` | `["en-us"]` | 검색 결과에 태그를 표시할 언어 |
| 🎚️ `format_priority` | `["flac","wav","mp3",…]` | 트랙에 여러 버전이 있을 때의 선호 형식 |
| 🕐 `last_update_check` | `0.0` | 자동 관리 — 24시간 이내에 실행된 경우 GitHub 확인 건너뜀 |

### `dir_template` 예시

| 템플릿 | 결과 폴더 이름 |
|----------|--------------------|
| `"{rj_id} {title}"` | `RJ01234567 Some Work Title` |
| `"{circle} - {title}"` | `SomeCircle - Some Work Title` |
| `"{year}/{circle}/{title}"` | `2024/SomeCircle/Some Work Title` |

### 언어 우선순위 값

| 값 | 언어 |
|-------|----------|
| `ja-jp` | 일본어 |
| `en-us` | 영어 |
| `zh-cn` | 중국어 (간체) |

---

## 📁 프로젝트 구조

```
asmr.one-downloader/
│
├── main.py          # 진입점 — CLI 플래그, 사전 점검, 업데이트 확인
├── asmr             # Linux / macOS 런처 (실행: chmod +x asmr)
├── asmr.bat         # Windows CMD 런처
├── asmr.ps1         # Windows PowerShell 런처
├── setup.bat        # 최초 설정 (venv 생성 + 종속성 설치)
├── requirements.txt # Python 종속성
├── config.json      # 사용자 설정 (첫 실행 시 자동 생성)
├── history.db       # SQLite — 라이브러리 및 다운로드 큐
├── singularity.log  # 순환 로그 파일
│
└── main/
    ├── app.py           # UI, 메뉴, 작업 실행, 검색
    ├── orchestrator.py  # 다운로드 로직, 재시도, 통계
    ├── network.py       # HTTP 클라이언트, 미러 관리
    ├── db.py            # 모든 데이터베이스 작업
    ├── config.py        # 구성 로딩 및 유효성 검사
    ├── models.py        # 데이터 타입 (WorkMetadata, TrackItem 등)
    ├── audio.py         # 오디오 메타데이터 태깅
    └── constants.py     # 미러, 로그 설정, 공유 상수, 태그 현지화
```

---

## 🔍 문제 해결

### "All API mirrors are unreachable" (모든 API 미러에 연결할 수 없음) 또는 연결 오류
**ASMR.ONE은 동아시아(일본, 중국 등) 이외의 지역에서는 적극적으로 지역 차단(리전 락)되어 있습니다.**
시작 시 미러 테스트가 실패하면 연결이 차단되고 있는 것입니다. **Cloudflare WARP**를 사용해 보세요:

1. [https://one.one.one.one/](https://one.one.one.one/)에서 다운로드
2. WARP 설정을 열고 → **Traffic and DNS (UDP)** 선택
3. 연결을 켜고 다운로더를 다시 시작합니다.

또는 `config.json`의 `proxy` 필드를 설정하세요 (예: `"http://user:pass@ip:port"`).

### 다운로드가 반복적으로 멈추거나 시간 초과됨
- `config.json`에서 `timeout`을 늘립니다 (예: `120`)
- `max_concurrent`를 `1` 또는 `2`로 줄입니다
- 다른 DNS를 사용해 보거나 프록시를 활성화합니다

### 태그가 잘못된 언어로 표시됨
`config.json`의 `tag_language_priority`를 선호하는 언어로 설정하세요:
```json
"tag_language_priority": ["en-us"]          // 영어만
"tag_language_priority": ["ja-jp", "en-us"] // 일본어, 실패 시 영어로 폴백
```

### 다시 시작할 때 진행률 표시줄이 잘못된 비율에서 시작됨
이것은 알려진 시각적 문제입니다. 다운로드는 올바른 바이트 오프셋에서 실제로 올바르게 다시 시작되고 있으며 — 데이터가 유입됨에 따라 시각적인 부분은 저절로 수정됩니다.

### `singularity.log`에 불필요한 정보가 너무 많음
기본적으로 `INFO`, `WARNING` 및 `ERROR` 메시지만 기록됩니다. `--verbose` 플래그는 `DEBUG` 출력(모든 HTTP 요청, 바이트 오프셋, 재시도 횟수)을 추가합니다. 적극적으로 디버깅할 때만 `--verbose`를 사용하세요.

### 알 수 없는 메시지와 함께 시작 시 "Fatal error" (치명적 오류) 발생
전체 트레이스백을 확인하려면 프로젝트 루트에 있는 `singularity.log`를 확인하세요.

### 다운로드 후 파일에 태그가 지정되지 않음
`config.json`에서 `tag_audio`가 `true`인지 확인하세요. 태깅은 MP3, FLAC 및 OGG 파일에만 적용됩니다. WAV 파일은 태깅되지 않습니다(표준 메타데이터 컨테이너가 없음).

---

## 📝 라이선스

MIT 라이선스 — 자세한 내용은 [LICENSE](LICENSE)를 참조하세요.

*Created by [Takoyune](https://github.com/takoyune)*
