"""Blueprint EKA: 13 tugas besar, 64 subtask dan 120 kebutuhan data awal.
Data awal merupakan permintaan, BUKAN dokumen keuangan aktual.
"""
from datetime import date,timedelta
START='2026-10-26'
MACROS=[
('BD-01','BD','ahmad','Pengaturan Proyek & Kebutuhan Kajian','Memastikan arah kajian, data, jadwal, dan PIC jelas','Rencana kerja, pembagian tugas, dan bahan rapat',0),
('BD-02','RND','ahmad','Riset Pasar & Konsep Bisnis','Membuktikan pasar, pelanggan, pesaing dan konsep hotel','Laporan pasar dan rekomendasi konsep',2),
('BD-03','RND','ahmad','Peluang Pengembangan Bisnis','Menemukan peluang pendapatan, efisiensi dan kemitraan','Daftar peluang dan tiga strategi pertumbuhan',4),
('BD-04','BD','ahmad','Rekomendasi & Roadmap Investasi','Membandingkan strategi dan menyiapkan keputusan manajemen','Laporan rekomendasi dan roadmap',6),
('FIN-01','FIN','angga','Pengumpulan Data Keuangan & Investasi','Menyediakan laporan keuangan dan data biaya proyek','Paket data keuangan dan investasi',1),
('FIN-02','FIN','angga','Penyiapan Data Pembiayaan','Menyiapkan informasi utang, modal, angsuran dan bank','Data pinjaman, angsuran, sumber dana',2),
('FIN-03','FIN','angga','Pemeriksaan & Finalisasi Data','Memastikan data sumber tercatat serta kekurangannya jelas','Daftar data valid dan catatan klarifikasi',4),
('DS-01','DS','donny','Alat Pengolahan Data Awal','Membersihkan dan menstandarkan data sumber','Alat impor dan laporan kualitas data',2),
('DS-02','DS','donny','Alat Perhitungan Kelayakan','Membangun model keuangan 10 tahun dan pembiayaan','Model arus kas, NPV, IRR, Payback dan DSCR',4),
('DS-03','DS','donny','Alat Simulasi Pengembangan Bisnis','Menguji target balik modal serta tiga strategi pertumbuhan','Reverse feasibility dan perbandingan strategi',5),
('DS-04','DS','donny','Pengujian & Penyerahan Tools','Menguji rumus, antarmuka, dan hasil model','Alat teruji, panduan, riwayat versi',6),
('MGT-01','MGMT','management','Pemeriksaan Hasil Kelayakan','Menilai ketepatan data, asumsi, dan risiko investasi','Keputusan menerima kajian atau meminta revisi',6),
('MGT-02','MGMT','management','Pemilihan Strategi & Persetujuan','Menetapkan pilihan investasi dan tindak lanjut','Keputusan dan persyaratan pelaksanaan',6)
]
SUBTASKS={
'BD-01': [('Tujuan dan batas kajian','Tentukan objek investasi;Catat target manajemen;Catat batas modal dan risiko'),('Kebutuhan penelitian','Daftar pertanyaan riset;Daftar sumber data;Tentukan cara memeriksa'),('Pembagian tugas tim','Tentukan penanggung jawab;Tentukan batas waktu;Tentukan hasil per bagian'),('Pemantauan kendala','Periksa progres;Catat kendala dan PIC;Tentukan tindakan lanjut'),('Bahan rapat','Ringkas hasil;Catat data belum siap;Buat pertanyaan keputusan')],
'BD-02':[('Riset industri dan lokasi','Cari statistik wilayah;Analisis penggerak permintaan;Simpan sumber'),('Riset pelanggan','Petakan segmen;Wawancara pelanggan;Uji harga'),('Riset kompetitor','Daftar hotel pembanding;Bandingkan harga dan fasilitas;Rangkum posisi pasar'),('Pemeriksaan aset','Periksa kondisi aset;Catat kapasitas;Minta ahli memeriksa keterbatasan teknis'),('Konsep bisnis hotel','Susun pilihan konsep;Tentukan sasaran pelanggan;Validasi asumsi komersial')],
'BD-03':[('Pemetaan peluang','Daftar optimasi hotel;Daftar diversifikasi;Catat sumber ide'),('Validasi pasar','Teliti permintaan;Uji harga;Rangkum bukti dan ketidakpastian'),('Model pendapatan','Rancang produk;Tentukan volume dan harga;Pilih cara pemasaran'),('Kemitraan dan efisiensi','Identifikasi calon mitra;Rancang manfaat sinergi;Hitung biaya pendukung'),('Tiga strategi pertumbuhan','Defensive dengan kegiatan nyata;Balanced bertahap;Accelerated dan modal tambahan'),('Prioritas peluang','Bandingkan pasar dan modal;Bandingkan risiko;Pilih peluang untuk dimodelkan')],
'BD-04':[('Review model investasi','Baca baseline;Periksa sensitivitas;Catat batas kajian'),('Perbandingan strategi','Bandingkan 3 pilihan;Periksa tambahan modal;Catat risiko'),('Rekomendasi investasi','Susun pilihan utama;Tuliskan alasan;Sertakan alternatif'),('Roadmap pelaksanaan','Tetapkan urutan;Tentukan PIC;Tentukan syarat tiap tahap'),('Laporan dan tindak lanjut','Satukan lampiran;Siapkan meeting;Catat tindak lanjut')],
'FIN-01':[('Laporan keuangan','Laba rugi historis;Neraca historis;Arus kas historis'),('Kas dan modal kerja','Saldo kas dan rekening;Piutang;Utang usaha'),('Biaya perusahaan','Data gaji;Operasional rutin;Biaya tetap dan variabel'),('Data aset','Daftar aset;Investasi historis;Bukti kepemilikan'),('Data proyek hotel','RAB dari pemilik proyek;Realisasi pembayaran;Sisa biaya dan tagihan'),('Dokumen pendukung','Buku besar;Trial balance;Keterangan dan periode dokumen')],
'FIN-02':[('Pinjaman berjalan','Daftar kreditur;Saldo pokok;Bunga dan tenor'),('Jadwal angsuran','Pokok jatuh tempo;Bunga jatuh tempo;Kewajiban lainnya'),('Sumber modal','Modal internal;Pinjaman baru;Sumber dana alternatif'),('Penawaran bank','Syarat bunga/margin;Masa tenggang;Biaya dan agunan'),('Risiko kewajiban','Jaminan;Covenants;Komitmen perusahaan')],
'FIN-03':[('Periksa kelengkapan','Cocokkan permintaan;Tandai data kurang;Konfirmasi penyedia'),('Periksa periode dan angka','Cek tanggal laporan;Rekonsiliasi selisih;Tandai data tidak konsisten'),('Klarifikasi dan perbaikan','Minta penjelasan;Lampirkan koreksi;Catat versi'),('Konfirmasi kesiapan','Cek kesesuaian sumber Finance;Tandai keterbatasan legal dan teknis;Serahkan daftar data valid')],
'DS-01':[('Format input','Tentukan kolom;Petakan akun;Tentukan periode'),('Alat pemasukan data','Impor file;Tangani format salah;Uji data kosong'),('Kebersihan data','Hapus duplikat;Periksa anomali;Standarkan dataset'),('Analisis awal','Hitung tren;Hitung rasio;Bandingkan dengan sumber'),('Uji alat','Jalankan data contoh;Periksa hasil;Catat error')],
'DS-02':[('Pendapatan dan biaya','Susun driver pendapatan;Susun biaya operasi;Pisahkan lini usaha'),('Modal dan arus kas','Susun CAPEX;Modal kerja;Periode cash flow'),('Pembiayaan','Jadwal pencairan;Pokok dan bunga;Saldo kewajiban'),('Hasil kelayakan','NPV;IRR;Payback;DSCR dan definisinya'),('Sensitivity analysis','Penurunan omzet;Kenaikan biaya;Keterlambatan proyek'),('Pemeriksaan model','Uji formula;Rekonsiliasi arus kas;Dokumentasikan asumsi')],
'DS-03':[('Target manajemen','Target pengembalian;Batas modal;Batas risiko'),('Reverse cash flow gap','Hitung kondisi dasar;Hitung kebutuhan kas per tahun;Uji target realistis'),('Input peluang usaha','Tambahan CAPEX;Tambahan biaya;Tanggal mulai pendapatan'),('Tiga strategi pertumbuhan','Defensive;Balanced;Accelerated'),('Pisahkan objek investasi','Hotel standalone;Hotel dan ekspansi;Portofolio EKA'),('Bandingkan hasil','Tambahan modal;NPV IRR Payback DSCR;Uji risiko')],
'DS-04':[('Tampilan input & hasil','Form input;Label angka jelas;Sumber perhitungan'),('Uji fitur dan hitung','Test input;Test rumus;Test skenario ekstrem'),('Tangani data buruk','Data kosong;Angka tidak masuk akal;Kesalahan format'),('Dokumentasi dan versi','Panduan;Penjelasan rumus;Riwayat perubahan'),('Penyerahan alat','Kirim versi dan hasil uji;Minta review;Perbaiki temuan')],
'MGT-01':[('Kondisi keuangan','Baca ringkasan;Periksa kebutuhan modal;Catat pertanyaan'),('Kelayakan dan risiko','Review return;Review DSCR;Periksa risiko'),('Keputusan hasil kajian','Terima atau minta revisi;Catat alasan;Tetapkan tindak lanjut')],
'MGT-02':[('Perbandingan strategi','Periksa tiga pilihan;Cek modal tambahan;Cek risiko'),('Kapasitas pendanaan','Periksa kemampuan angsuran;Sumber dana;Batas modal'),('Persetujuan dan tindak lanjut','Setujui/tunda/tolak;Tuliskan alasan;Tetapkan PIC berikutnya')]
}
DATA_GROUPS={
'Laporan Keuangan': ['Laba rugi','Neraca','Arus kas','Trial balance','Buku besar','Catatan laporan keuangan','Laporan audit','Realisasi anggaran','Rincian penyusutan','Laporan pajak'],
'Kas dan Modal Kerja':['Rekening koran','Saldo kas','Aging piutang','Aging utang usaha','Persediaan','Utang pajak','Perputaran kas','Pembayaran pemasok','Kontrak pelanggan','Rencana modal kerja'],
'Pembiayaan dan Agunan':['Daftar kreditur','Saldo pinjaman','Jadwal cicilan','Perjanjian kredit','Bunga pinjaman','Ketentuan covenant','Daftar agunan','Nilai agunan','Jaminan perusahaan','Penawaran bank'],
'Konstruksi Hotel':['RAB detail','Progress fisik','Progress pembayaran','Sisa pekerjaan','Kontrak kontraktor','Jadwal penyelesaian','Daftar peralatan','Daftar tagihan','Cadangan biaya','Berita acara pekerjaan'],
'Sumber dan Penggunaan Dana':['Investasi sudah keluar','Kebutuhan penyelesaian','Modal kerja awal','Biaya pra-operasi','Sumber modal sendiri','Pinjaman usulan','Pencairan bertahap','Cadangan bunga','Biaya pendanaan','Anggaran kontinjensi'],
'Riset Pasar':['Statistik kunjungan','Permintaan kamar','Daftar kompetitor','Tarif hotel pesaing','Occupancy pesaing','Segmen pelanggan','Survei perusahaan','Musim kunjungan','Permintaan MICE','Akses lokasi'],
'Operasional dan Pendapatan':['Jumlah kamar','Tarif rata-rata','Okupansi rencana','Pendapatan F&B','Meeting package','Biaya housekeeping','Biaya energi','Biaya payroll','Pemasaran','Pemeliharaan'],
'Legal dan Perizinan':['Sertifikat tanah','Izin bangunan','Izin operasional','Status zonasi','Dokumen lingkungan','Persetujuan usaha','Syarat pajak lokal','Status sengketa','Kontrak tanah','Dokumen asuransi'],
'Risiko dan Skenario':['Asumsi inflasi','Kenaikan biaya','Penurunan okupansi','Perubahan bunga','Risiko konstruksi','Biaya keterlambatan','Risiko karyawan','Risiko pemasaran','Asumsi diskonto','Nilai akhir aset'],
'Sinergi dan Ekspansi':['Peluang sewa ruang','Daftar calon mitra','Paket corporate','Training & meeting','Long-stay','Katering','Diversifikasi usaha','Biaya ekspansi','Waktu go-live','Kontrak calon pelanggan'],
'Target Manajemen dan Governance':['Target balik modal','Target IRR','Batas CAPEX','Batas pinjaman','Batas DSCR','Batas risiko','Jadwal keputusan','Penanggung jawab','Pihak penilai','Rencana mitigasi'],
'Profil Perusahaan':['Struktur kepemilikan','Entitas usaha','Produk utama','Pendapatan per bisnis','Margin per bisnis','Daftar aset','Arus kas per unit','Kontrak utama','Proyeksi existing','Rencana bisnis korporasi']}
assert sum(len(v) for v in SUBTASKS.values())==64
assert sum(len(v) for v in DATA_GROUPS.values())==120

