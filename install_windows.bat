@echo off
rem Install dependencies for Still Life Generator on Windows.
setlocal
cd /d "%~dp0"

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"

if not defined PY (
    echo.
    echo ERROR: Python not found. Install Python 3.10+ from https://python.org
    echo Make sure to tick "Add python.exe to PATH" during installation.
    echo.
    pause
    exit /b 1
)

set "TORCH_INDEX=https://download.pytorch.org/whl/cpu"
nvidia-smi >nul 2>nul
if not errorlevel 1 (
    echo NVIDIA GPU detected - installing CUDA build.
    set "TORCH_INDEX=https://download.pytorch.org/whl/cu130"
) else (
    echo No NVIDIA GPU detected - installing CPU build.
)
rem Override with:  set TORCH_INDEX=<url> then run this script

echo Creating virtual environment (.venv)...
if not exist ".venv\Scripts\python.exe" (
    %PY% -m venv .venv
    if errorlevel 1 exit /b 1
)

call ".venv\Scripts\activate.bat"

echo Installing Python packages...
python -m pip install --upgrade pip
python -m pip install torch --index-url %TORCH_INDEX%
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Installation failed. See the error message above.
    pause
    exit /b 1
)

echo.
echo Done! Launch the app with: run.bat
echo.
echo The app auto-detects your GPU and shows it in the top-right corner
echo of the window (GPU / CPU dropdown).
pause
