import json
import time
import getpass
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"
HISTORY_UPLOAD_FILE = BASE_DIR / "upload_history.json"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def fetch_table_catalog(page, max_pages: int = 5) -> list:
    """Mengambil katalog naskah terbaru untuk mendapatkan ID dokumen"""
    all_rows = []
    try:
        with page.expect_response(lambda r: "data_index" in r.url and "length=100" in r.url, timeout=15000) as resp_info:
            page.evaluate("() => { $('.dataTables').DataTable().page.len(100).draw(); }")
            
        data = resp_info.value.json().get("data", [])
        all_rows.extend(data)
        
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

def main():
    print("=" * 60)
    print(" 🗑️ TTE KEMENAG BATCH AUTO-CANCELER (PEMBATAL NASKAH) ")
    print("=" * 60)

    if not HISTORY_UPLOAD_FILE.exists():
        print("❌ File upload_history.json tidak ditemukan!")
        return

    with open(HISTORY_UPLOAD_FILE, "r", encoding="utf-8") as f:
        upload_hist = json.load(f)

    print(f"📋 Ditemukan {len(upload_hist)} riwayat dokumen di antrean pembatalan.")
    print("\n[?] PILIH JUMLAH DOKUMEN YANG AKAN DIBATALKAN:")
    print("    1. Tes batalkan 1 dokumen saja (Mode Uji Coba)")
    print("    2. Tes batalkan 2 dokumen")
    print("    3. Batalkan Semua Dokumen [Default]")
    print("    4. Tentukan jumlah sendiri")
    
    choice = input("\nPilih opsi [1/2/3/4] (Default: 3): ").strip() or "3"
    
    if choice == "1":
        upload_hist = upload_hist[:1]
        print(f"👉 Mode Uji Coba: Hanya membatalkan 1 dokumen")
    elif choice == "2":
        upload_hist = upload_hist[:2]
        print(f"👉 Mode Uji Coba: Membatalkan 2 dokumen")
    elif choice == "4":
        try:
            custom_count = int(input("Masukkan jumlah dokumen yang ingin dibatalkan: ").strip())
            upload_hist = upload_hist[:custom_count]
            print(f"👉 Membatalkan {len(upload_hist)} dokumen")
        except ValueError:
            print("⚠️ Input tidak valid, membatalkan 1 dokumen untuk uji coba.")
            upload_hist = upload_hist[:1]
    else:
        print(f"👉 Mode Penuh: Membatalkan seluruh {len(upload_hist)} dokumen")

    konfirmasi = input("\nYakin ingin melanjutkan proses pembatalan? (y/N): ").strip().lower()
    if konfirmasi != 'y':
        print("Dibatalkan.")
        return

    config = load_config()
    email = config.get("email", "")
    input_email = input(f"👤 Email/NIP [{email}]: ").strip()
    if input_email: email = input_email

    password = getpass.getpass("🔑 Masukkan Kata Sandi TTE: ")
    if not password: return

    is_headless = input("Mulai dalam mode senyap (Background)? (Y/n): ").strip().lower() != 'n'

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=is_headless)
        context = browser.new_context()
        page = context.new_page()

        print("\n🔑 Melakukan Login...")
        page.goto("https://tte.kemenag.go.id/login", wait_until="networkidle")
        try:
            try:
                page.get_by_role("radio", name="Admin SATKER").check()
            except:
                page.get_by_text("Admin SATKER").click()
            page.get_by_role("textbox", name="Masukkan Email").fill(email)
            page.get_by_role("textbox", name="Masukkan Kata Sandi").fill(password)
            page.get_by_role("button", name="Masuk").click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Login error: {e}")

        if "login" in page.url:
            page.wait_for_url("**/satker**", timeout=45000)
        print("✅ Berhasil Login!")

        print("\n📑 Membuka Tabel Naskah & Mengambil Data (ID)...")
        page.goto("https://tte.kemenag.go.id/satker/dokumen/naskah/index/unggah", wait_until="networkidle")
        time.sleep(2)

        catalog = fetch_table_catalog(page, max_pages=10)
        print(f"✅ Berhasil mengindeks {len(catalog)} naskah dari server.")

        # Ambil CSRF Token
        try:
            csrf_token = page.locator("input[name='_token']").first.get_attribute("value")
            if not csrf_token:
                csrf_token = page.locator("meta[name='csrf-token']").get_attribute("content")
        except:
            csrf_token = ""

        if not csrf_token:
            print("❌ Gagal mendapatkan token keamanan (CSRF Token) dari halaman.")
            return

        success_count = 0
        success_count = 0
        target_perihals = [item.get("perihal", "") for item in upload_hist if item.get("perihal")]
        canceled_perihals = []

        print("\n🚀 Memulai Proses Pembatalan Cepat (via API)...")
        for idx, row in enumerate(catalog):
            doc_id = row.get("id")
            perihal_server = row.get("perihal_dokumen", "")
            status_html = row.get("status_dokumen", "")
            
            import html
            # Cek apakah perihal naskah di server ada di dalam upload_hist kita
            matched_target_p = None
            for target_p in target_perihals:
                # Decode HTML entities dari server (misal &#039; jadi ' )
                decoded_server = html.unescape(perihal_server)
                
                # Normalisasi untuk pencocokan yang aman
                norm_target = re.sub(r'[^a-zA-Z0-9]', '', target_p.lower())
                norm_server = re.sub(r'[^a-zA-Z0-9]', '', decoded_server.lower())
                
                # Jika target perihal (dari riwayat lokal) terkandung / cocok dengan server
                if norm_target and (norm_target in norm_server or norm_server in norm_target):
                    matched_target_p = target_p
                    break

            if matched_target_p:
                # Periksa apakah belum final/batal
                if "Sukses" in status_html or "Dibatalkan" in status_html:
                    print(f"⏭️ [SKIP] Dokumen '{perihal_server[:40]}...' sudah final/dibatalkan.")
                    canceled_perihals.append(matched_target_p) # Tetap anggap aman dihapus dari antrean
                    continue
                
                # Kirim request pembatalan langsung menggunakan page.evaluate(fetch) agar sangat cepat
                print(f"🗑️ [BATAL] Membatalkan: {perihal_server[:50]}...")
                try:
                    js_code = f"""
                    fetch('https://tte.kemenag.go.id/satker/dokumen/naskah/{doc_id}/update_status/4', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                        body: new URLSearchParams({{
                            '_token': '{csrf_token}',
                            'alasan': 'Salah Dokumen / Otomatis Dibatalkan'
                        }})
                    }}).then(r => r.status);
                    """
                    page.evaluate(js_code)
                    success_count += 1
                    canceled_perihals.append(matched_target_p)
                    time.sleep(0.5) # Jeda aman anti-spam
                except Exception as e:
                    print(f"   ❌ Gagal membatalkan: {e}")

        print("\n" + "=" * 60)
        print(f"🎉 SELESAI! Berhasil membatalkan {success_count} dokumen.")
        
        # Hanya hapus dari history dokumen-dokumen yang sudah berhasil dibatalkan tadi
        if canceled_perihals:
            print(f"Mengeluarkan {len(canceled_perihals)} dokumen yang dibatalkan dari history...")
            # Muat ulang history asli dari file (bukan history yang dipotong saat tes)
            with open(HISTORY_UPLOAD_FILE, "r", encoding="utf-8") as f:
                full_history = json.load(f)
            
            # Saring history: hanya simpan yang TIDAK ada di canceled_perihals
            updated_history = [
                h for h in full_history 
                if h.get("perihal") not in canceled_perihals
            ]
            
            with open(HISTORY_UPLOAD_FILE, "w", encoding="utf-8") as f:
                json.dump(updated_history, f, indent=2, ensure_ascii=False)
            print(f"✅ Sisa dokumen di antrean: {len(updated_history)} file.")
        
        print("=" * 60)
        browser.close()

if __name__ == "__main__":
    main()
