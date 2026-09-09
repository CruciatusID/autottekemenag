import os
import sys
import json
import time
import re
import getpass
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ==========================================
# KONFIGURASI DEFAULT
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "upload_history.json"
CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_EMAIL = "198906212022031002@kemenag.go.id"
DEFAULT_PEMARAF = "Tamrin Lodo"
DEFAULT_SIGNERS = [
    {"nama": "Usman Senong", "anchor": "^"}
]
DEFAULT_JENIS_DOKUMEN = "Dokumen Lain-Lain"

def extract_anchors(anchor_input) -> list:
    """Ekstrak list anchor valid [^, #, $, *] dari input string, list, atau gabungan."""
    valid_symbols = ["^", "#", "$", "*"]
    if isinstance(anchor_input, list):
        res = []
        for a in anchor_input:
            for sub_a in extract_anchors(a):
                if sub_a not in res:
                    res.append(sub_a)
        return res if res else ["^"]
    elif isinstance(anchor_input, str):
        found = [ch for ch in anchor_input if ch in valid_symbols]
        return found if found else ["^"]
    return ["^"]

def normalize_signers(signers_raw: list) -> list:
    """
    Menggabungkan penandatangan dengan nama yang sama (case-insensitive)
    sehingga 1 penandatangan dapat memiliki multi-anchor sekaligus tanpa duplikasi baris di web.
    """
    grouped = {}
    for item in signers_raw:
        if isinstance(item, dict):
            name = item.get("nama", "").strip()
            anchor_val = item.get("anchor", item.get("anchors", "^"))
        elif isinstance(item, str):
            name = item.strip()
            anchor_val = "^"
        else:
            continue
        
        if not name:
            continue
            
        key = name.lower()
        anchors = extract_anchors(anchor_val)
        if key not in grouped:
            grouped[key] = {
                "nama": name,
                "anchors": []
            }
        for a in anchors:
            if a not in grouped[key]["anchors"]:
                grouped[key]["anchors"].append(a)
                
    result = []
    for g in grouped.values():
        if not g["anchors"]:
            g["anchors"] = ["^"]
        result.append(g)
    return result

def format_duration(seconds: float) -> str:
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours} jam {mins} menit {secs} detik"
    elif mins > 0:
        return f"{mins} menit {secs} detik"
    else:
        return f"{seconds:.1f} detik"

def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def get_all_pdf_files(base_path: Path, custom_path_str: str = None):
    scan_dir = base_path
    if custom_path_str:
        custom_path = Path(custom_path_str)
        if custom_path.exists() and custom_path.is_dir():
            scan_dir = custom_path

    files = []
    # Pindai seluruh file PDF di dalam folder dan seluruh subfoldernya secara otomatis
    for pdf in sorted(scan_dir.rglob("*.pdf")):
        # Abaikan file di folder tersembunyi / virtual env jika ada
        if any(part.startswith(".") or part in ["__pycache__", "venv", "env"] for part in pdf.parts):
            continue
            
        parent_name = pdf.parent.name if pdf.parent != scan_dir else "ROOT"
        files.append({
            "folder": parent_name,
            "filename": pdf.name,
            "perihal": pdf.stem, # nama file tanpa .pdf
            "path": str(pdf.resolve())
        })
    return files

