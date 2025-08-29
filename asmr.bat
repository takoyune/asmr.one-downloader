@echo off
setlocal EnableDelayedExpansion

:: Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH. Please install Python and add it to PATH.
    exit /b 1
)

:: Check if asmr.py exists
if not exist "C:\ASMR\asmr.py" (
    echo asmr.py not found in C:\ASMR. Please ensure the script is in the correct directory.
    exit /b 1
)

:: Set working directory to C:\ASMR
cd /d C:\ASMR

:: Run asmr.py with provided arguments
echo Running asmr.py...
python asmr.py %*
if %ERRORLEVEL% neq 0 (
    echo An error occurred while running asmr.py. Check the script or input arguments.
    exit /b 1
)

echo asmr.py completed.
exit /b 0