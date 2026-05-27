@echo off
setlocal enabledelayedexpansion

echo ====================================
echo    Myst Game Uninstaller (Windows)
echo ====================================

:: 1. Remove Virtual Environment
if exist ".venv" (
    echo [1/3] Removing virtual environment (.venv)...
    rmdir /s /q .venv
    echo Virtual environment removed.
) else (
    echo [1/3] Virtual environment not found, skipping.
)

:: 2. Remove Launcher
if exist "Myst.bat" (
    echo [2/3] Removing game launcher (Myst.bat)...
    del Myst.bat
    echo Launcher removed.
) else (
    echo [2/3] Launcher not found, skipping.
)

:: 3. Clean up __pycache__
echo [3/3] Cleaning up __pycache__ folders...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo ====================================
echo    Uninstallation Complete
echo ====================================
pause
