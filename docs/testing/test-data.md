# Rencana data dan akun pengujian

Tanggal: 18 Oktober 2026. Status: spesifikasi fixture; belum ada akun, database, file wajah atau data nyata yang dibuat.

## Data sintetis administratif

| Fixture | Isi | Tujuan |
|---|---|---|
| ACC-SA, ACC-ADMIN, ACC-OP, ACC-VIEW | Username test_sa/test_admin/test_operator/test_viewer; empat role PRD | Matriks akses; password dibuat acak saat seed uji, bukan password produksi/default |
| ACC-LOCK, ACC-RESET | Akun khusus lockout dan reset | Kegagalan login/session/reset tanpa mengunci admin uji |
| GRP-A, GRP-B | Kelas 10A dan IT | Filter, pindah group, relasi; contoh lintas organisasi tidak dicampur dalam satu tenant tanpa definisi |
| SHIFT-DAY | 08:00-17:00, grace 10 menit | Present/Late/early leave |
| SHIFT-NIGHT | 20:00-04:00, grace 10 menit | Shift lintas hari dan tanggal kerja |
| MEM-A, MEM-B | SG-TEST-0001/0002; nama Anggota Uji A/B, group berbeda, aktif | Registrasi, filter dan reassign |
| MEM-INACTIVE | SG-TEST-0003, nonaktif, attendance historis | Soft delete dan penolakan recognition |
| MEM-LONG | Nama panjang/Unicode, email example.invalid, optional field kosong | UI dan layout ekspor |
| LEAVE-A, CAL-A | Izin satu hari dan hari libur sintetis | Bersyarat D-13, belum menjadi skema final |
| EVENT-A | IN 08:05, OUT 17:00 | Contoh Present |
| EVENT-B | IN 08:11, OUT 16:30 | Late dan early leave (representasi menunggu D-12) |
| EVENT-BOUNDARY | 08:10 tepat; 08:10:00.001; selisih scan 59.999/60/60.001s | Batas grace/cooldown dengan clock terkendali |
| EVENT-NIGHT | IN hari H 20:00, OUT H+1 04:00 | Rekap tanggal kerja shift malam |
| PERF-10K | 10.000 member sintetis, >=5 vector 512D per member, generator seed tetap | Kinerja pencarian, bukan akurasi recognition |

Input URL RTSP tidak valid menggunakan placeholder nonrahasia; test RTSP valid mengambil konfigurasi lokal yang tidak masuk Git. Fixture produksi dan test tidak berbagi credential atau direktori.

## Sampel wajah nyata dan anti-spoof

- Menggunakan relawan dewasa yang menyetujui tujuan dan durasi uji. Jangan mengambil wajah anak sekolah atau orang lain tanpa pengaturan yang disetujui.
- Persetujuan mencakup enrollment, genuine probe, foto cetak/layar dan replay video bila relawan mengizinkan; simpan catatan persetujuan terpisah dari repo.
- Beri ID pseudonim, bukan nama asli; pisahkan mapping identitas dan batasi akses.
- Pisahkan enrollment, pengaturan threshold, dan holdout evaluasi; catat sesi/kamera/cahaya agar tidak terjadi kebocoran data evaluasi.
- Simpan foto, video, embedding dan dump DB hanya di storage lokal terbatas yang diabaikan Git; screenshot bukti tidak boleh membuka identitas tanpa izin.
- Durasi retensi, penanggung jawab, tempat penyimpanan dan cara menghapus salinan/backup harus disepakati sebelum pengumpulan; saat ini belum ada izin pengumpulan atau dataset nyata.
- Jangan menandai test nyata PASS menggunakan gambar sintetis atau vector acak.

## Kriteria kesiapan fixture

- Data administratif dapat dibuat ulang dengan seed tetap pada database test.
- Password sementara tidak tercantum dalam laporan/log.
- Dataset nyata belum siap sampai relawan, izin, penyimpanan dan retensi diputuskan.
- Identitas unknown tidak pernah dimasukkan ke enrollment database uji.

## Demo Dashboard Tahap 11

`scripts/demo_dashboard.py` memakai schema milik demo di stargate_test dan folder sementara .local. Lima anggota sintetis memberi angka awal aktif 5/Hadir 2/Terlambat 1/Absent 1/Izin 1/Belum masuk 1 pada 08:11 WIB. Simulasi check-in memakai AttendanceService/pgvector asli dengan embedding sintetis versi khusus; tidak membuka kamera fisik atau menyalin biometrik kerja. Angka Terlambat merupakan bagian dari Hadir, bukan kategori yang dijumlahkan lagi. Penutupan normal membersihkan schema sendiri; tidak menyapu schema yang bukan milik run ini. Rincian dan batas pada stage-11.md.
