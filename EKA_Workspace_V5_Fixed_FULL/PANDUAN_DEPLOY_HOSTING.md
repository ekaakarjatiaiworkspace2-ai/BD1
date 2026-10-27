# Panduan Hosting — EKA Workspace Cloud V6

## Rancangan
Browser / PWA (HTTPS) → Render Web Service FastAPI → Render Managed PostgreSQL
                                              → Cloudflare R2 *private bucket*

**PostgreSQL** menyimpan akun, tugas, subtask, status, persetujuan, chat, indeks dokumen, tahun, kategori, dan versi. **R2** menyimpan byte PDF/Excel. Setiap dokumen diunduh melalui server setelah pengecekan hak akses; bucket tidak publik.

## 1. Persiapkan layanan
1. Buat akun Render dan proyek privat GitHub/GitLab.
2. Buat Render **PostgreSQL** di wilayah yang sesuai kebijakan perusahaan. Simpan **Internal Database URL**.
3. Buat bucket Cloudflare R2 (misalnya `eka-documents-private`), **jangan mengaktifkan publikasi file**.
4. Buat R2 API token **terbatas hanya untuk bucket** dan akses yang diperlukan (read/write objek). Catat S3 endpoint, Access Key, Secret.
5. Siapkan password awal terpisah untuk Ahmad, Donny, Angga dan Management (>=12 karakter), serta penanggung jawab admin.
6. Tinjau kewajiban penempatan data, kontrak vendor, backup, dan persetujuan pimpinan. Database dan bucket sebaiknya menggunakan wilayah serta retensi sesuai kebijakan EKA.

## 2. Jalankan aplikasi pada Render
1. Unggah file kode ke **repository privat**. Jangan sertakan folder `data`, `.env`, password, laporan keuangan atau dokumen asli.
2. Render → New Web Service → hubungkan repo tersebut.
3. Runtime Python. Build: `pip install -r requirements.txt`.
4. Start: `uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1`.
5. Tambahkan Environment Variables di Render (gunakan *Secret* jika tersedia):
   - `EKA_DEPLOY_MODE=cloud`
   - `EKA_SECURE_COOKIE=1`
   - `DATABASE_URL` = Internal Database URL dari Render PostgreSQL
   - `S3_BUCKET` = nama bucket privat
   - `S3_ENDPOINT_URL` = URL endpoint R2
   - `S3_REGION=auto`
   - `S3_ACCESS_KEY_ID` & `S3_SECRET_ACCESS_KEY`
   - `EKA_PASSWORD_AHMAD`, `EKA_PASSWORD_DONNY`, `EKA_PASSWORD_ANGGA`, `EKA_PASSWORD_MANAGEMENT` (hanya untuk membuat akun bila database baru/kosong).
6. Health check path: `/api/health`. Jalankan Deploy. Jangan memproses keuangan sebelum seluruh uji lolos.
7. Tambahkan custom domain perusahaan dan pastikan HTTPS. Beri akses hanya kepada personel berwenang; sebaiknya dibatasi melalui Zero Trust/VPN sebelum audit produksi.

**Penting:** jangan menggunakan storage lokal Render untuk dokumen nyata. Mode cloud akan menolak start bila variabel PostgreSQL atau R2 belum lengkap. Secret jangan dikirim melalui chat.

## 3. Uji setelah deployment
- Login masing-masing akun dengan password kuat; segera ganti password awal.
- Angga unggah 2 dokumen *dummy* lewat Data → Arsip laporan tahunan.
- Pastikan kedua file terlihat pada tahun dan kategori yang benar.
- Unggah ulang file sama: dilewati; unggah isi berbeda dengan nama sama: versi 2.
- Ahmad memeriksa data sebelum menjadikannya Siap.
- Uji Donny/Management tidak dapat membuka file yang belum diizinkan.
- Periksa data tetap tersimpan setelah restart dan redeploy.
- Uji akses HP melalui HTTPS dan instal PWA ke layar utama bila sesuai.
- Siapkan snapshot database, aturan backup objek, restore drill, monitoring, dan audit log.

## 4. Ukuran file dan pekerjaan berikutnya
Saat ini maksimal **20 dokumen setiap batch dan 25 MB per file**. Untuk laporan multi-tahun, pilih satu tahun dan satu jenis kebutuhan per batch; unggah berulang untuk tahun berikutnya. Untuk dokumen >25 MB atau ribuan file: fase berikutnya perlu direct-to-bucket multipart/resumable upload, antivirus/quarantine dan worker background.

## 5. Harus dilakukan sebelum penggunaan produksi sensitif
- **Review keamanan** dan pengujian penetrasi oleh tim berkompeten.
- MFA/SSO + proses reset akun + pengelolaan admin.
- Rate limiting di reverse proxy/gateway dan audit aktivitas.
- Malware scanning & quarantine dokumen, pembatasan tipe yang lebih ketat.
- Backup PostgreSQL terjadwal, proteksi retensi/versi dokumen bucket, uji pemulihan.
- Kebijakan retensi, akses, DPA, lokasi data, enkripsi dan persetujuan keuangan/hukum.
- Migrasi database yang terkontrol, pemantauan latensi dan batas unggahan proxy.

Ini paket kode dan konfigurasi untuk deployment — **bukan bukti bahwa server atau layanan cloud sudah dibuat**.
