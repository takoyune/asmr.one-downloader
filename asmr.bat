@echo off
setlocal
title ASMR Manager X - Launcher
cd /d "%~dp0"

:: Cek apakah venv ada
if not exist "venv" (
    echo [INFO] First setup detected.
    echo Creating Environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

:: Jalankan
python main.py
if %errorlevel% neq 0 pause