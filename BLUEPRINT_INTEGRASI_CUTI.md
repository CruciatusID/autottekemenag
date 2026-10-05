# 🚀 Blueprint Integrasi TTE pada Aplikasi Cuti (Rencana Masa Depan)

Dokumen ini adalah **catatan (checkpoint)** untuk pengembangan fitur Tanda Tangan Elektronik (TTE) otomatis pada Aplikasi Cuti internal.

## 📌 Konsep Dasar (Jalur RPA / Bot Piggybacking)
Karena Aplikasi Cuti tidak dapat berkomunikasi langsung dengan API BSrE (karena membutuhkan Whitelisting IP, Client Certificate mTLS, dan MoU resmi), kita menggunakan metode **Robot Process Automation (RPA)** yang menjembatani Aplikasi Cuti dengan Portal Web TTE Kemenag.

---

## ⚙️ Alur Kerja (Siklus Hidup Dokumen Cuti)

### 1. Fase Pengajuan (Auto-Upload)
* **Pemicu:** Staf menekan tombol "Ajukan Cuti" di Aplikasi Cuti.
* **Proses Sistem:** 
  1. Aplikasi meng-generate file PDF Cuti dan menyisipkan simbol *Anchor* (misal: `^` di kolom tanda tangan Kepala).
  2. Aplikasi menjalankan bot (`tte_batch_uploader.py`) secara *headless* (layar tersembunyi).
  3. Bot *login* ke `tte.kemenag.go.id`, mengunggah PDF, mengisi "Perihal", dan menetapkan Pejabat Penandatangan.
* **Hasil Akhir:** Naskah Cuti sudah *standby* di menu "Perlu Ditandatangani" milik Kepala Kantor di server Kemenag.

### 2. Fase Persetujuan (Auto-Sign)
* **Pemicu:** Kepala Kantor menekan "Setujui" di Aplikasi Cuti dan menginput **Passphrase**.
* **Proses Sistem:**
  1. Aplikasi Cuti menyimimpan sementara *passphrase* tersebut.
  2. Aplikasi memanggil bot khusus (contoh: `tte_auto_signer.py`).
  3. Bot *login* ke `tte.kemenag.go.id` sebagai Kepala Kantor.
  4. Bot mengirimkan **API Request Payload** secara massal/tunggal dengan format:
     `id[]=2593419 & passphrase=passphrasePejabat`
* **Hasil Akhir:** Dokumen resmi disahkan (distempel TTE) oleh BSSN via Kemenag.

### 3. Fase Selesai (Auto-Download)
* **Pemicu:** API persetujuan membalas "Sukses".
* **Proses Sistem:**
  1. Bot segera melakukan aksi *download* pada ID dokumen terkait yang baru saja disahkan.
  2. Bot menyimpan file PDF final (yang sudah ada QR Code-nya) ke dalam sistem Cuti.
* **Hasil Akhir:** Staf mendapat Surat Cuti sah secara instan tanpa perlu repot keluar-masuk web Kemenag.

---

## 🛠️ Temuan Penting (Hasil Inspeksi API)
- Web TTE Kemenag mendukung **TTE Massal** (Bulk Sign/Paraf) lewat pengiriman array `id[]` dalam satu request POST. Ini memungkinkan bot menyetujui puluhan naskah cuti dalam hitungan detik.
- Payload yang dikirim untuk Paraf/Sign terdiri dari:
  - `_token` (CSRF)
  - `id[]` (Array ID Dokumen pada tabel Verify/Paraf)
  - `passphrase` (Kata Sandi Sertifikat)

---

> **💡 Status Proyek:** Disimpan sementara. Saat aplikasi Cuti sudah siap di-integrasikan, kita cukup membuat script `tte_auto_signer.py` berbasis *Playwright* untuk mengeksekusi request Payload di atas.
