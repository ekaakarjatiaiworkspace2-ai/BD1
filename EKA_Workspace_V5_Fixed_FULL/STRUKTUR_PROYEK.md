# Struktur folder

```
EKA_Workspace_V5_Logo_Mobile/
├── app.py                    # FastAPI, sesi, peran, tugas, data, bukti
├── seed.py                   # 13 tugas besar, 64 subtask, 120 data awal
├── requirements.txt
├── golive.bat                # Jalankan dengan .\golive di Windows
├── go.ps1                    # Daftarkan perintah go di PowerShell
├── .vscode/settings.json     # Terminal VS Code otomatis memuat perintah go
├── JALANKAN_WINDOWS.bat      # Launcher yang dipanggil oleh golive.bat
├── JALANKAN_JARINGAN_WINDOWS.bat # Uji Wi-Fi internal (hati-hati keamanan)
├── JALANKAN_MAC_LINUX.sh
├── static/
│   ├── index.html            # Layout resmi desktop + mobile
│   ├── style.css             # Style editorial navy EKA, aksesibilitas
│   ├── app.js                # Halaman dashboard dan alur pekerjaan
│   ├── manifest.webmanifest  # PWA
│   ├── sw.js                 # Cache shell statis, BUKAN API/data sensitif
│   └── assets/
│       ├── eka-logo-resmi.png  # File asli, tidak diubah
│       ├── eka-logo-lockup.png # Potongan transparansi logo untuk tampilan
│       ├── eka-emblem.png      # Potongan lambang asli
│       └── eka-icon-192.png, eka-icon-512.png
├── data/                     # Dibuat pertama kali saat server jalan
│   ├── project.sqlite3       # Database SQLite
│   ├── AKUN_AWAL.txt         # Password awal: RAHASIA
│   └── uploads/              # Dokumen pengguna
├── tests/
│   ├── test_workflow.py      # Keamanan dan workflow API
│   └── visual_preview.py     # Pemeriksaan visual memakai data seed nyata
└── README_MULAI_DI_SINI.md
```

**Catatan migrasi:** Berkas V4.1 sebelumnya tidak ada pada sesi pembuatan V5, jadi folder V5 bukan salinan aktual isi V4.1. Backup V4.1 sebelum uji, jangan menyalin database dengan skema yang belum dipastikan kompatibel.
