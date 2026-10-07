import os
import shutil
import fitz  # PyMuPDF
from pathlib import Path

def main():
    base_dir = Path(r"d:\projek\autottekemenag\HASIL_DOWNLOAD_TTE")
    
    # Create temp directories for separating
    peserta_dir = base_dir / "Peserta"
    narasumber_dir = base_dir / "Narasumber"
    lainnya_dir = base_dir / "Lainnya"
    
    peserta_dir.mkdir(exist_ok=True)
    narasumber_dir.mkdir(exist_ok=True)
    lainnya_dir.mkdir(exist_ok=True)
    
    # Track counts
    counts = {"Peserta": 0, "Narasumber": 0, "Lainnya": 0}
    
    for pdf_path in base_dir.glob("*.pdf"):
        if pdf_path.is_file():
            try:
                doc = fitz.open(pdf_path)
                text = ""
                if len(doc) > 0:
                    text = doc[0].get_text().lower()
                doc.close()
                
                if "sebagai narasumber" in text or "sebagai narasumber" in text.replace("\n", " "):
                    shutil.copy2(pdf_path, narasumber_dir / pdf_path.name)
                    counts["Narasumber"] += 1
                elif "sebagai peserta" in text or "sebagai peserta" in text.replace("\n", " "):
                    shutil.copy2(pdf_path, peserta_dir / pdf_path.name)
                    counts["Peserta"] += 1
                else:
                    # In case OCR parsing is a bit tricky, try checking just 'narasumber' or 'peserta'
                    if "narasumber" in text:
                        shutil.copy2(pdf_path, narasumber_dir / pdf_path.name)
                        counts["Narasumber"] += 1
                    elif "peserta" in text:
                        shutil.copy2(pdf_path, peserta_dir / pdf_path.name)
                        counts["Peserta"] += 1
                    else:
                        shutil.copy2(pdf_path, lainnya_dir / pdf_path.name)
                        counts["Lainnya"] += 1
            except Exception as e:
                print(f"Error reading {pdf_path.name}: {e}")
                shutil.copy2(pdf_path, lainnya_dir / pdf_path.name)
                counts["Lainnya"] += 1

    # Zip the directories
    print("Membuat Peserta.zip...")
    if counts["Peserta"] > 0:
        shutil.make_archive(str(base_dir / "Peserta"), 'zip', str(peserta_dir))
    
    print("Membuat Narasumber.zip...")
    if counts["Narasumber"] > 0:
        shutil.make_archive(str(base_dir / "Narasumber"), 'zip', str(narasumber_dir))
        
    print("Membuat Lainnya.zip...")
    if counts["Lainnya"] > 0:
        shutil.make_archive(str(base_dir / "Lainnya"), 'zip', str(lainnya_dir))

    # Clean up directories
    shutil.rmtree(peserta_dir)
    shutil.rmtree(narasumber_dir)
    shutil.rmtree(lainnya_dir)
    
    print(f"Selesai! Rekap:")
    print(f"- Peserta: {counts['Peserta']} file -> Peserta.zip")
    print(f"- Narasumber: {counts['Narasumber']} file -> Narasumber.zip")
    print(f"- Lainnya: {counts['Lainnya']} file -> Lainnya.zip")

if __name__ == "__main__":
    main()
