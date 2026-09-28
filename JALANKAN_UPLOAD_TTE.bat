@echo off
title TTE Kemenag Auto-Uploader
cd /d "%~dp0"

:menu
cls
echo ===================================================
echo       TTE Kemenag Batch Auto-Uploader Menu
echo ===================================================

if exist upload_history.json (
    echo Status Histori : [Tersedia] Ada file yang sudah diupload.
) else (
    echo Status Histori : [Kosong] Belum ada file histori.
)

echo ===================================================
echo 1. Jalankan Auto-Uploader
echo 2. Lihat List File yang Sudah Diupload
echo 3. Reset Histori Upload (Mulai dari awal)
echo 4. Keluar
echo ===================================================
set /p pilihan="Pilih menu (1/2/3/4): "

if "%pilihan%"=="1" goto jalankan
if "%pilihan%"=="2" goto lihat
if "%pilihan%"=="3" goto reset
if "%pilihan%"=="4" goto exit

goto menu

:jalankan
cls
echo ===================================================
echo     Menjalankan TTE Kemenag Batch Auto-Uploader
echo ===================================================
"C:\Users\Ande\AppData\Local\Programs\Python\Python313\python.exe" tte_batch_uploader.py
echo.
pause
goto menu

:lihat
cls
echo ===================================================
echo     Daftar File yang Sudah Diupload
echo ===================================================

if not exist upload_history.json goto histori_kosong

echo import json > tmp_view.py
echo try: >> tmp_view.py
echo     with open('upload_history.json', encoding='utf-8') as f: >> tmp_view.py
echo         data = json.load(f) >> tmp_view.py
echo     if data: >> tmp_view.py
echo         for i, x in enumerate(data): >> tmp_view.py
echo             name = x.get('filename', x) if isinstance(x, dict) else x >> tmp_view.py
echo             print(f' - {i+1}. {name}') >> tmp_view.py
echo     else: >> tmp_view.py
echo         print(' Histori ada, tapi kosong.') >> tmp_view.py
echo except Exception as e: >> tmp_view.py
echo     print(' Error membaca data:', e) >> tmp_view.py

"C:\Users\Ande\AppData\Local\Programs\Python\Python313\python.exe" tmp_view.py
del tmp_view.py
goto lanjut_lihat

:histori_kosong
echo [INFO] Belum ada file histori (upload_history.json).

:lanjut_lihat
echo ===================================================
pause
goto menu

:reset
echo.
echo ===================================================
echo PERINGATAN: Apakah Anda yakin ingin mereset histori?
echo Semua file akan dianggap belum pernah diupload.
echo ===================================================
set /p konfirmasi="Ketik 'Y' untuk lanjut reset atau tombol lain untuk batal: "
if /I not "%konfirmasi%"=="Y" goto reset_batal

if not exist upload_history.json goto reset_kosong
del upload_history.json
echo [SUKSES] Histori upload berhasil dihapus/direset!
goto reset_selesai

:reset_kosong
echo [INFO] File histori (upload_history.json) belum ada atau sudah kosong.
goto reset_selesai

:reset_batal
echo [INFO] Reset dibatalkan.

:reset_selesai
echo.
pause
goto menu

:exit
exit
