# 🚀 TTE Kemenag Auto-Assistant (Batch Uploader & Downloader)

Aplikasi otomasi cerdas berbasis **Python & Playwright** untuk mengunggah (*batch upload*) dan mengunduh (*batch download*) dokumen naskah dinas / SK / SKBK / Sertifikat secara massal di portal **TTE Kemenag** (`https://tte.kemenag.go.id`).

---

## 🌟 Fitur Utama

- ⚡ **Batch Auto-Upload**: Mengunggah puluhan hingga ratusan file PDF secara berurutan dan otomatis.
- 📂 **Pemindaian Folder Fleksibel**: Otomatis mendeteksi file PDF di dalam folder utama maupun seluruh subfolder (misal: `NON PNS`, `PNS KEMENAG`, `PPPK PEMDA`, dll.).
- ✍️ **Konfigurasi Pejabat Dinamis**:
  - Mendukung **1 Pejabat Pemaraf**.
  - Mendukung **1 hingga 4 Pejabat Penandatangan**.
  - Mendukung 4 simbol anchor resmi TTE Kemenag: **`^`**, **`#`**, **`$`**, **`*`**.
- 🔍 **Pencarian Cerdas Pejabat (Nama & NIP)**: Mendukung pencarian pejabat di dropdown Select2 menggunakan **Nama Lengkap**, **Nama Panggilan**, maupun nomor **NIP**.
- 📥 **Targeted High-Speed Auto-Downloader**:
  - **Katalog Indeks Server-Side**: Memuat data tabel langsung (100 item/halaman) sehingga pencocokan naskah berjalan instan (< 1 detik/file).
  - **Validasi Dokumen 2 Lapis**: Memverifikasi kecocokan jenis naskah dan nama pemilik secara presisi (mencegah salah ambil naskah lain yang memiliki nama depan serupa).
  - **Pilihan `FINAL` Teratas**: Otomatis mengambil naskah `FINAL` terbaru jika terdapat revisi / beberapa riwayat.
  - **Download Stream Langsung**: Mengunduh berkas bertanda tangan digital resmi tanpa jeda tab popup.
  - Pilihan penyimpanan: langsung di **1 folder utama** atau **otomatis dipisah ke subfolder kategori** (`NON PNS`, `PPPK`, dll.).
- 🛡️ **Anti-Duplikasi (Resume Support)**: Riwayat tersimpan di `upload_history.json` & `download_history.json`. Jika proses terhenti, bot akan melanjutkan sisa file tanpa mengulang dari awal.
- 🔒 **Keamanan Kredensial**: Kata sandi tidak disimpan di file konfigurasi; input kata sandi selalu diminta secara interaktif dan tersembunyi di terminal.
- 🖥️ **Pilihan Tampilan (Mode Senyap / Visual)**:
  - **Mode Senyap**: Berjalan murni di latar belakang (terminal) tanpa membuka jendela browser.
  - **Mode Visual**: Jendela browser Chrome terbuka di layar untuk memantau proses secara langsung.
- 🎥 **Perekam Langkah Terintegrasi ([`REKAM_DOWNLOAD.bat`](REKAM_DOWNLOAD.bat))**: Pintasan untuk merekam aksi web menggunakan Playwright Codegen.

---

## 📋 Struktur Direktori Projek

```text
├── HASIL_DOWNLOAD_TTE/          # Folder output hasil unduhan dokumen FINAL
├── JALANKAN_UPLOAD_TTE.bat      # Pintasan 1-klik untuk memulai Upload Massal
├── JALANKAN_DOWNLOAD_TTE.bat    # Pintasan 1-klik untuk memulai Download Dokumen FINAL
├── REKAM_DOWNLOAD.bat           # Perekam interaktif Playwright Codegen
├── INSTALL_DEPENDENCIES.bat     # Pintasan 1-klik instalasi library & browser
├── tte_batch_uploader.py        # Program utama Batch Auto-Uploader
├── tte_batch_downloader.py      # Program utama Batch Auto-Downloader
├── config.json                  # Konfigurasi akun, pemaraf, penandatangan, & anchor
├── upload_history.json          # Catatan histori dokumen yang sukses diunggah
├── download_history.json        # Catatan histori dokumen yang sukses diunduh
└── README.md                    # Dokumentasi panduan penggunaan
```

