# 🚀 TTE Kemenag Auto-Assistant (Full Suite)

Aplikasi otomasi cerdas berbasis **Python & Playwright** untuk mengelola naskah dinas / SK / SKBK / Sertifikat secara massal di portal **TTE Kemenag** (`https://tte.kemenag.go.id`). 

Repositori ini adalah sebuah *Full Suite* yang mencakup fitur **Auto-Upload**, **Auto-Download**, **Auto-Cancel (Pembatalan)**, hingga **Auto-Delete (Hapus Permanen)**.

---

## 🌟 Fitur Utama

- ⚡ **Batch Auto-Upload**: Mengunggah puluhan hingga ratusan file PDF secara berurutan dan otomatis dari berbagai folder/subfolder sekaligus.
- 📥 **High-Speed Auto-Downloader**: Mengunduh berkas berstatus `FINAL` secara cepat tanpa membuka tab baru (Direct Stream) dan otomatis merapikannya ke dalam subfolder kategori.
- 🛑 **Batch Canceler (Pembatalan Massal)**: Salah unggah dokumen? Bot ini bisa membatalkan (*cancel*) ratusan dokumen secara otomatis murni via tembakan API super cepat.
- 🗑️ **Batch Permanent Deleter**: Menarik daftar seluruh "Dokumen Dibatalkan", menyajikannya dalam tabel & CSV, lalu menyapu bersih (menghapus permanen) semuanya dari server dalam 1 klik.
- ✍️ **Konfigurasi Pejabat Dinamis**:
  - Mendukung **1 Pejabat Pemaraf** (Bisa di-skip).
  - Mendukung **1 hingga 4 Pejabat Penandatangan**.
  - Mendukung multi-anchor (misal: `^`, `#`, `$`, `*`).
- 🛡️ **Anti-Duplikasi (Resume Support)**: Memiliki sistem riwayat cerdas (`upload_history.json`, dll). Jika proses mati lampu atau terhenti, bot akan melanjutkannya dari dokumen terakhir tanpa mengulang dari awal.
- 🔒 **Keamanan & Transparansi**: Kata sandi diminta secara interaktif di terminal (tidak disimpan di file). Dilengkapi juga dengan log dan script inspeksi jaringan.

---

## 📋 Struktur Direktori Projek

```text
📁 HASIL_DOWNLOAD_TTE/          # Folder output hasil unduhan dokumen FINAL
📁 backup_riwayat/              # Folder pencadangan otomatis untuk upload_history
📄 config.json                  # Konfigurasi akun, pemaraf, penandatangan, & anchor
📄 upload_history.json          # Database riwayat naskah yang berhasil diunggah

🚀 Launcher (Pintasan 1-Klik)
├── INSTALL_DEPENDENCIES.bat        # Instalasi library & browser Playwright (Jalankan pertama kali)
├── JALANKAN_UPLOAD_TTE.bat         # Memulai Upload Massal
├── JALANKAN_DOWNLOAD_TTE.bat       # Memulai Download Naskah FINAL
├── JALANKAN_BATALKAN_TTE.bat       # Membatalkan naskah massal (API)
└── JALANKAN_HAPUS_PERMANEN_TTE.bat # Menghapus permanen dokumen batal (API)

🤖 Core Scripts (Logika Otomatisasi Python)
├── tte_batch_uploader.py
├── tte_batch_downloader.py
├── tte_batch_canceler.py
└── tte_batch_deleter.py

🕵️ Inspector Scripts (Alat Edukasi/Penyadap API)
├── inspeksi_batalkan.py
├── inspeksi_hapus.py
└── inspeksi_proses_tte.py

📘 Dokumen
├── README.md                       # Dokumentasi panduan penggunaan ini
└── BLUEPRINT_INTEGRASI_CUTI.md     # Rancangan sistem masa depan (Integrasi Aplikasi Cuti via RPA)
```

---

## 🛠️ Prasyarat Sistem

