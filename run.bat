@echo off
cd /d "%~dp0"
if exist "C:\Users\storm\AppData\Local\Programs\Python\Python311\python.exe" (
    start "" "C:\Users\storm\AppData\Local\Programs\Python\Python311\python.exe" "%~dp0still_life_gui.py"
) else (
    start "" python "%~dp0still_life_gui.py"
)
