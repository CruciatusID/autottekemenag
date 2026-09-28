import os
import sys
import json
import time
import re
import getpass
import difflib
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

def normalize_text(text: str) -> str:
    """Bersihkan teks untuk pencocokan yang fleksibel."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[\s\-_,./\\]+', ' ', text)
    return text.strip()

# Kata-kata umum / stop words yang sering muncul bersamaan di portal Kemenag
# Jangan biarkan kata-kata umum ini membuat dokumen yang berbeda dikira sama
STOP_WORDS = {
    "kemenag", "kementerian", "agama", "kabupaten", "kab", "tana", "toraja",
    "kantor", "tahun", "bulan", "thn", "bln",
    "oktober", "november", "desember", "januari", "februari", "maret",
    "april", "mei", "juni", "juli", "agustus", "september",
    "dokumen", "surat", "nomor", "no", "2024", "2025", "2026", "2027",
    "dan", "di", "ke", "dari", "pada", "untuk", "dengan"
}

def is_doc_type_match(target_perihal: str, candidate_perihal: str) -> bool:
    """Memeriksa apakah jenis dokumen cocok (misal Sertifikat KBC vs SKBK)."""
    t_norm = normalize_text(target_perihal)
    c_norm = normalize_text(candidate_perihal)
    
    doc_types = [
        "sertifikat kbc",
        "sertifikat mgmp",
        "sertifikat",
        "skbk",
        "skmt",
        "surat tugas",
        "surat keterangan",
        "surat pernyataan",
        "laporan kondisi barang",
        "laporan existing",
        "laporan",
        "jadwal",
        "usulan",
        "rekomendasi"
    ]
    
    for dt in doc_types:
        in_target = dt in t_norm
        in_candidate = dt in c_norm
        if in_target != in_candidate:
            return False
            
    return True

def calculate_match_score(target_perihal: str, candidate_perihal: str) -> float:
    """
    Menghitung skor kecocokan antara target dan kandidat perihal (0.0 - 1.0).
    Akurat, ketat, dan memprioritaskan kata pembeda (nama, bagian tugas, dll).
    """
    if not is_doc_type_match(target_perihal, candidate_perihal):
        return 0.0

    t_norm = normalize_text(target_perihal)
    c_norm = normalize_text(candidate_perihal)
    
    if not t_norm or not c_norm:
        return 0.0

    # 1. Kecocokan Sempurna (100% Persis)
    if t_norm == c_norm:
        return 1.0

    t_words = [w for w in t_norm.split() if len(w) > 1]
    c_words = [w for w in c_norm.split() if len(w) > 1]
    
    if not t_words or not c_words:
        return 0.0

    t_set = set(t_words)
    c_set = set(c_words)

    # 2. Kata-kata Pembeda (Distinctive Words: Nama orang, jenis sub-jadwal, dsb.)
    t_distinct = t_set - STOP_WORDS
    c_distinct = c_set - STOP_WORDS

    # Jika target memiliki kata pembeda, kata pembeda tersebut WAJIB cocok tinggi di kandidat
    if t_distinct:
        matched_distinct = t_distinct.intersection(c_set)
        distinct_ratio = len(matched_distinct) / len(t_distinct)
        # Jika kata kunci pembeda tidak ada di kandidat, tolak langsung (skor 0)
        if distinct_ratio < 0.80:
            return 0.0
            
    # 3. Hitung Jaccard similarity & Sequence similarity
    intersection = t_set.intersection(c_set)
    union = t_set.union(c_set)
    jaccard = len(intersection) / len(union) if union else 0.0
    seq_ratio = difflib.SequenceMatcher(None, t_norm, c_norm).ratio()
    
    final_score = (jaccard * 0.4) + (seq_ratio * 0.6)
    return round(final_score, 4)

def fetch_table_catalog(page, max_pages: int = 3) -> list:
    """
    Mengambil katalog data naskah langsung dari server portal TTE (100 item per halaman)
    sehingga seluruh dokumen naskah terindeks di memori dengan cepat dan 100% akurat.
    """
    all_rows = []
    try:
        # Set page length to 100
        with page.expect_response(lambda r: "data_index" in r.url and "length=100" in r.url, timeout=15000) as resp_info:
            page.evaluate("() => { $('.dataTables').DataTable().page.len(100).draw(); }")
            
        data = resp_info.value.json().get("data", [])
        all_rows.extend(data)
        
        # Jika total records lebih banyak dari 100 dan kita butuh halaman berikutnya
        records_total = resp_info.value.json().get("recordsTotal", 0)
        if records_total > 100 and max_pages > 1:
            pages_to_fetch = min(max_pages, (records_total // 100) + 1)
            for p_idx in range(1, pages_to_fetch):
                try:
                    with page.expect_response(lambda r: "data_index" in r.url and f"start={p_idx*100}" in r.url, timeout=10000) as next_resp:
                        page.evaluate(f"() => {{ $('.dataTables').DataTable().page({p_idx}).draw('page'); }}")
                    next_data = next_resp.value.json().get("data", [])
                    all_rows.extend(next_data)
                except Exception:
                    break
    except Exception as e:
        print(f"⚠️ Peringatan saat memuat katalog tabel: {e}")
        
    return all_rows

def get_target_files():
    """
    Mengumpulkan seluruh file target beserta kategori foldernya:
    (NON PNS, PNS KEMENAG, PNS PEMDA, PPPK Kemenag, PPPK PEMDA)
    """
    file_map = {}

    # 1. Pindai langsung dari struktur folder lokal di BASE_DIR
    for pdf in BASE_DIR.rglob("*.pdf"):
        if any(part.startswith(".") or part in ["__pycache__", "venv", "HASIL_DOWNLOAD_TTE"] or "backup" in part.lower() for part in pdf.parts):
            continue
        if pdf.name not in ["recorded_download.py", "Sertifikat_MGMP.pdf"]:
            parent_folder = pdf.parent.name if pdf.parent != BASE_DIR else "ROOT"
            file_map[pdf.name] = {
                "filename": pdf.name,
                "perihal": pdf.stem,
                "kategori": parent_folder
            }

    if HISTORY_UPLOAD_FILE.exists():
        try:
            with open(HISTORY_UPLOAD_FILE, "r", encoding="utf-8") as f:
                upload_hist = json.load(f)
                for item in upload_hist:
                    if isinstance(item, dict):
                        fn = item.get("filename")
                        if fn:
                            existing = file_map.get(fn, {})
                            local_kat = existing.get("kategori")
                            hist_kat = item.get("kategori")
                            chosen_kat = local_kat if (local_kat and local_kat != "ROOT") else (hist_kat or "LAINNYA")
                            file_map[fn] = {
                                "filename": fn,
                                "perihal": item.get("perihal", existing.get("perihal", Path(fn).stem)),
                                "kategori": chosen_kat
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

def run_batch_downloader():
    print("=" * 60)
    print(" 📥 TTE KEMENAG AUTO-DOWNLOADER (AKURAT & CEPAT) ")
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
        reset_choice = input("\n[?] Ingin RESET histori unduhan dan memeriksa ulang SEMUA file dari awal? (y/N): ").strip().lower()
        if reset_choice == "y":
            download_history = []
            save_download_history([])
            pending_download = target_files.copy()
            print(f"🔄 Histori direset! Seluruh {len(pending_download)} dokumen siap dicek kembali.")
        else:
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

    print("\n[?] KONFIRMASI AKUN:")
    input_email = input(f"👤 Akun NIP/Email (Tekan ENTER untuk '{email}'): ").strip()
    if input_email:
        email = input_email
        config["email"] = email
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    password = getpass.getpass("🔑 Masukkan Kata Sandi TTE: ")
    if not password:
        print("❌ Password tidak boleh kosong!")
        return

    with sync_playwright() as playwright:
        if is_headless:
            print("\n⚡ Menjalankan di latar belakang (Mode Senyap)...")
        else:
            print("\n🌐 Membuka browser Chrome...")

        browser = playwright.chromium.launch(headless=is_headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # 1. Login
        print("🔑 Melakukan Login ke TTE Kemenag...")
        page.goto("https://tte.kemenag.go.id/login", wait_until="networkidle")

        try:
            page.get_by_text("Admin SATKER").click()
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

        # 2. Buka Halaman Dokumen Diajukan & Indeks Katalog
        print("📑 Membuka Tabel Dokumen & Mengindeks Katalog Naskah...")
        page.goto("https://tte.kemenag.go.id/satker/dokumen/naskah/index/unggah", wait_until="networkidle")
        time.sleep(2)

        print("🔄 Mengambil data katalog naskah dari server TTE...")
        catalog_rows = fetch_table_catalog(page, max_pages=3)
        print(f"✅ Berhasil mengindeks {len(catalog_rows)} naskah dari sistem TTE.")

        success_download_count = 0
        waiting_sign_count = 0
        not_found_count = 0
        total_start_time = time.time()

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
                # 1. Cari kecocokan di katalog memori
                matched_candidates = []
                for row in catalog_rows:
                    cand_perihal = row.get("perihal_dokumen", "")
                    score = calculate_match_score(perihal, cand_perihal)
                    if score >= 0.80:
                        matched_candidates.append((row, score, cand_perihal))

                if not matched_candidates:
                    print(f"   ⚠️ Naskah belum ditemukan di sistem TTE.")
                    not_found_count += 1
                    continue

                # Urutkan berdasarkan skor tertinggi (score DESC)
                # Playwright/DataTable katalog urutan aslinya adalah kronologis (terbaru di atas)
                # Dengan sort key score, dokumen yang paling cocok 100% selalu diprioritaskan
                matched_candidates.sort(key=lambda x: x[1], reverse=True)

                best_score = matched_candidates[0][1]
                # Saring hanya kandidat terbaik dengan selisih skor <= 2%
                top_candidates = [c for c in matched_candidates if c[1] >= best_score - 0.02]

                # 2. Di antara kandidat terbaik, ambil yang statusnya FINAL (ambil yang terbaru)
                selected_row = None
                selected_score = 0
                selected_cand_perihal = ""
                selected_is_final = False
                selected_url = None
                selected_status = "Dalam Proses"

                for row, score, cand_perihal in top_candidates:
                    unduh_html = row.get("unduh", "")
                    status_html = row.get("status_dokumen", "")
                    is_final = "FINAL" in unduh_html or "Sukses" in status_html
                    
                    if is_final:
                        match_url = re.search(r'href="([^"]+)"', unduh_html)
                        if match_url:
                            selected_row = row
                            selected_score = score
                            selected_cand_perihal = cand_perihal
                            selected_is_final = True
                            selected_url = match_url.group(1)
                            selected_status = "FINAL"
                            break

                if not selected_is_final:
                    # Jika belum ada yang FINAL, ambil info naskah teratas dari kandidat terbaik
                    top_row, top_sc, top_perihal = top_candidates[0]
                    status_clean = re.sub(r'<[^>]+>', '', top_row.get("status_dokumen", "Dalam Proses")).strip()
                    waiting_sign_count += 1
                    print(f"   ⏳ Status: [BELUM FINAL] ({status_clean}) - Kecocokan: {top_sc*100:.0f}% -> Dilewati.")
                    continue

                # 3. Unduh dokumen FINAL
                clean_cand_name = re.sub(r'<[^>]+>', '', selected_cand_perihal).strip()
                print(f"   🎉 Status: [FINAL] -> Cocok: '{clean_cand_name}' ({selected_score*100:.0f}%) -> Mengunduh...")
                full_url = f"https://tte.kemenag.go.id{selected_url}" if selected_url.startswith("/") else selected_url
                
                target_filepath.parent.mkdir(parents=True, exist_ok=True)
                resp = context.request.get(full_url)
                
                if resp.status == 200 and len(resp.body()) > 500:
                    with open(target_filepath, "wb") as f:
                        f.write(resp.body())
                        
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
                    print(f"   ✅ Berhasil disimpan: {dest_info} ({target_filepath.stat().st_size / 1024:.1f} KB - ⏱️ {format_duration(file_elapsed)})")
                else:
                    print(f"   ❌ Gagal mengunduh file dari URL: {full_url}")

            except Exception as ex:
                print(f"   ❌ Gagal memproses: {ex}")
                time.sleep(1)

        total_elapsed = time.time() - total_start_time
        avg_speed = total_elapsed / len(pending_download) if pending_download else 0

        print("\n" + "=" * 60)
        print("🏁 REKAP PENGECEKAN & DOWNLOAD:")
        print(f"   - Berhasil Diunduh (Baru) : {success_download_count} file")
        print(f"   - Masih Menunggu TTE      : {waiting_sign_count} file")
        print(f"   - Belum Ditemukan di Web  : {not_found_count} file")
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
