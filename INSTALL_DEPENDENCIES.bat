@echo off
title Installer Dependensi TTE Kemenag Auto-Assistant
cd /d "%~dp0"
echo ========================================================
echo    Menginstal Dependensi & Browser Playwright Otomatis
echo ========================================================
echo.

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

if not defined PYTHON_CMD (
    echo [!] Python belum terdeteksi di sistem.
    echo     Silakan unduh dan pasang Python terlebih dahulu dari https://www.python.org/
    echo     (Pastikan centang "Add Python to PATH" saat instalasi).
    echo.
    pause
    exit /b 1
)

echo [*] Menggunakan interpreter: %PYTHON_CMD%
echo.
echo [*] Menginstal library playwright...
"%PYTHON_CMD%" -m pip install --upgrade pip
"%PYTHON_CMD%" -m pip install playwright

echo.
echo [*] Memasang browser engine Chromium...
"%PYTHON_CMD%" -m playwright install chromium

echo.
echo ========================================================
echo   [OK] SEMUA DEPENDENSI BERHASIL TERPASANG DENGAN SUKSES!
echo   Anda sekarang bisa menjalankan JALANKAN_UPLOAD_TTE.bat
echo ========================================================
pause
