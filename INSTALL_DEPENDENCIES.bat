@echo off
title Installer Dependensi TTE Kemenag Auto-Assistant
cd /d "%~dp0"
echo ========================================================
echo    Menginstal Dependensi & Browser Playwright Otomatis
echo ========================================================
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python belum terdeteksi di sistem.
    echo     Silakan unduh dan pasang Python terlebih dahulu dari https://www.python.org/
    echo     (Pastikan centang "Add Python to PATH" saat instalasi).
    echo.
    pause
    exit /b
)

echo [*] Menginstal library playwright...
python -m pip install --upgrade pip
python -m pip install playwright

echo.
echo [*] Memasang browser engine Chromium...
python -m playwright install chromium

echo.
echo ========================================================
echo   [OK] SEMUA DEPENDENSI BERHASIL TERPASANG DENGAN SUKSES!
echo   Anda sekarang bisa menjalankan JALANKAN_UPLOAD_TTE.bat
echo ========================================================
pause
