import json
import os
import sys
import time
import getpass
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"
LOG_FILE = BASE_DIR / "inspeksi_batal.log"

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def log_event(text: str):
    print(text)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")
    except Exception:
        pass

def main():
    print("=" * 65)
    print(" 🔍 INSPEKSI / PEREKAM TOMBOL PEMBATALAN NASKAH TTE KEMENAG ")
    print("=" * 65)
    print("Script ini akan:")
    print("1. Membuka Chrome dan login otomatis ke akun TTE Kemenag Anda.")
    print("2. Menampilkan halaman tabel naskah yang baru saja diunggah.")
    print("3. Memantau klik elemen dan request jaringan saat Anda mencontohkan")
    print("   pembatalan pada salah satu dokumen.")
    print("=" * 65)

    config = load_config()
    email = config.get("email", "198906212022031002@kemenag.go.id")

    input_email = input(f"👤 Email/NIP [{email}]: ").strip()
    if input_email:
        email = input_email

    password = getpass.getpass("🔑 Masukkan Kata Sandi TTE: ")
    if not password:
        print("❌ Password tidak boleh kosong!")
        input("\nTekan ENTER untuk keluar...")
        return

    # Bersihkan file log sebelumnya
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== SESI INSPEKSI PEMBATALAN {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    with sync_playwright() as playwright:
        print("\n🌐 Meluncurkan browser Chrome...")
        browser = playwright.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={"width": 1366, "height": 768})
        page = context.new_page()

        # Listener jaringan untuk menangkap request AJAX / API pembatalan
        def on_request(request):
            req_url = request.url
            if any(keyword in req_url.lower() for keyword in ["batal", "cancel", "hapus", "delete", "reject", "status"]):
                log_event(f"📡 [NETWORK REQUEST] {request.method} {req_url}")
                try:
                    if request.post_data:
                        log_event(f"   Payload: {request.post_data}")
                except Exception:
                    pass

        def on_response(response):
            resp_url = response.url
            if any(keyword in resp_url.lower() for keyword in ["batal", "cancel", "hapus", "delete", "reject", "status"]):
                log_event(f"📥 [NETWORK RESPONSE] {response.status} {resp_url}")
                try:
                    text = response.text()
                    log_event(f"   Response Body (first 300 char): {text[:300]}")
                except Exception:
                    pass

        page.on("request", on_request)
        page.on("response", on_response)

        # Dialog listener (jika ada popup konfirmasi native browser / SweetAlert)
        def on_dialog(dialog):
            log_event(f"⚠️ [DIALOG POPUP] Type: {dialog.type} | Message: {dialog.message}")
            dialog.accept()

        page.on("dialog", on_dialog)

        # Login
        print("🔑 Melakukan Login ke https://tte.kemenag.go.id/login ...")
        page.goto("https://tte.kemenag.go.id/login", wait_until="networkidle")

        try:
            try:
                page.get_by_role("radio", name="Admin SATKER").check()
            except Exception:
                page.get_by_text("Admin SATKER").click()

            page.get_by_role("textbox", name="Masukkan Email").fill(email)
            page.get_by_role("textbox", name="Masukkan Kata Sandi").fill(password)
            page.get_by_role("button", name="Masuk").click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Info saat login: {e}")

        if "login" in page.url:
            print("⏳ Menunggu verifikasi login selesai...")
            try:
                page.wait_for_url("**/satker**", timeout=45000)
            except Exception:
                pass

        print("✅ Berhasil masuk ke dashboard SATKER!")

        # Buka halaman naskah
        naskah_url = "https://tte.kemenag.go.id/satker/dokumen/naskah/index/unggah"
        print(f"📄 Membuka tabel dokumen: {naskah_url}")
        page.goto(naskah_url, wait_until="networkidle")
        time.sleep(3)

        # Pasang listener klik di DOM untuk mencatat tombol yang diklik
        page.evaluate("""
        () => {
            document.addEventListener('click', (e) => {
                let target = e.target;
                let btn = target.closest('button, a, .btn, [role="button"]') || target;
                let info = {
                    tagName: btn.tagName,
                    id: btn.id,
                    className: btn.className,
                    textContent: (btn.textContent || '').trim().replace(/\\s+/g, ' '),
                    href: btn.getAttribute('href') || '',
                    title: btn.getAttribute('title') || '',
                    onclick: btn.getAttribute('onclick') || '',
                    dataId: btn.getAttribute('data-id') || btn.getAttribute('data-dokumen-id') || ''
                };
                console.log('DOM_CLICK_CAPTURED:' + JSON.stringify(info));
            }, true);
        }
        """)

        # Console log listener
        def on_console(msg):
            text = msg.text
            if text.startswith("DOM_CLICK_CAPTURED:"):
                payload = text.replace("DOM_CLICK_CAPTURED:", "")
                log_event(f"🖱️ [KLIK TERDETEKSI] {payload}")

        page.on("console", on_console)

        print("\n" + "=" * 65)
        print("🎯 BROWSER & INSPEKTOR SUDAH SIAP!")
        print("=" * 65)
        print("Instruksi Langkah Anda di Browser:")
        print(" 1. Cari salah satu baris dokumen yang salah di tabel.")
        print(" 2. Klik tombol 'Batalkan' (atau ikon aksi pembatalan terkait).")
        print(" 3. Jika muncul modal konfirmasi / alasan pembatalan, silakan selesaikan.")
        print(" 4. Jendela Playwright Inspector juga terbuka (bisa klik 'Record' jika mau).")
        print(" 5. Setelah selesai 1 kali contoh pembatalan, Anda bisa kembali ke terminal ini.")
        print("=" * 65)
        print("👉 Script sedang aktif memantau... Tekan ENTER di terminal ini jika sudah selesai mencontohkan.")

        # Pause agar Playwright Inspector terbuka dan user bisa berinteraksi penuh
        try:
            page.pause()
        except Exception:
            pass

        try:
            input("\nTekan ENTER setelah selesai mencontohkan di browser...")
        except Exception:
            pass

        print(f"\n✅ Selesai merekam! Seluruh log tersimpan di: {LOG_FILE.resolve()}")
        browser.close()

if __name__ == "__main__":
    main()
