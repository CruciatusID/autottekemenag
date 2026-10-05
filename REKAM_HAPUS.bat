@echo off
title Inspeksi Hapus Permanen Naskah TTE Kemenag
cd /d "%~dp0"

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
echo   Perekam / Inspeksi Aksi Hapus Permanen Naskah
echo ===================================================

if not defined PYTHON_CMD (
    echo [ERROR] Python tidak ditemukan di sistem!
    pause
    exit /b 1
)

"%PYTHON_CMD%" inspeksi_hapus.py
echo.
pause
