# Tahap 11 — Dashboard dan monitoring otomatis

Tanggal: 20 Oktober 2026. Review Tahap 10 disetujui pengguna; implementasi/verifikasi otomatis Tahap 11 PASS, menunggu uji mandiri/review pengguna. Tahap 12 belum dimulai.

## Definisi yang digunakan

Pengguna menyetujui definisi berikut pada 20 Oktober 2026: Hadir adalah semua anggota yang sudah check-in; Terlambat merupakan bagian dari Hadir; anggota terjadwal yang belum check-in tetap Belum masuk sampai shift berakhir, lalu Absent; Izin berasal dari catatan izin.

- **Anggota aktif**: jumlah data anggota aktif saat ini, termasuk yang belum memiliki sampel wajah. Ini padanan total registered members; bukan jumlah embedding.
- **Hadir/Terlambat**: orang unik dengan event IN yang sudah tersimpan pada tanggal kerja terpilih. OUT, break, dua kamera dan beberapa sesi dalam satu tanggal tidak menggandakan jumlah orang. Riwayat IN tetap dihitung bila anggota kemudian nonaktif atau mendapat izin setelah IN.
- **Izin/Absent/Belum masuk**: anggota aktif dengan penugasan berlaku pada tanggal kerja, tanpa IN. Izin mengecualikan Absent dan Belum masuk. Tanpa kalender khusus, tanggal penugasan adalah hari kerja; override kalender LOCAL nonhari kerja mengecualikan ketiga hitungan tersebut. Tepat akhir shift sudah Absent bila belum IN.
- Penugasan bertumpang tindih tanpa IN ditandai sebagai konflik dan dikeluarkan dari tiga kategori terakhir; data tidak dipaksakan menjadi angka absensi yang valid.
- Total anggota aktif saat ini berbeda dari statistik historis. Angka Hadir historis dapat melebihi anggota aktif saat ini setelah anggota dinonaktifkan. Statistik izin/jadwal memakai data penugasan dan izin yang tersedia saat query, bukan rekonstruksi versi lama yang belum disimpan.

Dashboard memakai **tanggal kerja**, bukan tanggal kalender setiap event. Shift malam 20:00–04:00 tetap milik tanggal saat mulai; pilih tanggal sebelumnya untuk meninjau shift malam yang masih berlangsung setelah tengah malam. Feed juga mengikuti tanggal kerja terpilih, sehingga OUT pukul 01:00 tetap muncul pada sesi malam tanggal sebelumnya. Tombol `Hari ini` mengembalikan tanggal ke hari ini di zona aplikasi dan mengaktifkan pergantian tanggal otomatis saat tengah malam; memilih tanggal sendiri menghentikan pengikutan tersebut.

Deployment awal satu lokasi: tanggal/jam batas jadwal Dashboard menggunakan zona organisasi di konfigurasi dan kalender lokasi LOCAL. Penugasan belum memiliki relasi lokasi; jangan menganggap perhitungan Absent ini sudah mendukung penugasan lintas lokasi/zona. Scan tetap menyimpan tanggal kerja berdasarkan zona lokasi kameranya sesuai Tahap 10. Editor izin/kalender operasional belum tersedia; contoh uji disiapkan di demo dan fixture.

## Tampilan dan pembaruan