def run_batch_uploader():
    print("=" * 60)
    print("      🚀 TTE KEMENAG BATCH AUTO-UPLOADER (STANDALONE)      ")
    print("=" * 60)

    # 1. Ambil Kredensial & Pengaturan
    config = load_config()
    custom_folder = config.get("folder_pdf")

    # Tanya / Konfirmasi Folder PDF
    if not custom_folder:
        folder_input = input(f"📁 Masukkan path folder PDF (Tekan ENTER untuk folder projek saat ini): ").strip().strip('"').strip("'")
        if folder_input:
            custom_folder = folder_input

    # 2. Kumpulkan file PDF
    all_files = get_all_pdf_files(BASE_DIR, custom_folder)
    if not all_files:
        print(f"❌ Tidak ditemukan file PDF di folder: {custom_folder or BASE_DIR}")
        input("Tekan ENTER untuk keluar...")
        return

    history = load_history()
    completed_filenames = {h if isinstance(h, str) else h.get("filename") for h in history}
    pending_files = [f for f in all_files if f["filename"] not in completed_filenames]

    print(f"📁 Total file PDF ditemukan : {len(all_files)}")
    print(f"✅ Sudah pernah diunggah    : {len(completed_filenames)}")
    print(f"⏳ Antrean yang akan diupload: {len(pending_files)}")
    print("-" * 60)

    if not pending_files:
        print("🎉 Semua file PDF sudah selesai diunggah sebelumnya!")
        reset_choice = input("\n[?] Ingin RESET histori dan mengunggah ulang SEMUA file dari awal? (y/N): ").strip().lower()
        if reset_choice == "y":
            history = []
            save_history([])
            pending_files = all_files.copy()
            print("🔄 Histori berhasil direset! Seluruh 66 file siap diunggah kembali.")
        else:
            print("👍 Selesai.")
            return

    # Pilihan Mode Uji Coba atau Penuh
    print("\n[?] PILIH JUMLAH FILE:")
    print("    1. Tes 1 file saja (Mode Uji Coba)")
    print("    2. Tes 2 file")
    print("    3. Proses Semua File Antrean")
    print("    4. Tentukan jumlah file sendiri")
    
    choice = input("\nPilih opsi [1/2/3/4] (Default: 3): ").strip() or "3"
    
    if choice == "1":
        pending_files = pending_files[:1]
        print(f"👉 Mode Uji Coba Aktif: Hanya memproses 1 file ({pending_files[0]['filename']})")
    elif choice == "2":
        pending_files = pending_files[:2]
        print(f"👉 Mode Uji Coba Aktif: Memproses 2 file ({', '.join(f['filename'] for f in pending_files)})")
    elif choice == "4":
        try:
            custom_count = int(input("Masukkan jumlah file yang ingin diproses: ").strip())
            pending_files = pending_files[:custom_count]
            print(f"👉 Memproses {len(pending_files)} file")
        except ValueError:
            print("⚠️ Input tidak valid, memproses 1 file untuk uji coba.")
            pending_files = pending_files[:1]
    else:
        print(f"👉 Mode Penuh Aktif: Memproses seluruh {len(pending_files)} file")

    print("-" * 60)

    # Pilihan Tampilan Jendela Browser (Mode Senyap / Visual)
    print("\n[?] PILIH TAMPILAN:")
    print("    1. Mode Senyap (Murni di Terminal / Tanpa Jendela Browser) [Default]")
    print("    2. Mode Visual (Tampilkan Jendela Browser)")
    view_choice = input("\nPilih opsi tampilan [1/2] (Default: 1): ").strip() or "1"
    is_headless = (view_choice != "2")

    if is_headless:
        print("👉 Mode Senyap Aktif: Browser berjalan di latar belakang (RAM).")
    else:
        print("👉 Mode Visual Aktif: Jendela browser akan terbuka di layar.")

    print("-" * 60)

    # 2. Ambil Kredensial & Pengaturan Pejabat
    config = load_config()
    email = config.get("email") or DEFAULT_EMAIL
    password = config.get("password")
    jenis_dokumen = config.get("jenis_dokumen") or DEFAULT_JENIS_DOKUMEN
    
    pemaraf_cfg = config.get("pemaraf")
    if isinstance(pemaraf_cfg, dict):
        pemaraf_name = pemaraf_cfg.get("nama", DEFAULT_PEMARAF)
    elif isinstance(pemaraf_cfg, str):
        pemaraf_name = pemaraf_cfg
    else:
        pemaraf_name = DEFAULT_PEMARAF

    signers_cfg = config.get("penandatangan")
    if isinstance(signers_cfg, list) and len(signers_cfg) > 0:
        signers = normalize_signers(signers_cfg)[:4] # Maksimal 4 penandatangan
    else:
        signers = normalize_signers(DEFAULT_SIGNERS)

    print("\n[?] KONFIRMASI AKUN & PEJABAT:")
    # Konfirmasi / Ubah Email Akun
    input_email = input(f"👤 Akun NIP/Email (Tekan ENTER untuk '{email}'): ").strip()
    if input_email:
        email = input_email

    # Konfirmasi / Ubah Pemaraf
    input_pemaraf = input(f"✍️  Nama Pemaraf (Tekan ENTER untuk '{pemaraf_name}'): ").strip()
    if input_pemaraf:
        pemaraf_name = input_pemaraf

    # Konfirmasi / Ubah Penandatangan
    signers_display = ", ".join([f"{s.get('nama')} (Anchor: {', '.join(s.get('anchors', ['^']))})" for s in signers])
    print(f"🖋️  Penandatangan saat ini: {signers_display}")
    ubah_signer = input("    Ingin ubah penandatangan? (y/N - Tekan ENTER jika sudah sesuai): ").strip().lower()
    
    if ubah_signer == "y":
        signers_raw = []
        anchors_avail = ["^", "#", "$", "*"]
        try:
            jml = int(input("    Berapa jumlah orang penandatangan (1-4)? ").strip() or "1")
            jml = max(1, min(4, jml))
        except ValueError:
            jml = 1

        for i in range(jml):
            def_anchor = anchors_avail[i] if i < len(anchors_avail) else "^"
            s_name = input(f"    - Nama Penandatangan ke-{i+1}: ").strip()
            s_anc = input(f"      Anchor [^, #, $, *] (Bisa lebih dari 1 cth: #, $ | Default: {def_anchor}): ").strip() or def_anchor
            if s_name:
                signers_raw.append({"nama": s_name, "anchor": s_anc})

        signers = normalize_signers(signers_raw)
        if not signers:
            signers = normalize_signers(DEFAULT_SIGNERS)

    # Simpan kembali ke config.json jika ada perubahan
    config["email"] = email
    config["pemaraf"] = {"nama": pemaraf_name}
    config["penandatangan"] = [
        {"nama": s["nama"], "anchor": s["anchors"] if len(s["anchors"]) > 1 else s["anchors"][0]}
        for s in signers
    ]
    config["jenis_dokumen"] = jenis_dokumen
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("-" * 60)
    print(f"👤 Akun NIP/Email    : {email}")
    print(f"📑 Jenis Dokumen     : {jenis_dokumen}")
    print(f"✍️  Pemaraf          : {pemaraf_name}")
    print(f"🖋️  Penandatangan ({len(signers)} Orang):")
    for s_idx, s in enumerate(signers, 1):
        anc_str = ", ".join(s.get("anchors", ["^"]))
        print(f"    {s_idx}. {s.get('nama')} [Anchor: {anc_str}]")
    print("-" * 60)

    if not password:
        password = getpass.getpass("\n🔑 Masukkan Kata Sandi TTE: ")
        if not password:
            print("❌ Password tidak boleh kosong!")
            return

    # 3. Jalankan Playwright
    with sync_playwright() as playwright:
        if is_headless:
            print("\n⚡ Menjalankan engine otomatisasi di latar belakang (Mode Senyap)...")
        else:
            print("\n🌐 Membuka browser Chrome...")

        browser = playwright.chromium.launch(headless=is_headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Step Login
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

        # 4. Loop Unggah Setiap File
        success_count = 0
        failed_count = 0
        total_start_time = time.time()

        for idx, item in enumerate(pending_files, 1):
            file_start_time = time.time()
            filename = item["filename"]
            filepath = item["path"]
            perihal = item["perihal"]
            folder = item["folder"]

            print(f"\n[{idx}/{len(pending_files)}] 📄 Memproses: [{folder}] {filename}")

            try:
                # 1. Buka Halaman Create Naskah
                page.goto("https://tte.kemenag.go.id/satker/dokumen/naskah/create", wait_until="networkidle")
                time.sleep(1)

                # 2. Pilih Jenis Dokumen
                try:
                    page.locator(".select2-selection").first.click()
                    time.sleep(0.3)
                    page.get_by_role("treeitem", name=jenis_dokumen).click()
                except Exception:
                    pass

                time.sleep(0.5)

                # 3. Upload File PDF
                file_input = page.locator("input[type='file'][name='path_dokumen']")
                if not file_input.count():
                    file_input = page.locator("input[type='file']")
                file_input.set_input_files(filepath)

                # 4. Isi Perihal Dokumen
                page.get_by_role("textbox", name="Perihal Dokumen").fill(perihal)
                time.sleep(0.5)

                # 5. Klik Tombol Lanjut (Tahap 1 -> Tahap 2)
                page.get_by_role("button", name="Lanjut ").click()
                page.wait_for_url("**/create_step_two**", timeout=15000)
                time.sleep(1)

                # 6. Tahap 2: Tambah 1 Pemaraf
                print(f"   🔍 Memilih Pemaraf: {pemaraf_name}...")
                page.get_by_text("Cari Pegawai").click()
                time.sleep(0.3)
                search_box = page.locator("input.select2-search__field").first
                search_box.fill(pemaraf_name)
                time.sleep(2) # Tunggu AJAX response
                
                # Coba cari yang cocok dengan teks, jika tidak cocok (misal cari via NIP), pilih hasil pertama
                matched_pemaraf = page.locator(".select2-results__option").filter(has_text=re.compile(re.escape(pemaraf_name), re.IGNORECASE))
                if matched_pemaraf.count() > 0:
                    matched_pemaraf.first.click()
                else:
                    first_opt = page.locator(".select2-results__option:not(.select2-results__message)").first
                    first_opt.click()

                time.sleep(0.5)

                page.get_by_role("button", name="Tambah Pemaraf").click()
                time.sleep(1.5)
                page.wait_for_load_state("networkidle")
                
                # Klik Lanjut menuju step three
                page.get_by_role("link", name="Lanjut ").click()
                page.wait_for_url("**/create_step_three**", timeout=15000)
                time.sleep(1)

                # 7. Tahap 3: Tambah Penandatangan (Dukungan Multi-Anchor per Penandatangan)
                for s_num, signer_obj in enumerate(signers, 1):
                    signer_name = signer_obj.get("nama", "").strip()
                    anchor_symbols = signer_obj.get("anchors", ["^"])
                    if isinstance(anchor_symbols, str):
                        anchor_symbols = extract_anchors(anchor_symbols)

                    anc_display = ", ".join(anchor_symbols)
                    print(f"   🔍 [{s_num}/{len(signers)}] Memilih Penandatangan: {signer_name} (Anchor: {anc_display})...")
                    page.get_by_text("Cari Pegawai").click()
                    time.sleep(0.3)
                    search_box = page.locator("input.select2-search__field").first
                    search_box.fill(signer_name)
                    time.sleep(2) # Tunggu AJAX response

                    # Coba klik opsi yang cocok teks, jika via NIP pilih hasil pertama
                    matched_signer = page.locator(".select2-results__option").filter(has_text=re.compile(re.escape(signer_name), re.IGNORECASE))
                    if matched_signer.count() > 0:
                        matched_signer.first.click()
                    else:
                        first_opt = page.locator(".select2-results__option:not(.select2-results__message)").first
                        first_opt.click()

                    time.sleep(0.8)

                    # Set Nilai Anchor via Javascript / Selectpicker
                    try:
                        page.evaluate(
                            """(anchors) => {
                                const sel = document.getElementById("anchor") || document.querySelector("select[name='anchor[]']") || document.querySelector("select[name='anchor']");
                                if (sel) {
                                    for (let opt of sel.options) {
                                        const val = (opt.value || "").trim();
                                        const txt = (opt.text || "").trim();
                                        opt.selected = anchors.includes(val) || anchors.includes(txt);
                                    }
                                    sel.dispatchEvent(new Event("change", { bubbles: true }));
                                    if (window.$ && $(sel).selectpicker) {
                                        $(sel).selectpicker("val", anchors);
                                        $(sel).selectpicker("render");
                                        $(sel).trigger("change");
                                    }
                                }
                            }""",
                            anchor_symbols
                        )
                    except Exception:
                        pass

                    time.sleep(0.5)

                    # Trigger UI jika belum tercentang
                    try:
                        anchor_btn = page.locator("button[data-id='anchor'], .bootstrap-select button").first
                        if anchor_btn.is_visible():
                            anchor_text = anchor_btn.inner_text().strip()
                            if any(a not in anchor_text for a in anchor_symbols):
                                anchor_btn.click()
                                time.sleep(0.4)
                                for a in anchor_symbols:
                                    item = page.locator(".dropdown-menu.show a, .bootstrap-select .dropdown-menu a, .dropdown-menu.show li, .bootstrap-select .dropdown-menu li").filter(has_text=re.compile(rf"^\s*{re.escape(a)}\s*$")).first
                                    if item.is_visible():
                                        is_selected = item.evaluate("el => (el.closest('li') ? el.closest('li').classList.contains('selected') : el.classList.contains('selected'))")
                                        if not is_selected:
                                            item.click()
                                            time.sleep(0.3)
                                page.keyboard.press("Escape")
                                time.sleep(0.3)
                    except Exception:
                        pass

                    time.sleep(0.5)

                    # Klik Tambah Penandatangan (1 kali untuk seluruh anchor orang ini)
                    page.get_by_role("button", name="Tambah Penandatangan").click()
                    time.sleep(2)
                    page.wait_for_load_state("networkidle")

                # 8. Selesai Semua Penandatangan
                print("   🏁 Mengklik tombol Selesai...")
                selesai_btn = page.locator("button:has-text('Selesai'), button.btn-success:has-text('Selesai')").first
                selesai_btn.click()
                
                # Tunggu redirect kembali ke tabel naskah
                page.wait_for_url("**/satker/dokumen/naskah/index/**", timeout=20000)
                time.sleep(1)

                # Catat histori sukses dengan kategori folder
                history_entry = {
                    "filename": filename,
                    "perihal": perihal,
                    "kategori": folder,
                    "waktu": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                # Support backwards compatibility
                if filename not in [h if isinstance(h, str) else h.get("filename") for h in history]:
                    history.append(history_entry)
                    save_history(history)

                file_elapsed = time.time() - file_start_time
                success_count += 1
                print(f"   ✅ Berhasil diunggah dan diverifikasi! [{folder}] (⏱️ {format_duration(file_elapsed)})")

            except PlaywrightTimeoutError as te:
                print(f"   ❌ Gagal (Timeout): {te}")
                failed_count += 1
                time.sleep(2)
            except Exception as ex:
                print(f"   ❌ Gagal: {ex}")
                failed_count += 1
                time.sleep(2)

        total_elapsed = time.time() - total_start_time
        avg_speed = total_elapsed / len(pending_files) if pending_files else 0

        print("\n" + "=" * 60)
        print(f"🏁 PROSES SELESAI!")
        print(f"   - Berhasil           : {success_count} file")
        print(f"   - Gagal              : {failed_count} file")
        print(f"   - Total di Histori   : {len(history)} file")
        print(f"   - ⏱️ Total Waktu     : {format_duration(total_elapsed)}")
        if success_count > 0:
            print(f"   - ⚡ Rata-rata/File  : {avg_speed:.1f} detik/file")
        print("=" * 60)

        context.close()
        browser.close()

if __name__ == "__main__":
    run_batch_uploader()
