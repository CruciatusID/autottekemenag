import os
import sys
import json
import time
import re
import getpass
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ==========================================
# KONFIGURASI DOWNLOADER TERARAH & KATEGORI
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "HASIL_DOWNLOAD_TTE"
CONFIG_FILE = BASE_DIR / "config.json"
HISTORY_UPLOAD_FILE = BASE_DIR / "upload_history.json"
HISTORY_DOWNLOAD_FILE = BASE_DIR / "download_history.json"

DEFAULT_EMAIL = "198906212022031002@kemenag.go.id"

def format_duration(seconds: float) -> str:
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours} jam {mins} menit {secs} detik"
    elif mins > 0:
        return f"{mins} menit {secs} detik"
    else:
        return f"{seconds:.1f} detik"

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def load_download_history():
    if HISTORY_DOWNLOAD_FILE.exists():
        try:
            with open(HISTORY_DOWNLOAD_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_download_history(hist):
    with open(HISTORY_DOWNLOAD_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2, ensure_ascii=False)

def get_target_files():
    """
    Mengumpulkan seluruh file target beserta kategori foldernya:
    (NON PNS, PNS KEMENAG, PNS PEMDA, PPPK Kemenag, PPPK PEMDA)
    """
    file_map = {} # filename -> {filename, perihal, kategori}

    # 1. Pindai langsung dari struktur folder lokal di BASE_DIR
    for pdf in BASE_DIR.rglob("*.pdf"):
        if any(part.startswith(".") or part in ["__pycache__", "venv", "HASIL_DOWNLOAD_TTE"] for part in pdf.parts):
            continue
        if pdf.name != "recorded_download.py":
            parent_folder = pdf.parent.name if pdf.parent != BASE_DIR else "ROOT"
            file_map[pdf.name] = {
                "filename": pdf.name,
                "perihal": pdf.stem,
                "kategori": parent_folder
            }

    # 2. Periksa upload_history.json jika ada data kategori tambahan
    if HISTORY_UPLOAD_FILE.exists():
        try:
            with open(HISTORY_UPLOAD_FILE, "r", encoding="utf-8") as f:
                upload_hist = json.load(f)
                for item in upload_hist:
                    if isinstance(item, dict):
                        fn = item.get("filename")
                        if fn:
                            file_map[fn] = {
                                "filename": fn,
                                "perihal": item.get("perihal", Path(fn).stem),
                                "kategori": item.get("kategori", file_map.get(fn, {}).get("kategori", "LAINNYA"))
                            }
                    elif isinstance(item, str) and item not in file_map:
                        file_map[item] = {
                            "filename": item,
                            "perihal": Path(item).stem,
                            "kategori": "LAINNYA"
                        }
        except Exception:
            pass

    return sorted(list(file_map.values()), key=lambda x: (x["kategori"], x["filename"]))

def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return cleaned if cleaned else "Dokumen_TTE"

def run_batch_downloader():
    print("=" * 60)
    print(" 📥 TTE KEMENAG AUTO-DOWNLOADER (KATEGORI: PNS / PPPK / NON PNS) ")
    print("=" * 60)

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Folder Utama Simpan: {DOWNLOAD_DIR.resolve()}")

    target_files = get_target_files()
    if not target_files:
        print("❌ Tidak ada daftar file target lokal / upload history yang ditemukan!")
        input("Tekan ENTER untuk keluar...")
        return

    download_history = load_download_history()
    downloaded_filenames = {h if isinstance(h, str) else h.get("filename") for h in download_history}

    pending_download = []
    for f in target_files:
        fn = f["filename"]
        kat = f["kategori"]
        target_path = DOWNLOAD_DIR / kat / fn
        flat_path = DOWNLOAD_DIR / fn
        if fn not in downloaded_filenames and not target_path.exists() and not flat_path.exists():
            pending_download.append(f)

    print(f"📋 Total Dokumen Target Milik Anda : {len(target_files)}")
    print(f"✅ Sudah Berhasil Diunduh         : {len(target_files) - len(pending_download)}")
    print(f"⏳ Yang Akan Dicek Statusnya      : {len(pending_download)}")
    print("-" * 60)

    if not pending_download:
        print("🎉 Semua dokumen target Anda sudah lengkap diunduh ke folder kategori masing-masing!")
        input("Tekan ENTER untuk keluar...")
        return

    # Pilihan Jumlah Dokumen
    print("\n[?] PILIH JUMLAH DOKUMEN UNTUK DICEK/DOWNLOAD:")
    print("    1. Tes 1 file saja (Mode Uji Coba)")
    print("    2. Tes 3 file")
    print("    3. Cek Semua Dokumen Antrean [Default]")
    print("    4. Tentukan jumlah dokumen sendiri")
    
    choice = input("\nPilih opsi [1/2/3/4] (Default: 3): ").strip() or "3"
    
    if choice == "1":
        pending_download = pending_download[:1]
        print(f"👉 Mode Uji Coba: Hanya mengecek 1 file ({pending_download[0]['filename']})")
    elif choice == "2":
        pending_download = pending_download[:3]
        print(f"👉 Mode Uji Coba: Mengecek {len(pending_download)} file")
    elif choice == "4":
        try:
            custom_count = int(input("Masukkan jumlah dokumen yang ingin dicek: ").strip())
            pending_download = pending_download[:custom_count]
            print(f"👉 Mengecek {len(pending_download)} dokumen")
        except ValueError:
            print("⚠️ Input tidak valid, mengecek 3 file untuk uji coba.")
            pending_download = pending_download[:3]
    else:
        print(f"👉 Mode Penuh: Mengecek seluruh {len(pending_download)} dokumen antrean")

    # Pilihan Struktur Folder
    print("\n[?] PILIH STRUKTUR FOLDER PENYIMPANAN:")
    print("    1. Simpan Langsung di 1 Folder Utama (Tanpa Subfolder Kategori) [Default]")
    print("    2. Pisahkan Otomatis ke Subfolder Kategori (NON PNS, PPPK, PNS, dll)")
    folder_choice = input("\nPilih opsi struktur [1/2] (Default: 1): ").strip() or "1"
    use_subfolders = (folder_choice == "2")

    if use_subfolders:
        print("👉 Menyimpan ke Subfolder Kategori masing-masing.")
    else:
        print("👉 Menyimpan langsung di folder utama HASIL_DOWNLOAD_TTE.")

    print("-" * 60)

    # Pilihan Tampilan
    print("\n[?] PILIH TAMPILAN:")
    print("    1. Mode Senyap (Murni di Terminal / Tanpa Jendela Browser) [Default]")
    print("    2. Mode Visual (Tampilkan Jendela Browser)")
    view_choice = input("\nPilih opsi tampilan [1/2] (Default: 1): ").strip() or "1"
    is_headless = (view_choice != "2")

    config = load_config()
    email = config.get("email") or DEFAULT_EMAIL
    password = config.get("password")

    print("\n[?] KONFIRMASI AKUN:")
    input_email = input(f"👤 Akun NIP/Email (Tekan ENTER untuk '{email}'): ").strip()
    if input_email:
        email = input_email
        config["email"] = email
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    if not password:
        password = getpass.getpass("🔑 Masukkan Kata Sandi TTE: ")
        if not password:
            print("❌ Password tidak boleh kosong!")
            return

    with sync_playwright() as playwright:
        if is_headless:
            print("\n⚡ Menjalankan pengecekan di latar belakang (Mode Senyap)...")
        else:
            print("\n🌐 Membuka browser Chrome...")

        browser = playwright.chromium.launch(headless=is_headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # 1. Login
        print("🔑 Melakukan Login ke TTE Kemenag...")
        page.goto("https://tte.kemenag.go.id/login", wait_until="networkidle")

        try:
            page.get_by_role("radio", name="Admin SATKER").check()
            page.get_by_role("textbox", name="Masukkan Email").fill(email)
            page.get_by_role("textbox", name="Masukkan Kata Sandi").fill(password)
            page.get_by_role("button", name="Masuk").click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Terjadi kesalahan saat form login: {e}")

        if "login" in page.url:
            print("⚠️ Menunggu login selesai...")
            page.wait_for_url("**/satker**", timeout=60000)

        print("✅ Berhasil Login!")

        # 2. Buka Halaman Dokumen Diajukan
        print("📑 Membuka Tabel Dokumen Diajukan...")
        page.goto("https://tte.kemenag.go.id/satker/dokumen/naskah/index/unggah", wait_until="networkidle")
        time.sleep(2)

        success_download_count = 0
        waiting_sign_count = 0
        total_start_time = time.time()

        search_input = page.locator("input[type='search']").first

        for idx, item in enumerate(pending_download, 1):
            file_start_time = time.time()
            filename = item["filename"]
            perihal = item["perihal"]
            kategori = item["kategori"]

            if use_subfolders:
                kategori_dir = DOWNLOAD_DIR / kategori
                kategori_dir.mkdir(parents=True, exist_ok=True)
                target_filepath = kategori_dir / filename
            else:
                target_filepath = DOWNLOAD_DIR / filename

            print(f"\n[{idx}/{len(pending_download)}] 🔍 [{kategori}] Mencari: {perihal}")

            try:
                if search_input.count() > 0:
                    search_input.fill(perihal)
                    time.sleep(1.5) # Tunggu filter AJAX tabel selesai
                
                rows = page.locator("table tbody tr")
                if rows.count() == 0 or "tidak ditemukan" in rows.first.inner_text().lower():
                    print(f"   ⚠️ Naskah belum ditemukan di sistem TTE.")
                    continue

                matched_row = rows.first
                final_link = matched_row.locator("a:has-text('FINAL'), a.btn:has-text('FINAL')").first

                if final_link.count() > 0 and final_link.is_visible():
                    print(f"   🎉 Status: [FINAL] -> Mengunduh ke [{kategori}]...")
                    download_url = final_link.get_attribute("href")

                    downloaded = False
                    if download_url and not download_url.startswith("javascript"):
                        if download_url.startswith("/"):
                            full_url = f"https://tte.kemenag.go.id{download_url}"
                        else:
                            full_url = download_url

                        try:
                            resp = context.request.get(full_url)
                            if resp.status == 200:
                                with open(target_filepath, "wb") as f:
                                    f.write(resp.body())
                                downloaded = True
                        except Exception:
                            pass

                    if not downloaded:
                        with page.expect_download(timeout=10000) as download_info:
                            final_link.click()
                        download = download_info.value
                        download.save_as(str(target_filepath))
                        downloaded = True

                    if downloaded:
                        file_elapsed = time.time() - file_start_time
                        success_download_count += 1
                        history_entry = {
                            "filename": filename,
                            "perihal": perihal,
                            "kategori": kategori,
                            "waktu_download": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        download_history.append(history_entry)
                        downloaded_filenames.add(filename)
                        save_download_history(download_history)
                        dest_info = f"{kategori}/{filename}" if use_subfolders else filename
                        print(f"   ✅ Berhasil disimpan: {dest_info} (⏱️ {format_duration(file_elapsed)})")
                else:
                    waiting_sign_count += 1
                    status_col = matched_row.locator("td").nth(4).inner_text().strip() if matched_row.locator("td").count() >= 5 else "Dalam Proses"
                    print(f"   ⏳ Status: [BELUM FINAL] ({status_col}) -> Dilewati.")

            except Exception as ex:
                print(f"   ❌ Gagal memproses baris ini: {ex}")
                time.sleep(1)

        total_elapsed = time.time() - total_start_time
        avg_speed = total_elapsed / len(pending_download) if pending_download else 0

        print("\n" + "=" * 60)
        print("🏁 REKAP PENGECEKAN & DOWNLOAD:")
        print(f"   - Berhasil Diunduh (Baru) : {success_download_count} file")
        print(f"   - Masih Menunggu TTE      : {waiting_sign_count} file")
        print(f"   - Total File di Histori   : {len(download_history)} file")
        print(f"   - ⏱️ Total Waktu Proses   : {format_duration(total_elapsed)}")
        if len(pending_download) > 0:
            print(f"   - ⚡ Rata-rata/Dokumen    : {avg_speed:.1f} detik/file")
        print(f"   - Lokasi Penyimpanan      : {DOWNLOAD_DIR.resolve()}")
        print("=" * 60)

        context.close()
        browser.close()

if __name__ == "__main__":
    run_batch_downloader()
