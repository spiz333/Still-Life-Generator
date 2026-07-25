@echo off
cd /d "%~dp0"
if not exist "outputs" mkdir "outputs"
python "%~dp0still_life_gui.py" 2>nul || py -3 "%~dp0still_life_gui.py" 2>nul || python3 "%~dp0still_life_gui.py"
if errorlevel 1 (
    echo Python not found. Install Python 3.10+ from https://python.org
    pause
)
