import json
import time
import getpass
import csv
from pathlib import Path
from playwright.sync_api import sync_playwright
import html

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"
CSV_FILE = BASE_DIR / "daftar_dokumen_dibatalkan.csv"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def fetch_table_catalog(page, max_pages: int = 20) -> list:
    """Mengambil katalog naskah dari tabel Dokumen Dibatalkan"""
    all_rows = []
    try:
        # Pancing halaman pertama (100 item)
        with page.expect_response(lambda r: "data_index" in r.url, timeout=15000) as resp_info:
            page.evaluate("() => { $('.dataTables').DataTable().page.len(100).draw(); }")
            
        data = resp_info.value.json().get("data", [])
        all_rows.extend(data)
        
        records_total = resp_info.value.json().get("recordsTotal", 0)
        
        if records_total > 100 and max_pages > 1:
            pages_to_fetch = min(max_pages, (records_total // 100) + 1)
            for p_idx in range(1, pages_to_fetch):
                try:
                    # Ambil halaman berikutnya (index ke p_idx)
                    with page.expect_response(lambda r: "data_index" in r.url, timeout=15000) as next_resp:
                        page.evaluate(f"() => {{ $('.dataTables').DataTable().page({p_idx}).draw('page'); }}")
                    next_data = next_resp.value.json().get("data", [])
                    if not next_data:
                        break
                    all_rows.extend(next_data)
                except Exception as e:
                    print(f"⚠️ Gagal menarik halaman {p_idx+1}: {e}")
                    break
    except Exception as e:
        print(f"⚠️ Peringatan saat memuat katalog tabel: {e}")
    return all_rows

def main():
    print("=" * 70)
    print(" 🗑️ TTE KEMENAG BATCH PERMANENT DELETER (HAPUS PERMANEN) ")
    print("=" * 70)

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
            try: page.get_by_role("radio", name="Admin SATKER").check()
            except: page.get_by_text("Admin SATKER").click()
            page.get_by_role("textbox", name="Masukkan Email").fill(email)
            page.get_by_role("textbox", name="Masukkan Kata Sandi").fill(password)
            page.get_by_role("button", name="Masuk").click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
        except Exception as e:
            pass

        if "login" in page.url:
            page.wait_for_url("**/satker**", timeout=45000)
        print("✅ Berhasil Login!")

        print("\n📑 Membuka Keranjang 'Dokumen Dibatalkan'...")
        page.goto("https://tte.kemenag.go.id/satker/dokumen/naskah/index/dibatalkan", wait_until="networkidle")
        time.sleep(2)

        print("🔍 Mengekstrak seluruh daftar naskah dari tabel...")
        catalog = fetch_table_catalog(page, max_pages=15)
        
        if not catalog:
            print("🎉 Hore! Keranjang Dokumen Dibatalkan Anda sudah KOSONG / Bersih!")
            browser.close()
            return

        # Simpan ke CSV dengan mengekstrak SELURUH variabel/kolom (termasuk alasan jika ada)
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            if catalog:
                # Ambil semua kunci (keys) dari dokumen pertama sebagai header kolom
                headers = ["No"] + list(catalog[0].keys())
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                for i, row in enumerate(catalog, 1):
                    row_data = {"No": i}
                    for k, v in row.items():
                        # Decode HTML entities khusus untuk string
                        row_data[k] = html.unescape(str(v)) if isinstance(v, str) else v
                    writer.writerow(row_data)
        
        print("\n" + "=" * 70)
        print(f"📋 DAFTAR {len(catalog)} DOKUMEN YANG AKAN DIHAPUS PERMANEN")
        print("=" * 70)
        print(f"{'No':<4} | {'ID':<9} | {'Perihal (Dipotong max 45 char)':<48} | {'Waktu'}")
        print("-" * 70)
        for i, row in enumerate(catalog[:15], 1): # Tampilkan max 15 di layar
            perihal = html.unescape(row.get("perihal_dokumen", ""))
            short_p = perihal[:45] + "..." if len(perihal) > 45 else perihal
            print(f"{i:<4} | {row.get('id'):<9} | {short_p:<48} | {row.get('waktu')}")
        
        if len(catalog) > 15:
            print(f"... dan {len(catalog) - 15} dokumen lainnya (Total: {len(catalog)}).")
        print("-" * 70)
        print(f"✅ Daftar lengkap telah disimpan ke: {CSV_FILE.name}")
        
        print("\n[?] PILIH TINDAKAN SELANJUTNYA:")
        print("    1. Hapus Permanen 1 dokumen saja (Mode Uji Coba)")
        print("    2. Hapus Permanen 2 dokumen")
        print("    3. Babad Habis (Hapus Permanen SEMUA DOKUMEN) [Default]")
        print("    4. Batal & Keluar (Biarkan saja)")
        
        choice = input("\nPilih opsi [1/2/3/4] (Default: 3): ").strip() or "3"
        
        target_docs = []
        if choice == "1":
            target_docs = catalog[:1]
        elif choice == "2":
            target_docs = catalog[:2]
        elif choice == "4":
            print("Keluar. Tidak ada dokumen yang dihapus.")
            browser.close()
            return
        else:
            target_docs = catalog

        konfirmasi = input(f"\n⚠️ PERINGATAN: Dokumen tidak bisa dikembalikan! Yakin ingin menghapus {len(target_docs)} dokumen secara permanen? (y/N): ").strip().lower()
        if konfirmasi != 'y':
            print("Dibatalkan.")
            browser.close()
            return

        # Ambil CSRF Token
        try:
            csrf_token = page.locator("input[name='_token']").first.get_attribute("value")
            if not csrf_token:
                csrf_token = page.locator("meta[name='csrf-token']").get_attribute("content")
        except:
            csrf_token = ""

        if not csrf_token:
            print("❌ Gagal mendapatkan token keamanan (CSRF Token) dari halaman.")
            browser.close()
            return

        success_count = 0
        print("\n🚀 Memulai Eksekusi Penghapusan Permanen...")
        for idx, row in enumerate(target_docs, 1):
            doc_id = row.get("id")
            perihal = html.unescape(row.get("perihal_dokumen", ""))
            
            print(f"🔥 [{idx}/{len(target_docs)}] Menghapus: {perihal[:50]}...")
            try:
                js_code = f"""
                fetch('https://tte.kemenag.go.id/satker/dokumen/{doc_id}/destroy', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                    body: new URLSearchParams({{
                        '_token': '{csrf_token}',
                        '_method': 'DELETE'
                    }})
                }}).then(r => r.status);
                """
                page.evaluate(js_code)
                success_count += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"   ❌ Gagal: {e}")

        print("\n" + "=" * 70)
        print(f"🎉 SELESAI! Berhasil menghapus permanen {success_count} dokumen.")
        print("=" * 70)
        browser.close()

if __name__ == "__main__":
    main()
