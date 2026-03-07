@echo off
title Installing ASMR Downloader Ultimate...
echo Creating Virtual Environment...
python -m venv venv

echo.
echo Installing Requirements (This might take a minute)...
call venv\Scripts\activate
pip install -r requirements.txt

echo.
echo Installation Complete!
echo You can now click START.bat
pause