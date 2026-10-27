> **Update perbaikan startup Windows:** Jika paket sebelumnya gagal dengan pesan `... was unexpected at this time.`, launcher Batch kini diperbaiki. Baca `CARA_MEMPERBAIKI_ERROR_WINDOWS.md`.

# EKA Workspace V6.3 — PT Eka Akar Jati

Versi ini menggabungkan paket Cloud V6 dengan proyek lokal dan menambahkan unggah batch berdasarkan tahun serta jenis dokumen. Panduan fitur terbaru ada di [UPDATE_V6_BATCH_UPLOAD.md](UPDATE_V6_BATCH_UPLOAD.md).

V6.2 menambahkan [kelengkapan per tahun](UPDATE_V6_2_KELENGKAPAN_TAHUNAN.md): laporan tahunan 2021, 2022, dan tahun lainnya dapat berstatus **Done** tanpa diwajibkan melengkapi data bulanan. Pilih patokan fleksibel, tahunan, kuartalan, bulanan, atau periode tertentu sesuai kebutuhan kajian.

V6.3 menambahkan [tautan Google Drive](UPDATE_V6_3_GOOGLE_DRIVE.md): Angga boleh mengunggah file langsung, mengirim tautan Drive saja, atau memakai keduanya. Tautan ikut tercatat dalam arsip dan kelengkapan periode.

Aplikasi web pilot internal, dengan **logo resmi EKA**, dashboard desktop, tampilan mobile, dan dukungan **PWA (Add to Home Screen)**. Dibuat sebagai satu folder proyek yang dapat langsung dibuka di VS Code. Tidak perlu memasang patch V4.2 terlebih dahulu.

## Menjalankan di VS Code (Windows)

1. Ekstrak ZIP, buka folder `EKA_Workspace_V5_Logo_Mobile` di VS Code. Pastikan terlihat `app.py` dan `golive.bat`.
2. Pastikan Python 3.11+ terpasang.
3. Tutup terminal lama dengan ikon tempat sampah, lalu pilih **Terminal → New Terminal**. Terminal **EKA PowerShell** akan otomatis memuat perintah proyek. Jalankan:

```powershell
go
```

   Pengaturan ada di `.vscode/settings.json`, sehingga ikut terbawa bersama folder proyek. Untuk langsung memakai terminal lama, jalankan `. .\go.ps1` (ada titik dan spasi di depan), lalu ketik `go`. Launcher `.\golive` juga tetap tersedia.

4. Tunggu server aktif, buka `http://127.0.0.1:8000` di browser **komputer server**.
5. File `data/AKUN_AWAL.txt` **baru muncul setelah server pertama kali dijalankan**. Di dalamnya ada password acak untuk akun `ahmad`, `donny`, `angga`, `management`. Jangan kirim file ini ke orang lain. Masuk dengan masing-masing akun lalu ganti password melalui Pengaturan akun.

Jika terminal belum berada di folder proyek, gunakan menu **File → Open Folder** di VS Code. Folder yang dibuka harus berisi `app.py` langsung, bukan hanya folder induk.

## Unggah dokumen banyak tahun

Masuk sebagai Angga, buka **Data → Arsip laporan tahunan**, pilih **tahun**, **jenis dokumen**, kebutuhan data, unit bisnis dan periode. Pilih beberapa Excel/PDF, isi **tautan Google Drive**, atau gunakan keduanya, lalu klik **Simpan dokumen**. Maksimal **20 dokumen per pengiriman**, masing-masing file maksimal **25 MB**. Ulangi dengan tahun berikutnya untuk laporan tahun lain.

Arsip dapat difilter berdasarkan tahun, jenis dokumen, dan unit bisnis. File identik dilewati dan revisi dengan nama sama disimpan sebagai versi berikutnya. Jika satu file gagal, batch dibatalkan agar tidak tersimpan sebagian.

Konfigurasi hosting PostgreSQL/S3 disertakan dari ZIP V6; lihat [PANDUAN_DEPLOY_HOSTING.md](PANDUAN_DEPLOY_HOSTING.md). Akun dan lampiran lokal yang sudah ada dipertahankan saat pembaruan skema.

## Menjalankan dari HP

