@echo off
title Perekam Langkah TTE Kemenag (Playwright Codegen)
cd /d "%~dp0"
echo ===================================================
echo   Membuka Browser Perekam Langkah TTE Kemenag...
echo ===================================================
echo.
echo Silakan login dan lakukan pencarian naskah / download di browser.
echo Semua aksi dan selector tombol akan otomatis tercatat ke recorded_download.py.
echo.
"C:\Users\Ande\AppData\Local\Programs\Python\Python313\python.exe" -m playwright codegen https://tte.kemenag.go.id/login -o recorded_download.py
echo.
echo Selesai merekam! File recorded_download.py berhasil dibuat.
pause
