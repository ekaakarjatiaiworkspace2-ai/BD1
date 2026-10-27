# EKA Workspace V6.1 — Unggah dokumen tahunan sekaligus

Penyesuaian paket `EKA_Workspace_Cloud_V6_Hosting_Upload_Tahunan.zip` pada proyek yang sudah ada.

## Cara Angga mengunggah dokumen

1. Masuk sebagai Angga, lalu buka **Data → Arsip laporan tahunan**.
2. Isi **Tahun laporan**, misalnya **2023**.
3. Pilih **Jenis dokumen → Laporan Keuangan**, lalu kebutuhan data yang sesuai, unit bisnis, dan periode.
4. Pilih beberapa Excel/PDF sekaligus dari pemilih file. Periksa daftar nama dan jumlah file.
5. Klik **Unggah dokumen**. Hasilnya muncul pada arsip tahun, jenis dokumen, dan unit yang sama.

Maksimal **20 file per batch**, masing-masing **25 MB**. Format yang didukung mengikuti V6: PDF, XLSX, XLS, CSV, DOCX, PNG, JPG, JPEG, WEBP, dan TXT.

File dengan nama dan isi identik dalam tahun, unit, periode, dan kebutuhan data yang sama dilewati. Isi baru dengan nama yang sama mendapat nomor versi berikutnya. Dokumen tetap memerlukan pemeriksaan Ahmad sebelum data berstatus siap.

## Perilaku saat gagal

Semua file divalidasi sebelum penyimpanan. Jika validasi atau penyimpanan satu file gagal, catatan database untuk batch dibatalkan dan file yang baru ditulis dibersihkan. Pilihan file tetap tersedia untuk mencoba kembali. Filter arsip tidak menghapus file yang sedang dipilih.

## Kompatibilitas

- Akun, hash kata sandi, sesi, pekerjaan, dan lampiran V5 dipertahankan.
- Tabel indeks dokumen ditambahkan otomatis pada database lama saat server mulai.
- Lampiran lama tetap bisa diunduh dari rincian kebutuhan data. Lampiran lama tidak diberi tahun secara otomatis karena tahun sumbernya belum diketahui.
- Menu akun, tombol keluar, tombol mata kata sandi, dan perintah `go` tetap tersedia.
- CSS, JavaScript, serta cache PWA diperbarui ke versi 6.1.

## Lokal dan hosting

Untuk menjalankan lokal, hentikan server lama lalu jalankan `go`. Muat ulang browser dengan **Ctrl + F5**. Di terminal lama yang belum mengenal `go`, jalankan `. .\go.ps1` terlebih dahulu, atau gunakan `.\golive`.

Dukungan PostgreSQL dan penyimpanan S3 privat disertakan dari paket V6. Pengujian pada proyek ini menggunakan SQLite dan penyimpanan lokal. Lihat `PANDUAN_DEPLOY_HOSTING.md` untuk konfigurasi hosting dan `PANDUAN_MIGRASI_DATA_V5.md` untuk perpindahan ke PostgreSQL. Perubahan kode ini tidak menerbitkan aplikasi ke hosting.

## Verifikasi

- API: `python -m pytest tests/test_workflow.py tests/test_document_cloud.py tests/test_pg_adapter.py -q` (memerlukan pytest dan httpx).
- Browser: `node tests/account_menu.cjs` (Windows, Chrome, dan virtual environment Python).
- Pengujian memakai database sementara dan dokumen dummy, mencakup pengelompokan tahun/jenis/unit, versi, duplikat, batas file, kegagalan batch, akses akun, serta kompatibilitas lampiran V5.
