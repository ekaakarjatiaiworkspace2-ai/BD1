# Migrasi data V5 lokal → Cloud

Jika V5 sudah berisi pekerjaan, password yang telah diganti, chat atau berkas, jangan mulai ulang dari nol.

1. **Hentikan V5**, backup seluruh folder `data` (database + `uploads`) ke media terenkripsi.
2. Siapkan database PostgreSQL dan bucket R2 privat. Pastikan cloud V6 dapat dijalankan dengan konfigurasi hosting dan belum digunakan untuk pekerjaan nyata.
3. Jalankan pemeriksaan jumlah data **di komputer sendiri**:
   `python scripts/migrate_v5_sqlite_to_cloud.py --source "C:\\lokasi\\EKA_V5\\data"`
4. Pastikan jumlah akun, pekerjaan, pesan dan berkas masuk akal.
5. **Sebelum impor sungguhan**, buat backup database target serta simpan snapshot data asli. Database target sebaiknya hanya berisi data seed V6 (tanpa kerja baru).
6. Pada komputer admin yang memiliki akses sementara ke URL Postgres target dan kredensial bucket, set `DATABASE_URL`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, lalu:
   `EKA_IMPORT_CONFIRM=I_HAVE_A_BACKUP` dan jalankan perintah yang sama dengan `--apply`.
7. Skrip menyalin akun beserta password hash, catatan proyek, pesan, persetujuan, audit, serta seluruh berkas. Berkas lama diberikan label *migrasi V5*; **tahun hasil inferensi nama file perlu diperiksa ulang**.
8. Pastikan file lama dapat diunduh pada akun yang berwenang, jumlah record dan status sesuai. Login dengan password terakhir V5 yang sudah dipakai.
9. Simpan backup asli dengan aman sampai uji pemulihan selesai; jangan unggah database SQLite ke repository.

Skrip menolak impor kedua kali dan menolak database target yang sudah berisi pesan/file. Tidak mencakup otomatisasi merge dua basis data yang sama-sama sudah aktif. Untuk migrasi produksi, jalankan bersama admin server dan lakukan *maintenance window*.
