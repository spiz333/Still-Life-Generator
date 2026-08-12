@echo off
setlocal
cd /d "%~dp0"
if not exist "outputs" mkdir "outputs"

rem Keep the AI model in this project's .huggingface\ folder.
set "HF_HOME=%~dp0.huggingface"

set "PY="
set "PYARGS="
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul && set "PY=python"
    if not defined PY where py >nul 2>nul && (set "PY=py" & set "PYARGS=-3")
)

if not defined PY (
    echo Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

rem Check that the required dependencies are installed.
"%PY%" %PYARGS% -c "import diffusers, torch, PIL, tkinter" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Dependencies are missing.
    echo.
    echo Install them first (one time only), then run this script again:
    echo   Windows:  install_windows.bat
    echo   Linux:    ./install_linux.sh
    echo   macOS:    ./install_mac.sh
    echo.
    echo Note: if you installed Python dependencies globally, this script
    echo will automatically pick them up and the .venv folder can be deleted.
    pause
    exit /b 1
)

"%PY%" %PYARGS% "%~dp0still_life_gui.py"
if errorlevel 1 pause
