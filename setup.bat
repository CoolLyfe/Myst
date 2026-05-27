@echo off
setlocal enabledelayedexpansion

echo ====================================
echo    Myst Game Setup (Windows)
echo ====================================

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed.
    echo Please install Python 3.10 or newer from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/4] Python detected.

:: 2. Create Virtual Environment
echo [2/4] Creating virtual environment (.venv)...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

:: 3. Install Dependencies
echo [3/4] Installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet

:: Install requirements
:: ffpyplayer and pymediainfo usually have wheels for Windows
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies failed to install.
    echo The game might still run, but features like videos might be disabled.
)

:: 4. Create Launcher Script
echo [4/4] Creating launcher (Myst.bat)...
(
echo @echo off
echo cd /d "%%~dp0"
echo call .venv\Scripts\activate.bat
echo cd game
echo python menu.py
) > Myst.bat

echo ====================================
echo    Setup Complete
echo ====================================
echo You can now start the game by running: Myst.bat
pause
