@echo off
title Perekam Langkah TTE Kemenag (Playwright Codegen)
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
echo   Membuka Browser Perekam Langkah TTE Kemenag...
echo ===================================================
echo.
echo Silakan login dan lakukan pencarian naskah / download di browser.
echo Semua aksi dan selector tombol akan otomatis tercatat ke recorded_download.py.
echo.

if not defined PYTHON_CMD (
    echo [ERROR] Python tidak ditemukan di sistem!
    echo Silakan jalankan INSTALL_DEPENDENCIES.bat terlebih dahulu.
    echo.
    pause
    exit /b 1
)

"%PYTHON_CMD%" -m playwright codegen https://tte.kemenag.go.id/login -o recorded_download.py
echo.
echo Selesai merekam! File recorded_download.py berhasil dibuat.
pause
