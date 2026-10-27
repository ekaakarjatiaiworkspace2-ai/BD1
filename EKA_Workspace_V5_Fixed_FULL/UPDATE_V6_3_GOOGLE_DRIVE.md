# V6.3 — Unggah file atau kirim Google Drive

Angga dapat memakai salah satu atau kedua sumber dalam **Data → Arsip laporan tahunan**:

- **Unggah file langsung:** pilih satu atau beberapa Excel/PDF seperti sebelumnya.
- **Google Drive:** isi kolom tautan file/folder Drive, Google Sheets, atau Google Docs. Nama dokumen tautan boleh diisi agar mudah dikenali.

Pilih tahun, unit, jenis dokumen, kebutuhan data, dan periode, lalu klik **Simpan dokumen**. Tidak wajib memilih file jika tautan sudah diisi. Satu pengiriman dibatasi 20 dokumen, termasuk tautan; batas file tetap 25 MB per file.

File dan tautan memakai arsip serta perhitungan kelengkapan yang sama. Contohnya, tautan laporan tahunan 2021 dapat membuat kebutuhan tahunan 2021 **Done** tanpa meminta data bulanan. Ringkasan membedakan jumlah file dan tautan. Status Done tetap berarti pengumpulan lengkap; pemeriksaan isi dokumen mengikuti reviewer.

Di arsip, file memiliki tombol **Unduh** dan tautan memiliki tombol **Buka Google Drive**. Pembukaan tautan melalui aplikasi tetap memeriksa hak akses akun. Tautan yang menunjuk objek Drive yang sama pada tahun, unit, kebutuhan, dan periode yang sama dilewati sebagai duplikat, termasuk jika format tautan berbagi berbeda.

Tautan dicatat sebagai referensi, tanpa mengunduh isi Drive ke penyimpanan aplikasi. **Angga perlu memberi akses Google Drive kepada akun reviewer.** Izin Drive tidak diubah atau diverifikasi otomatis. Isi file yang berubah pada URL Drive yang sama mengikuti sumber Drive; aplikasi tidak membuat salinan versi isi Drive.

Server hanya menerima tautan HTTPS ke `drive.google.com` atau `docs.google.com` dengan pola dokumen/folder yang didukung. Tautan tidak valid membatalkan seluruh pengiriman, termasuk file yang disertakan. Isian formulir tetap tersedia untuk percobaan ulang.

Data dan akun lama tetap menggunakan skema yang sama. Untuk menjalankan pembaruan, hentikan server lama (**Ctrl+C**), jalankan `go`, lalu tekan **Ctrl+F5** pada browser.

Verifikasi API: `python -m pytest tests/test_document_links.py tests/test_document_coverage.py tests/test_document_cloud.py tests/test_workflow.py tests/test_pg_adapter.py -q`.

Verifikasi browser: `node tests/account_menu.cjs`.