- Menu Dashboard tersedia sesuai izin yang sudah ada: Super Admin, Admin, Operator. Viewer tetap hanya Reports. Tiap pemuatan memvalidasi sesi dan role terbaru.
- Enam kartu ringkasan dan **20 event terbaru**, dengan nama/kode, jenis event, waktu, shift, perangkat dan sumber Scan/Otomatis. Teks/nama ditampilkan sebagai teks biasa, tanpa menampilkan embedding/foto atau sumber RTSP.
- Grafik shift/grup menampilkan maksimal 12 kategori dengan check-in terbanyak. Grup mengikuti `attendance.group_id` historis saat IN; pengubahan grup anggota tidak memindahkan hitungan lama. Jika satu orang mempunyai riwayat IN pada beberapa shift/grup pada satu tanggal, masing-masing kategori dapat memuat orang yang sama; total utama tetap orang unik.
- Tren harian: 30 tanggal kerja sampai tanggal terpilih, satu orang maksimum sekali per hari. Tren bulanan: 12 bulan sampai tanggal terpilih, unit **hari-kehadiran**, bukan orang unik sebulan. Hijau Hadir dan jingga Terlambat tidak dijumlahkan karena Terlambat termasuk Hadir. Tooltip dan nama aksesibel menyediakan label/nilai grafik.
- Pemuatan awal dan polling **setiap 2 detik saat halaman terlihat**, maksimal satu pekerjaan berjalan. Perubahan filter selama pemuatan membuang hasil lama dan meminta data terbaru setelah pekerjaan selesai. Polling bukan jaminan batas keras dua detik bila database/mesin sibuk.
- Query/otorisasi berjalan pada worker, bukan thread GUI. Polling tidak menyentuh aktivitas sesi operator, membuka kamera, memulai inference atau memindahkan fokus. Halaman tersembunyi berhenti polling; logout/penutupan menunggu worker aman selesai. Navigasi dari Kehadiran tetap menghentikan scan sesuai aturan Tahap 10.
- Snapshot query memakai batas transaksi/lock autentikasi yang sama dengan penulis resmi aplikasi, termasuk terminal lain pada database sama. Tidak menambah cloud sync maupun penulis SQL luar aplikasi. Feed hanya memuat event committed, bukan optimisme dari frame kamera.
- Database gagal: status menyatakan data belum diperbarui, angka terakhir tidak diganti nol palsu. Role/sesi ditolak: data dikosongkan dan jalur penolakan sesi aplikasi dijalankan. Data kosong ditampilkan sebagai nol dengan grafik tanpa check-in.

Grafik memakai QPainter bawaan Qt melalui PyQt6. Tidak ada library, model, migrasi atau dependensi baru. Laporan/ekspor adalah Tahap 12.

## Demo cepat

```bash
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/demo_dashboard.py
```

Demo masuk otomatis dan membuka Dashboard. Lima anggota, penugasan, izin dan data awal disiapkan pada schema sementara milik demo di stargate_test. Data kerja tidak diubah dan kamera nyata tidak dibuka. Tutup normal untuk membersihkan schema; penutupan paksa dapat meninggalkan schema sementara, tanpa penghapusan massal schema lain.

1. Awal pukul 08:11 WIB simulasi: **Anggota aktif 5, Hadir 2, Terlambat 1, Absent 1, Izin 1, Belum masuk 1**. Terlambat termasuk dua orang Hadir.
2. Klik **Simulasikan check-in terminal lain**. Layanan/penulis lain menyimpan IN melalui aturan absensi asli. Tanpa refresh manual, Hadir menjadi **3**, Terlambat **2**, Belum masuk **0**, dan feed bertambah satu event. Klik ulang tidak membuat IN kedua.
3. Untuk melihat perubahan Absent tanpa check-in, tutup/buka demo baru lalu langsung klik **Majukan ke akhir shift**. Waktu absensi menjadi 17:00 WIB; setelah polling, Absent menjadi **2** dan Belum masuk **0**. Jam sistem tidak diubah. Jika IN sudah dilakukan terlebih dahulu, Absent tetap 1.
4. Pilih tanggal kemarin: filter tidak kembali sendiri. Tekan **Hari ini** untuk kembali ke tanggal demo. Coba fokus pada tanggal dan periksa bahwa pembaruan tidak menghilangkan fokus.
5. Gulir untuk melihat grafik harian/bulanan. Ubah ukuran jendela dan periksa nama/angka tetap terbaca; nilai penuh juga tersedia lewat tooltip.
6. Tutup dan buka demo kembali untuk mengulang data awal. Pada demo, waktu absensi terkontrol berbeda dari jam nyata pada header aplikasi; lihat status kontrol demo.

## Tes mandiri dengan data kerja/uji nyata

