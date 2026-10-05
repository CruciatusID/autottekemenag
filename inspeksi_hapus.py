import json
import os
import sys
import time
import getpass
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"
LOG_FILE = BASE_DIR / "inspeksi_hapus.log"

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
    print(" 🗑️ INSPEKSI / PEREKAM TOMBOL HAPUS PERMANEN TTE KEMENAG ")
    print("=" * 65)
    print("Script ini akan membuka Chrome dan login otomatis.")
    print("Tugas Anda:")
    print(" 1. Klik menu 'Dokumen Dibatalkan' (atau menu tempat dokumen batal berada).")
    print(" 2. Contohkan hapus permanen 1 dokumen.")
    print("=" * 65)

    config = load_config()
    email = config.get("email", "198906212022031002@kemenag.go.id")

    input_email = input(f"👤 Email/NIP [{email}]: ").strip()
    if input_email: email = input_email

    password = getpass.getpass("🔑 Masukkan Kata Sandi TTE: ")
    if not password: return

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== SESI INSPEKSI HAPUS PERMANEN {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={"width": 1366, "height": 768})
        page = context.new_page()

        # Listener jaringan
        def on_request(request):
            req_url = request.url
            if any(keyword in req_url.lower() for keyword in ["batal", "cancel", "hapus", "delete", "destroy", "remove"]):
                log_event(f"📡 [NETWORK REQUEST] {request.method} {req_url}")
                try:
                    if request.post_data:
                        log_event(f"   Payload: {request.post_data}")
                except: pass

        def on_response(response):
            resp_url = response.url
            # Abaikan polling notifikasi yang gak penting
            if "notifikasi" in resp_url.lower(): return
            
            # Khusus ambil URL request DataTables agar kita tahu URL datanya
            if "data_index" in resp_url.lower() or "datatables" in resp_url.lower():
                log_event(f"📋 [DATATABLES API] {response.status} {resp_url}")
                return
                
            if any(keyword in resp_url.lower() for keyword in ["batal", "cancel", "hapus", "delete", "destroy", "remove"]):
                log_event(f"📥 [NETWORK RESPONSE] {response.status} {resp_url}")
                try:
                    text = response.text()
                    log_event(f"   Response Body: {text[:300]}")
                except: pass

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("dialog", lambda dialog: [log_event(f"⚠️ [DIALOG POPUP] {dialog.message}"), dialog.accept()])

        print("🔑 Melakukan Login...")
        page.goto("https://tte.kemenag.go.id/login", wait_until="networkidle")
        try:
            try: page.get_by_role("radio", name="Admin SATKER").check()
            except: page.get_by_text("Admin SATKER").click()
            page.get_by_role("textbox", name="Masukkan Email").fill(email)
            page.get_by_role("textbox", name="Masukkan Kata Sandi").fill(password)
            page.get_by_role("button", name="Masuk").click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
        except Exception as e: print(f"⚠️ Info saat login: {e}")

        # Pasang DOM listener
        page.evaluate("""
        () => {
            document.addEventListener('click', (e) => {
                let target = e.target;
                let btn = target.closest('button, a, .btn, [role="button"]') || target;
                let info = {
                    tagName: btn.tagName, id: btn.id, className: btn.className,
                    textContent: (btn.textContent || '').trim().replace(/\\s+/g, ' '),
                    href: btn.getAttribute('href') || '', onclick: btn.getAttribute('onclick') || ''
                };
                console.log('DOM_CLICK_CAPTURED:' + JSON.stringify(info));
            }, true);
        }
        """)

        page.on("console", lambda msg: log_event(f"🖱️ [KLIK] {msg.text.replace('DOM_CLICK_CAPTURED:', '')}") if msg.text.startswith("DOM_CLICK_CAPTURED:") else None)

        print("\n" + "=" * 65)
        print("🎯 BROWSER SUDAH SIAP!")
        print("=" * 65)
        print("Instruksi Anda:")
        print(" 1. Cari menu 'Dokumen Dibatalkan' (atau sejenisnya) di navigasi kiri.")
        print(" 2. Klik tombol 'Hapus' / 'Delete' pada salah satu dokumen.")
        print(" 3. Kembali ke terminal ini dan tekan ENTER setelah selesai.")
        print("=" * 65)
        
        try: page.pause()
        except: pass
        try: input("\nTekan ENTER jika sudah selesai mencontohkan di browser...")
        except: pass

        print(f"\n✅ Selesai merekam! Log tersimpan di: {LOG_FILE.resolve()}")
        browser.close()

if __name__ == "__main__":
    main()