1. **Sistem Operasi**: Windows 10 / 11 (64-bit).
2. **Python**: Versi 3.10 atau yang lebih baru ([Unduh Python](https://www.python.org/downloads/)).
   > ⚠️ **PENTING saat instalasi Python**: Pastikan centang opsi **"Add Python to PATH"**.

---

## 🚀 Panduan Penggunaan (Tutorial)

### 1. Instalasi (Cukup Sekali di Awal)
Dobel-klik file [**`INSTALL_DEPENDENCIES.bat`**](INSTALL_DEPENDENCIES.bat).
Script ini akan otomatis menginstal `playwright` dan browser engine `Chromium`.

---

### 2. Mengunggah Surat (Batch Upload)
1. Kumpulkan file PDF di folder projek ini (boleh dalam subfolder).
2. Dobel-klik [**`JALANKAN_UPLOAD_TTE.bat`**](JALANKAN_UPLOAD_TTE.bat).
3. Anda akan dipandu oleh menu interaktif:
   - Pilih jumlah (Uji Coba 1-2 file atau Semua).
   - Verifikasi nama Pemaraf dan Penandatangan.
   - Masukkan kata sandi.
4. Bot akan mengendalikan browser (*UI Automation*) dan memproses dokumen hingga selesai. Data dokumen yang sukses akan dicatat di `upload_history.json`.

---

### 3. Membatalkan Dokumen yang Salah (Batch Cancel)
Jika Anda menyadari ada kesalahan setelah dokumen terunggah:
1. Dobel-klik [**`JALANKAN_BATALKAN_TTE.bat`**](JALANKAN_BATALKAN_TTE.bat).
2. Script ini akan membaca `upload_history.json` sebagai daftar target.
3. Anda bisa memilih opsi tes (1 dokumen) atau batal massal. 
4. Fitur ini menggunakan jalur API Murni, sangat cepat (bisa membatalkan ratusan naskah hanya dalam puluhan detik).
5. Dokumen yang sukses dibatalkan akan dihapus otomatis dari file `upload_history.json`.

---

### 4. Sapu Bersih (Batch Permanent Deleter)
Untuk membuang dokumen dari keranjang "Dokumen Dibatalkan":
1. Dobel-klik [**`JALANKAN_HAPUS_PERMANEN_TTE.bat`**](JALANKAN_HAPUS_PERMANEN_TTE.bat).
2. Bot akan mengambil **seluruh daftar dokumen** di keranjang sampah server.
3. Bot akan menampilkan tabel daftarnya di layar terminal dan menyimpannya ke `daftar_dokumen_dibatalkan.csv`.
4. Anda diberi opsi konfirmasi sebelum sistem menghapus bersih naskah tersebut secara permanen.

---

### 5. Mengunduh Dokumen FINAL (Batch Download)
Jika Pejabat telah menyetujui (memaraf/menandatangani) dokumen:
1. Dobel-klik [**`JALANKAN_DOWNLOAD_TTE.bat`**](JALANKAN_DOWNLOAD_TTE.bat).
2. Pilih apakah Anda ingin struktur folder dipertahankan (Subfolder) atau ditumpuk di 1 folder utama.
3. Bot akan memeriksa katalog portal TTE dengan kecepatan tinggi, mencari yang berstatus **`FINAL`**, lalu mengunduhnya secara paralel langsung ke folder [**`HASIL_DOWNLOAD_TTE/`**](HASIL_DOWNLOAD_TTE/).

---

## ⚙️ Kustomisasi `config.json`

File konfigurasi ini mengatur pejabat standar (*default*) agar Anda tidak perlu mengetik manual tiap saat:

```json
{
  "email": "198906212022031002@kemenag.go.id",
  "jenis_dokumen": "Dokumen Lain-Lain",
  "pemaraf": {
    "nama": "Tamrin Lodo"
  },
  "penandatangan": [
    {
      "nama": "usman senong",
      "anchor": ["#", "$"]
    }
  ]
}
```
> **Catatan:**
> - Set `"pemaraf": null` jika tidak butuh pemaraf.
> - Multi-anchor (misal `["#", "$"]`) akan dicentang sekaligus oleh sistem untuk satu penandatangan.

---

## ❓ FAQ (Tanya Jawab)

- **Q: Apakah aman mematikan program di tengah jalan (Cancel/Upload)?**  
  **A**: Sangat aman. Sistem riwayat (*history tracker*) mencatat setiap file per detiknya. Saat Anda jalankan ulang, ia otomatis melanjutkan sisanya (Resume).

- **Q: Apa fungsi file Inspector (`inspeksi_*.py`)?**  
  **A**: Script tersebut adalah alat sadap jaringan (*Network & API Interceptor*). Berguna bagi developer/programmer yang ingin belajar bagaimana sistem portal TTE Kemenag saling bertukar data di belakang layar tanpa harus membongkar *source code* website mereka. 

- **Q: Bagaimana jika dokumen ditolak (*Rejected*) oleh pejabat?**  
  **A**: Anda bisa menggunakan fitur Batalkan atau hapus manual di web, lalu unggah perbaikan dokumennya seperti biasa.

---
*Dibuat untuk mempermudah dan mengotomatisasi administrasi naskah digital secara efisien & pintar.* 🚀
