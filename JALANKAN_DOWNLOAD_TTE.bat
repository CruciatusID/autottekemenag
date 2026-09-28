@echo off
title TTE Kemenag Auto-Downloader
cd /d "%~dp0"

:: ==========================================
:: Deteksi Interpreter Python Otomatis
:: ==========================================
set "PYTHON_CMD="
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
) else if exist "C:\Users\Ande\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PYTHON_CMD=C:\Users\Ande\AppData\Local\Programs\Python\Python313\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    ) else (
        where py >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=py"
    )
)

echo ===================================================
echo    Menjalankan TTE Kemenag Batch Auto-Downloader
echo ===================================================

if not defined PYTHON_CMD (
    echo [ERROR] Python tidak ditemukan di sistem!
    echo Silakan jalankan INSTALL_DEPENDENCIES.bat terlebih dahulu.
    echo.
    pause
    exit /b 1
)

"%PYTHON_CMD%" tte_batch_downloader.py
echo.
pause
