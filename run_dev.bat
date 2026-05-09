@echo off
setlocal

cd /d "%~dp0"

echo [1/4] Resolving Python interpreter...
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [2/4] Checking Python...
"%PYTHON_EXE%" --version >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python is not available.
    echo Install Python or create .venv first.
    pause
    exit /b 1
)

echo [3/4] Preparing database if missing...
if not exist "campus_trading.db" (
    echo Database not found. Running init_db.py...
    "%PYTHON_EXE%" init_db.py
    if errorlevel 1 (
        echo ERROR: Database initialization failed.
        pause
        exit /b 1
    )
)

echo [4/4] Starting app at http://127.0.0.1:12000 ...
start "" "http://127.0.0.1:12000"
"%PYTHON_EXE%" app.py

if errorlevel 1 (
    echo.
    echo App exited with error.
    pause
)