**Penting:** aplikasi ini *PWA/web app*, **bukan APK/IPA native**. Fitur bekerja di browser HP. Untuk memasang ke layar utama HP seperti aplikasi, dibutuhkan URL HTTPS yang dapat diakses HP.

**Uji coba dari HP dalam Wi-Fi yang sama:**

1. Pastikan laptop dan HP tersambung jaringan internal terpercaya, tanpa VPN yang mengisolasi perangkat.
2. Hentikan server lokal (Ctrl+C) lalu jalankan `JALANKAN_JARINGAN_WINDOWS.bat`, konfirmasi `YA`.
3. Cari IPv4 komputer melalui `ipconfig` (contoh `192.168.1.20`).
4. Di browser HP buka `http://192.168.1.20:8000` (IP sesuaikan dengan komputer Anda). Jika gagal, periksa aturan firewall Windows dan apakah perangkat saling terhubung; **jangan membuka port router ke internet**.
5. Browser HP bisa menggunakan tampilan responsif. Namun pemasangan PWA/service worker membutuhkan **HTTPS** pada alamat HP (kecuali localhost pada perangkat yang sama). Untuk penggunaan serius, siapkan reverse proxy HTTPS di server/domain privat yang disetujui tim IT.
6. Setelah HTTPS tersedia, Android: menu browser → **Install app / Add to Home screen**. iPhone Safari: Share → **Add to Home Screen**. Status instalasi bergantung dukungan browser/OS.

**Jangan mengunggah data keuangan asli sensitif** selama server jaringan belum diamankan dengan TLS/HTTPS, kebijakan backup, kontrol jaringan, dan review keamanan.

## Isi proyek

- `app.py` — login, pembatasan hak akses dari server, tugas, data, chat, dokumen, keputusan, audit SQLite.
- `seed.py` — 13 tugas besar, 64 subtask, 120 kebutuhan data awal. Status awal belum diminta/belum mulai; **bukan data asli perusahaan**.
- `static/index.html`, `static/style.css`, `static/app.js` — tampilan responsif.
- `static/assets/eka-logo-resmi.png` — logo asli dari pengguna; ikon aplikasi dibuat dari potongan lambang resmi.
- `static/manifest.webmanifest`, `static/sw.js` — dukungan PWA. PWA tidak menyimpan data kerja sensitif secara offline.
- `data/` — database, dokumen unggahan, password awal; tidak masuk ZIP rilis.
- `tests/` — pengujian hak akses, proses review, dan tampilan browser.

## Fitur kerja

- Ahmad: empat tugas besar BD/R&D, Kelola Tim, data, tools, Timeline, meeting, chat, review pekerjaan.
- Donny: empat tugas besar DS, checklist, hasil pengujian dan tools, data terkait.
- Angga: tiga tugas besar Finance dan 120 kebutuhan data awal.
- Management: ringkasan progres empat fungsi, dua tugas pemeriksaan, meeting yang dibagikan, keputusan, dan Timeline ringkas.
- Subtask **baru dianggap selesai setelah reviewer menyetujui**. Data diterima tidak otomatis siap digunakan. Jadwal dapat diubah Ahmad dengan alasan dan target awal tidak ditimpa.

## Perbedaan dengan V4.1/V4.2 dan migrasi

**Source code lengkap V4.1 tidak tersedia dalam sesi pembuatan paket ini**, sehingga ini adalah aplikasi V5 mandiri yang mempertahankan *konsep kerja* sebelumnya, **bukan upgrade database V4.1 yang diuji kompatibel**. Data V4 lama **tidak otomatis terbawa**. Simpan folder V4 beserta database, akun dan berkas sebelumnya. Jangan menyalin SQLite V4 langsung ke folder `data` V5: skemanya tidak dijamin sama. Import data lama harus melalui proses migrasi terpisah dengan contoh backup, pemeriksaan skema dan UAT; jangan menghapus instalasi lama sebelum itu.

## Status produk

Ini **pilot lokal yang berfungsi**, bukan sistem produksi bank, bukan layanan cloud publik, dan **belum** mempunyai mesin NPV/IRR/DSCR otomatis. Daftar tools tersebut berupa pekerjaan Data Science yang perlu dikembangkan kemudian. SQLite dipakai untuk pilot; untuk penggunaan bisnis multiuser produksi, perlu migrasi keamanan, operasi server, audit file, backup, hardening, dan pengujian skala.