def records():
    result={'tasks':[],'data':[],'tools':[],'meetings':[],'decisions':[]}
    for code,fun,owner,title,purpose,output,idx in MACROS:
        due=str(date.fromisoformat(START)+timedelta(days=idx))
        result['tasks'].append({'id':code,'level':'macro','owner':owner,'function':fun,'title':title,'purpose':purpose,'deliverable':output,'start':START,'due':due,'baseline_due':due,'status':'belum_mulai','weight':1,'queue':'hari_ini' if idx<=1 else 'backlog'})
        for i,(t,check) in enumerate(SUBTASKS[code],1):
            result['tasks'].append({'id':f'ST-{code}-{i:02d}','level':'subtask','parent':code,'owner':owner,'function':fun,'title':t,'purpose':f'Bagian dari {title}.','deliverable':f'Hasil {t} yang dapat diperiksa','checklist':check.split(';'),'completed_checks':[],'actual_result':'','weight':1,'status':'belum_mulai','start':START,'due':due,'baseline_due':due,'block_reason':'','queue':'backlog'})
    idn=0
    for category,labels in DATA_GROUPS.items():
        for label in labels:
            idn+=1
            result['data'].append({'id':f'DATA-{idn:03}','category':category,'title':label,'owner':'angga','source_owner':'Pemilik dokumen terkait','purpose':f'Bahan analisis {category.lower()} dan rekomendasi investasi','status':'belum_diminta','validation':'belum_diperiksa','note':'','source_link':'','received_at':None,'priority':'penting' if label in ('Laba rugi','Neraca','Arus kas','RAB detail','Saldo pinjaman','Jadwal cicilan','Target balik modal') else 'normal'})
    for code,title,macro in [('TOOL-01','Alat pengolahan data','DS-01'),('TOOL-02','Financial Model 10 tahun','DS-02'),('TOOL-03','Reverse Feasibility & Expansion','DS-03'),('TOOL-04','Dashboard analisis','DS-04')]:
        result['tools'].append({'id':code,'title':title,'owner':'donny','macro_id':macro,'status':'direncanakan','objective':'Alat yang harus dibuat dan diuji oleh Data Science','test_result':'','link':'','version':'Belum dibuat','deliverable':'Alat, dokumentasi, dan bukti pengujian'})
    return result
