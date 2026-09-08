import os
import re
import sys
from pathlib import Path
import pypdf

# Pastikan output console UTF-8 di Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
SOURCE_PDF = BASE_DIR / "Sertifikat_MGMP.pdf"
OUTPUT_DIR = BASE_DIR / "SERTIFIKAT_KBC"

def clean_filename(text: str) -> str:
    # Hilangkan koma atas / apostrof (' ’ ‘ `)
    cleaned = re.sub(r"['’‘`]", "", text)
    # Hilangkan karakter ilegal Windows \ / : * ? " < > |
    cleaned = re.sub(r'[\\/*?:"<>|]', "", cleaned)
    # Rapikan spasi ganda
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def split_certificates():
    print("=" * 60)
    print("      ✂️  SPLITTER SERTIFIKAT MGMP KBC (2 HALAMAN / FILE)      ")
    print("=" * 60)

    if not SOURCE_PDF.exists():
        print(f"❌ File sumber tidak ditemukan: {SOURCE_PDF}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Folder Output: {OUTPUT_DIR.resolve()}\n")

    reader = pypdf.PdfReader(str(SOURCE_PDF))
    total_pages = len(reader.pages)
    total_certs = total_pages // 2

    print(f"📄 Total Halaman : {total_pages}")
    print(f"📜 Total Sertifikat : {total_certs}\n")

    success_count = 0

    for i in range(total_certs):
        page_idx_1 = i * 2
        page_idx_2 = i * 2 + 1

        p1 = reader.pages[page_idx_1]
        p2 = reader.pages[page_idx_2]

        text = p1.extract_text()
        
        # Ekstrak Nama Peserta
        m = re.search(r'Nama\s*:\s*([^\n\r]+)', text)
        if m:
            raw_name = m.group(1).strip()
        else:
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            raw_name = f"Peserta_{i+1}"
            for idx, l in enumerate(lines):
                if 'Nama' in l and idx + 1 < len(lines):
                    raw_name = lines[idx+1]
                    break

        clean_name = clean_filename(raw_name)
        filename = f"Sertifikat KBC - {clean_name}.pdf"
        output_filepath = OUTPUT_DIR / filename

        # Buat PDF 2 halaman
        writer = pypdf.PdfWriter()
        writer.add_page(p1)
        writer.add_page(p2)

        with open(output_filepath, "wb") as f_out:
            writer.write(f_out)

        success_count += 1
        print(f"[{i+1:02d}/{total_certs}] ✅ Berhasil: {filename} (Hal {page_idx_1+1}-{page_idx_2+1})")

    print("\n" + "=" * 60)
    print(f"🏁 SELESAI! Berhasil memecah {success_count} file sertifikat.")
    print(f"📁 Lokasi: {OUTPUT_DIR.resolve()}")
    print("=" * 60)

if __name__ == "__main__":
    split_certificates()
