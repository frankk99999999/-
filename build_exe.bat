@echo off
setlocal

cd /d "%~dp0"

echo [1/4] Checking pyinstaller...
where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo ERROR: pyinstaller is not installed or not in PATH.
    echo Please run: pip install pyinstaller
    pause
    exit /b 1
)

echo [2/4] Cleaning old build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
for %%f in ("*.spec") do (
    if exist "%%~nf" rmdir /s /q "%%~nf"
)

set "SPEC_FILE="
for %%f in (*.spec) do (
    if not defined SPEC_FILE (
        set "SPEC_FILE=%%f"
    ) else (
        echo ERROR: Multiple .spec files found. Keep only one or edit build_exe.bat.
        pause
        exit /b 1
    )
)

if not defined SPEC_FILE (
    echo ERROR: No .spec file found in current directory.
    pause
    exit /b 1
)

echo [3/4] Building executable from spec: %SPEC_FILE%
pyinstaller --clean "%SPEC_FILE%"
if errorlevel 1 (
    echo.
    echo BUILD FAILED.
    pause
    exit /b 1
)

echo [4/4] Build finished.
echo Output folder: dist\校园二手交易平台
pause
