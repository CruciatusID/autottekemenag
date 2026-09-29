# Aturan & Pengetahuan Proyek TTE Kemenag (AGENTS.md)

## Definisi & Ketentuan Anchor TTE
- **Pengertian**: **Anchor** adalah karakter/simbol penanda titik koordinat penempatan tanda tangan elektronik (TTE / QR Code) yang akan distempel secara otomatis oleh sistem TTE Kemenag (`https://tte.kemenag.go.id`) pada dokumen PDF.
- **Letak Anchor**: Anchor diletakkan di dalam dokumen PDF pada **kolom tanda tangan**, biasanya di antara jabatan penandatangan (misal: `Kepala,`) dan nama pejabat penandatangan (misal: `Usman Senong`), atau tepat di atas nama penandatangan.
- **Simbol Anchor yang Valid**:
  - `^` (caret) - Biasanya untuk Penandatangan Utama / Kepala Kantor
  - `#` (pagar)
  - `$` (dolar)
  - `*` (bintang)
- **Catatan Pemaraf**: Pejabat **Pemaraf** (misalnya `Tamrin Lodo`) **tidak memerlukan anchor** pada dokumen PDF, karena pemaraf hanya memaraf dokumen secara digital di portal TTE sebelum berkas ditandatangan.

---

## Prosedur Saat Diminta "Cek Anchor di PDF"
Setiap kali pengguna meminta untuk memeriksa/mengecek anchor pada berkas PDF:
1. **Pindai Dokumen**: Ekstrak teks dari setiap berkas PDF di folder yang ditentukan (misalnya folder `tte29` atau folder kerja lainnya).
2. **Deteksi Simbol**: Periksa keberadaan simbol-simbol anchor valid (`^`, `#`, `$`, `*`) di seluruh halaman dokumen.
3. **Validasi Teks**: Pastikan anchor terbaca sebagai teks digital (vektor/TrueType), bukan gambar pindaian/scan raster, sehingga dapat dideteksi oleh mesin TTE Kemenag.
4. **Cek Konteks & Pejabat**: Cocokkan posisi anchor terhadap nama pejabat penandatangan dan konfigurasi di `config.json`.
5. **Sajikan Laporan Lengkap**:
   - Nama berkas & jumlah halaman.
   - Simbol anchor yang ditemukan.
   - Posisi/baris teks di sekitar anchor.
   - Pejabat penandatangan terkait.
   - Kesimpulan apakah anchor sudah lengkap dan siap diunggah.