---

## 🛠️ Prasyarat Sistem

1. **Sistem Operasi**: Windows 10 / 11 (64-bit).
2. **Python**: Versi 3.10 atau yang lebih baru ([Unduh Python](https://www.python.org/downloads/)).
   > ⚠️ **PENTING saat instalasi Python**: Pastikan centang opsi **"Add Python to PATH"**.

---

## 🚀 Panduan Penggunaan Cepat (Quick Start)

### 1. Instalasi Dependensi (Cukup Sekali di Awal)
Dobel-klik file [**`INSTALL_DEPENDENCIES.bat`**](INSTALL_DEPENDENCIES.bat).
Script ini akan otomatis menginstal library `playwright` dan browser engine `Chromium`.

---

### 2. Mengunggah Surat Secara Massal (Batch Upload)
1. Letakkan file-file PDF yang ingin diunggah ke dalam folder projek ini (bisa dipisah dalam subfolder seperti `PNS`, `PPPK`, dll).
2. Dobel-klik [**`JALANKAN_UPLOAD_TTE.bat`**](JALANKAN_UPLOAD_TTE.bat).
3. Anda akan dipandu oleh menu interaktif di terminal:
   - **Path Folder PDF**: Tekan `ENTER` untuk folder saat ini (atau drag-and-drop folder lain).
   - **Jumlah Dokumen**: Pilih mode tes (1 atau 2 file) atau semua antrean.
   - **Tampilan**: Tekan `ENTER` untuk Mode Senyap (latar belakang).
   - **Konfirmasi Pejabat**: Konfirmasi NIP/Email, nama Pemaraf, dan nama Penandatangan (beserta anchornya).
   - **Kata Sandi**: Masukkan kata sandi akun TTE Anda.
4. Bot akan memproses seluruh surat hingga selesai! 🎉

---

### 3. Mengunduh Dokumen yang Selesai di-TTE (Batch Download)
1. Dobel-klik [**`JALANKAN_DOWNLOAD_TTE.bat`**](JALANKAN_DOWNLOAD_TTE.bat).
2. Anda akan disajikan opsi:
   - **Jumlah File**: Pilih tes beberapa file atau seluruh antrean.
   - **Struktur Folder**: Simpan langsung di 1 folder utama atau pisahkan ke subfolder kategori.
   - **Tampilan**: Pilih Mode Senyap atau Visual.
   - **Kata Sandi**: Masukkan kata sandi akun TTE Anda.
3. Bot akan memeriksa katalog dokumen di portal TTE. Dokumen yang berstatus **`FINAL`** akan langsung diunduh secara cepat dan disimpan rapi ke folder [**`HASIL_DOWNLOAD_TTE/`**](HASIL_DOWNLOAD_TTE/).

---

## ⚙️ Kustomisasi via `config.json`

Anda dapat mengatur default akun dan pejabat di file `config.json`:

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
> *Catatan: Satu penandatangan bisa memiliki lebih dari 1 anchor sekaligus (misal `["#", "$"]` atau `"#,$"`). Bot akan otomatis mencentang semua anchor tersebut dalam satu kali klik di portal TTE.*

---

## ❓ FAQ & Troubleshooting

- **Q: Apakah aman jika proses dihentikan di tengah jalan?**  
  **A**: Sangat aman. Setiap surat yang sukses langsung dicatat di `upload_history.json` / `download_history.json`. Saat dijalankan kembali, surat yang sudah ada otomatis dilewati.
- **Q: Bagaimana jika ada file yang belum FINAL saat proses download?**  
  **A**: Bot akan memberikan status `[BELUM FINAL]` (misal: *Menunggu Paraf*) dan melewatinya. Anda bisa menjalankan downloader kembali di lain hari untuk mengambil sisa file yang sudah selesai ditandatangani.
- **Q: Apakah kata sandi tersimpan di komputer?**  
  **A**: Tidak. Kata sandi diminta langsung secara interaktif saat menjalankan bot dan tidak disimpan ke file demi menjaga privasi dan keamanan akun.

---

## 📜 Lisensi & Penggunaan
Aplikasi ini dikembangkan untuk mempermudah dan mempercepat tugas administratif naskah dinas elektronik di lingkungan Kementerian Agama. Gunakan dengan bijak dan sesuai dengan ketentuan instansi.
