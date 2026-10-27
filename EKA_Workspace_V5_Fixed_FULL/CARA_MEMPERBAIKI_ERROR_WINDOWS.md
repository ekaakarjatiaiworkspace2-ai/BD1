# Perbaikan startup Windows — EKA Workspace V5

## Masalah yang diperbaiki

Jika saat menjalankan `JALANKAN_WINDOWS.bat` muncul pesan:

```text
... was unexpected at this time.
```

maka sumber masalahnya adalah sintaks pada launcher batch dari paket sebelumnya (tanda kurung dalam perintah `echo` di dalam blok `if`). **Tidak perlu menghapus database, file proyek, atau data pengguna.**

## Cara paling mudah — hanya ganti satu file

1. Tutup server jika sedang berjalan (`Ctrl+C`).
2. Buka folder proyek V5 yang sudah diekstrak di komputer.
3. Ganti file `JALANKAN_WINDOWS.bat` dengan file perbaikan dari paket ini.
4. Dari PowerShell di dalam folder tersebut, jalankan:

```powershell
.\JALANKAN_WINDOWS.bat
```

5. Tunggu sampai terminal menampilkan alamat aplikasi, lalu buka `http://127.0.0.1:8000`.
6. Jangan tutup terminal ketika menggunakan aplikasi.

## Alternatif: instalasi paket lengkap yang telah diperbaiki

Ekstrak ZIP **EKA_Workspace_V5_Fixed_FULL.zip** ke folder baru. Buka folder itu di VS Code, lalu jalankan `JALANKAN_WINDOWS.bat`. Jika sebelumnya sudah mengisi data, **jangan hapus folder lama**. Simpan salinan folder `data` lama (termasuk `project.sqlite3`, uploads, dan file akun). Salin folder `data` lama ke proyek baru *sebelum* menjalankan aplikasi.

## Jika file batch masih bermasalah

Jalankan perintah ini **satu per satu** di terminal PowerShell dalam folder proyek:

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Jika `py` tidak ditemukan, gunakan `python` untuk dua baris yang menggunakan `py -3`. Python 3.11+ diperlukan.

## Untuk dibuka di HP

1. Jalankan `JALANKAN_JARINGAN_WINDOWS.bat` hanya pada jaringan internal terpercaya.
2. Pastikan HP dan komputer berada di Wi-Fi sama dan firewall Windows memberi izin yang diperlukan.
3. Buka `http://ALAMAT-IP-KOMPUTER:8000` dari browser HP.
4. PWA yang dapat diinstal secara normal memerlukan HTTPS valid atau lingkungan localhost. Akses HTTP melalui IP jaringan tidak otomatis memungkinkan pemasangan PWA.

**Jangan membuka port langsung ke internet.** Aplikasi masih ditujukan untuk uji coba lokal; penggunaan dengan data sensitif perusahaan membutuhkan server dan konfigurasi keamanan yang benar.
