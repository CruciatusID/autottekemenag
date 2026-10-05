import json
import os
import sys
import time
import getpass
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"
LOG_FILE = BASE_DIR / "inspeksi_proses_tte.log"

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
    print(" 🕵️ INSPEKTOR PROSES TTE (PEMARAFAN & PENANDATANGANAN) ")
    print("=" * 65)
    print("Script ini akan merekam jejak digital (Network & API) saat Anda")
    print("melakukan aksi Paraf atau Tanda Tangan pada sebuah dokumen.")
    print("=" * 65)

    config = load_config()
    email = config.get("email", "")

    input_email = input(f"👤 Email/NIP (Gunakan Akun Pejabat) [{email}]: ").strip()
    if input_email: email = input_email
    elif not email:
        email = input("👤 Email/NIP Pejabat: ").strip()

    password = getpass.getpass("🔑 Masukkan Kata Sandi Akun Pejabat: ")
    if not password: return

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== SESI INSPEKSI PROSES TTE {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={"width": 1366, "height": 768})
        page = context.new_page()

        # Listener jaringan untuk memantau request sensitif (Paraf / TTE)
        def on_request(request):
            req_url = request.url.lower()
            if any(keyword in req_url for keyword in ["sign", "paraf", "tandatangan", "tte", "approve", "passphrase", "verify", "api"]):
                log_event(f"📡 [NETWORK REQUEST] {request.method} {request.url}")
                try:
                    if request.post_data:
                        # Sensor passphrase agar tidak tersimpan vulgar di log, cukup lihat strukturnya
                        sanitized_data = request.post_data
                        if "passphrase" in sanitized_data.lower():
                            log_event(f"   Payload (mengandung passphrase): {sanitized_data}")
                        else:
                            log_event(f"   Payload: {sanitized_data}")
                except: pass

        def on_response(response):
            resp_url = response.url.lower()
            if any(keyword in resp_url for keyword in ["sign", "paraf", "tandatangan", "tte", "approve", "verify"]):
                log_event(f"📥 [NETWORK RESPONSE] {response.status} {response.url}")
                try:
                    text = response.text()
                    log_event(f"   Response Body: {text[:400]}")
                except: pass

        page.on("request", on_request)
        page.on("response", on_response)

        print("🔑 Melakukan Login...")
        page.goto("https://tte.kemenag.go.id/login", wait_until="networkidle")
        try:
            # Mengklik opsi Pegawai ASN sesuai screenshot
            try: 
                page.locator("input[type='radio']").nth(0).check() # Pilihan pertama biasanya Pegawai ASN
                page.get_by_text("Pegawai ASN").click()
            except: pass 
            
            time.sleep(0.5)
            
            # Kolom NIP (bisa 'Masukkan NIP' atau input teks pertama)
            try:
                page.get_by_role("textbox", name="Masukkan NIP").fill(email)
            except:
                page.locator("input[type='text']").first.fill(email)
                
            page.get_by_role("textbox", name="Masukkan Kata Sandi").fill(password)
            page.get_by_role("button", name="Masuk").click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
        except Exception as e: print(f"⚠️ Info saat login: {e}")

        # Pasang pendengar klik
        page.evaluate("""
        () => {
            document.addEventListener('click', (e) => {
                let target = e.target;
                let btn = target.closest('button, a, .btn, [role="button"]') || target;
                let info = {
                    tagName: btn.tagName, id: btn.id, className: btn.className,
                    textContent: (btn.textContent || '').trim().replace(/\\s+/g, ' '),
                    href: btn.getAttribute('href') || ''
                };
                console.log('DOM_CLICK_CAPTURED:' + JSON.stringify(info));
            }, true);
        }
        """)

        page.on("console", lambda msg: log_event(f"🖱️ [KLIK] {msg.text.replace('DOM_CLICK_CAPTURED:', '')}") if msg.text.startswith("DOM_CLICK_CAPTURED:") else None)

        print("\n" + "=" * 65)
        print("🎯 BROWSER SUDAH SIAP!")
        print("=" * 65)
        print("Instruksi Anda (sebagai Pejabat/Pemaraf):")
        print(" 1. Buka kotak masuk/dokumen yang menunggu persetujuan Anda.")
        print(" 2. Lakukan proses Paraf atau Tanda Tangan (masukkan Passphrase dsb).")
        print(" 3. Kembali ke terminal ini dan tekan ENTER jika dokumen sudah ter-TTE.")
        print("=" * 65)
        
        try: page.pause()
        except: pass
        try: input("\nTekan ENTER jika sudah selesai melakukan TTE di browser...")
        except: pass

        print(f"\n✅ Selesai merekam! Log tersimpan di: {LOG_FILE.resolve()}")
        browser.close()

if __name__ == "__main__":
    main()
