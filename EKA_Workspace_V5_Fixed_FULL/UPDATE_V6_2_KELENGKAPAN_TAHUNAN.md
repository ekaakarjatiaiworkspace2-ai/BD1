# V6.2 — Kelengkapan dokumen Angga per tahun

Di **Data → Arsip laporan tahunan**, pilih tahun laporan, jenis dokumen, unit bisnis, dan kebutuhan data. Tahun 2021, 2022, dan tahun lain dicatat secara terpisah; dokumen suatu tahun tidak melengkapi tahun lainnya.

Pada bagian **Kapan pengumpulan dokumen dianggap Done?**, pilih patokan yang sesuai:

| Patokan | Syarat Done |
| --- | --- |
| Fleksibel (bawaan) | Satu laporan tahunan, atau empat kuartal, atau dua belas bulan tersedia. |
| Tahunan saja | Laporan tahunan tersedia. Bulanan dan kuartalan tidak diperlukan. |
| Kuartalan | Kuartal 1 sampai 4 tersedia. |
| Bulanan | Januari sampai Desember tersedia. |
| Periode tertentu | Semua periode yang dicentang tersedia. Catatan alasan wajib diisi. |

Contoh: untuk 2021 hanya ada laporan tahunan. Pilih **Tahunan saja**, isi catatan ketersediaan, lalu unggah file dengan periode **Tahunan**. Sistem mencatat **Done — dokumen lengkap**, **1/1 periode**, tanpa menandai dua belas bulan sebagai kekurangan.

Gunakan **Simpan kebutuhan tahun ini** untuk menyimpan pola dan catatan meskipun dokumennya belum diunggah. Saat mengunggah, pengaturan juga disimpan bersama batch dalam satu transaksi. Jika unggahan gagal, pengaturan batch dan dokumen yang baru ditambahkan dibatalkan bersama.

Ringkasan menunjukkan persentase, jumlah file, periode yang masih kurang, dan riwayat kelengkapan tahun-tahun yang pernah diunggah atau diatur. Tombol tahun pada riwayat membuka pola tahun tersebut. Perubahan jenis dokumen, unit, atau tahun memuat pengaturan untuk lingkup yang baru.

Status dihitung dari periode dokumen, sehingga beberapa file atau versi pada bulan yang sama tidak menggandakan progres. Unggahan tahunan V6 yang sudah ada langsung ikut dihitung tanpa perlu diunggah ulang. Perubahan menuju Done atau kembali belum lengkap dicatat di audit.

**Done adalah kelengkapan pengumpulan dokumen.** Pemeriksaan kebenaran isi data tetap tercatat terpisah dan mengikuti kewenangan reviewer. Sistem tidak otomatis menerima hasil tugas atau menyatakan data valid hanya karena ada file.

Untuk memakai pembaruan, hentikan server lama dengan **Ctrl+C**, jalankan `go`, lalu muat ulang browser dengan **Ctrl+F5**. Tabel pengaturan ditambahkan otomatis tanpa menghapus data yang sudah ada.

Pengujian API: `python -m pytest tests/test_document_coverage.py tests/test_document_cloud.py tests/test_workflow.py tests/test_pg_adapter.py -q`. Pengujian browser: `node tests/account_menu.cjs`.