1. Tutup aplikasi lama, buka `main.py`, login dengan peran yang diizinkan dan buka Dashboard.
2. Cocokkan Hadir/Terlambat dengan anggota unik yang mempunyai IN pada tanggal kerja tersebut, bukan jumlah semua baris riwayat. Total kartu aktif dibaca dari daftar anggota aktif.
3. Lakukan absensi pada terminal/proses lain yang memakai database sama; Dashboard terbuka harus memperbarui feed/kartu tanpa refresh. Pada satu jendela, lakukan absensi dari Kehadiran kemudian kembali ke Dashboard. Kamera halaman Kehadiran tetap berhenti saat pindah menu sesuai desain yang sudah direview.
4. Periksa break/OUT menambah feed tetapi tidak jumlah Hadir, serta checkout otomatis bertanda sumber Otomatis.
5. Untuk shift malam, pilih tanggal mulai shift dan periksa IN serta OUT lewat tengah malam tetap dihitung satu orang. Statistik hari berikutnya tidak menerima IN kemarin sebagai IN baru.
6. Biarkan melampaui akhir shift dan pergantian hari yang relevan; Absent dan tanggal otomatis diperbarui. Jangan mengubah jam sistem. Batas waktu dan kondisi izin/libur juga diuji memakai jam/fixture terkontrol.
7. Periksa input filter, pindah menu, logout dan tutup aplikasi. Jangan mematikan database development untuk memaksakan error; kegagalan ditangani oleh tes sintetis.

Laporan review cukup memuat tanggal kerja, zona, angka yang diharapkan/terlihat, langkah, waktu, serta pesan masalah. Tidak perlu mengirim wajah, embedding, password atau kredensial kamera.

## Bukti dan batas

Regresi penuh: **371 PASS**, nol failure/error/skip, durasi **370,89 detik**. Coverage app+database+ai **89,59% (5974/6668 statements)**, memenuhi batas 80%. Native macOS: **59 PASS**, durasi **154,83 detik**, termasuk Dashboard, demo dua tahap, kamera/inference sintetis, fokus, registrasi, pengaturan, administrasi, sesi dan lifecycle worker. Satu FutureWarning upstream InsightFace/scikit-image tetap terlihat.

Pemeriksaan database development baca saja PASS: 0004_devices/current/head, schema valid, 14 tabel aplikasi. Tidak ada migrasi/dependensi baru atau penulisan data operasional oleh pengujian. Demo, placeholder dan semua hasil statistika uji memakai data sintetis; suite model memakai fixture publik yang sudah tersedia. Tidak ada pengambilan/pendaftaran wajah nyata baru.

Bukti: [regresi penuh](evidence/stage-11-tests.xml), [native macOS](evidence/stage-11-native.xml), [ringkasan](evidence/stage-11-summary.json), [Dashboard sintetis](evidence/stage-11-dashboard.png), [demo lima anggota](evidence/stage-11-demo.png), [render keempat grafik sintetis](evidence/stage-11-charts-synthetic.png). Coverage lengkap tersimpan lokal pada .local/stage-11-coverage.json. Render grafik ditinjau terpisah dengan data sintetis ilustratif (bukan angka dari demo lima anggota); label, Unicode, nama panjang dan skala diperiksa secara visual. Gambar native Dashboard/demo juga telah ditinjau. Tidak ada sesi tes yang masih berjalan.

Bukti otomatis tidak menjadi klaim benchmark produksi, hasil kamera/serangan fisik, RTSP atau Windows. Persetujuan review Tahap 10 tidak diubah menjadi angka percobaan fisik yang belum dilaporkan. Review Tahap 11 tetap menunggu pengguna.

Referensi melalui MCP Context7: [SQLAlchemy agregasi/distinct](https://docs.sqlalchemy.org/en/20/core/sqlelement.html), [SELECT/GROUP BY](https://docs.sqlalchemy.org/en/20/tutorial/data_select.html), [Qt QWidget paintEvent](https://doc.qt.io/qt-6/qwidget.html#paintEvent), [QPainter](https://doc.qt.io/qt-6/qpainter.html), [QTimer](https://doc.qt.io/qt-6/qtimer.html). Bindings tetap PyQt6.

Review pengguna Tahap 11 diterima pada 20 Oktober 2026 dan lanjut Tahap 12 diizinkan. Hasil laporan/ekspor dicatat terpisah pada [Tahap 12](stage-12.md).
