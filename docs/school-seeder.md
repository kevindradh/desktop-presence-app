# Seeder simulasi sekolah SMP

Seeder ini mengisi database aplikasi dengan data sekolah fiktif untuk mencoba halaman Anggota, Grup, Shift, Perangkat, Dashboard, Kehadiran, dan Laporan.
Nama siswa dan guru memakai kata Simulasi, bukan identitas orang nyata. Kode anggota diawali `SIM-SMP-`.
Seeder menulis catatan kehadiran langsung untuk pengujian tampilan dan aturan laporan. Catatan ini bukan hasil pengenalan wajah atau bukti akurasi AI.

## Menjalankan setelah migrasi

Dari folder proyek pada macOS:

```bash
.venv/bin/python scripts/manage_database.py upgrade
.venv/bin/python scripts/manage_database.py seed-school
```

Perintah kedua memakai tanggal hari ini dan riwayat 30 hari, mengikuti zona waktu aplikasi.
Pengaturan bawaan dibuat jika belum ada. Akun dan password yang sudah dibuat tetap dapat digunakan.
Jika belum ada akun, buka aplikasi dan buat Super Admin seperti biasa. Seeder tidak membuat akun atau password demo.

Database harus sudah dimigrasi dan belum berisi anggota, grup, shift, perangkat, penugasan, kalender, izin, atau absensi.
Jika tabel-tabel tersebut sudah terisi, seeder berhenti sebelum menambahkan data.
Untuk mengulang dari awal pada database testing, gunakan perintah `fresh` yang sudah tersedia. Fresh menghapus data aplikasi, termasuk akun; lihat [panduan reset](database-fresh.md).

Untuk memilih tanggal dan panjang riwayat:

```bash
.venv/bin/python scripts/manage_database.py seed-school --date 2026-10-21 --days 30
```

Ganti tanggal contoh sesuai kebutuhan. Tanggal tidak boleh berada di masa depan. Panjang riwayat tersedia dari 14 sampai 90 hari.
Untuk database test terpisah, tambahkan `--database test` pada kedua perintah migrasi dan seeder.
Pada Windows dengan checkout sumber dan virtual environment, ganti `.venv/bin/python` dengan `.venv\Scripts\python.exe`.
Perintah ini tersedia dari sumber proyek; installer Windows sebelumnya belum dibangun ulang.

## Isi data

| Data | Jumlah |
|---|---:|
| Kelas 7A, 7B, 8A, 8B, 9A, 9B | 6 |
| Siswa per kelas | 12 |
| Total siswa | 72 |
| Guru | 6 |
| Staf tata usaha dan petugas piket | 2 |
| Total anggota | 80 |
| Anggota aktif | 74 |
| Grup, termasuk Guru dan Staf | 8 |
| Shift | 4 |
| Perangkat simulasi | 3 |
| Penugasan shift | 74 |
| Catatan izin dan sakit | 12 |

Enam siswa nonaktif masih mempunyai riwayat lama. Jumlah penugasan mencakup penugasan historis yang telah berakhir.
Jumlah catatan absensi bergantung pada tanggal, panjang riwayat, kalender, dan jam menjalankan seeder; ringkasan jumlah dicetak setelah selesai.

## Kode untuk menemukan skenario

Cari kode berikut di halaman Anggota atau filter Laporan. Contoh memakai kelas 7A; pola yang sama tersedia pada lima kelas lainnya.

| Kode | Skenario | Yang dapat diperiksa |
|---|---|---|
| `SIM-SMP-7A-01` | Tepat waktu | Masuk pukul 07.00, keluar pukul 14.00. |
| `SIM-SMP-7A-02` | Terlambat | Masuk pukul 07.25; masuk hitungan Hadir dan Terlambat. |
| `SIM-SMP-7A-03` | Batas toleransi | Masuk tepat pukul 07.10, masih berstatus Hadir tepat waktu. |
| `SIM-SMP-7A-04` | Pulang awal | Keluar pukul 12.30 dan ditandai pulang awal. |
| `SIM-SMP-7A-05` | Istirahat lengkap | Keluar istirahat pukul 10.00, masuk kembali pukul 10.15. |
| `SIM-SMP-7A-06` | Checkout otomatis | Catatan keluar pukul 14.00 ditandai Otomatis. |
| `SIM-SMP-7A-07` | Izin | Memiliki catatan izin, tanpa check-in. |
| `SIM-SMP-7A-08` | Sakit | Memiliki catatan bertipe SICK; masuk hitungan Izin. |
| `SIM-SMP-7A-09` | Belum check-in | Belum masuk sebelum pukul 14.00, Tidak hadir/Absent setelahnya. |
| `SIM-SMP-7A-10` | Nonaktif | Tidak termasuk Anggota aktif; masih mempunyai absensi lama. |
| `SIM-SMP-7A-11` | Tanpa jadwal | Aktif, tetapi tidak otomatis dihitung Absent karena tidak memiliki penugasan. |
| `SIM-SMP-7A-12` | Penugasan berakhir | Aktif; jadwal berakhir tujuh hari sebelum tanggal acuan, riwayat lama tetap ada. |
| `SIM-SMP-GURU-02` | Guru terlambat | Shift guru mulai 06.45, toleransi 5 menit, masuk 07.05. |
| `SIM-SMP-TU` | Tata usaha | Shift 07.30 sampai 15.30, termasuk catatan istirahat. |
| `SIM-SMP-PIKET` | Lintas hari | Masuk 20.00, keluar 06.00 esok hari; tanggal kerja mengikuti tanggal masuk. |

Seluruh skenario diulang pada hari kerja di rentang riwayat, bukan diputar secara acak. Ini memudahkan perbandingan hasil.
Catatan hari ini hanya dibuat sampai jam seeder dijalankan. Seeder tidak menulis absensi dengan waktu di masa depan dan tidak melanjutkan simulasi otomatis setelah selesai.
Misalnya, jika seeder dijalankan pukul 09.00, catatan pulang dan istirahat hari ini belum ada. Pilih hari kerja sebelumnya untuk melihat rangkaian lengkap.

## Kalender dan waktu

Sabtu dan Minggu ditandai libur selama rentang simulasi. Ada satu hari kerja tambahan yang diberi label Libur kegiatan simulasi, sekitar sepuluh hari sebelum tanggal acuan.
Ini libur buatan untuk pengujian, bukan kalender resmi pendidikan atau hari libur nasional.
Tanggal acuan tetap dijadikan hari uji, termasuk bila jatuh pada akhir pekan. Kalender lokasi LOCAL berlaku untuk semua grup, termasuk petugas piket.
Nilai `holiday` pada ringkasan hasil menunjukkan tanggal libur buatan; `ended_assignment` menunjukkan akhir penugasan historis.

Untuk memeriksa Dashboard:

1. Pilih tanggal acuan dan lihat hubungan Hadir dengan Terlambat.
2. Pilih hari kerja sebelumnya untuk melihat catatan masuk, istirahat, pulang, dan pulang otomatis yang lengkap.
3. Pilih tanggal `holiday`. Anggota tanpa scan tidak dihitung Absent atau Belum masuk pada hari libur.
4. Buka Laporan, filter kelas 7A dan satu tanggal kerja, lalu cocokkan dengan tabel kode skenario.
5. Ekspor hasil filter ke Excel atau PDF, lalu cocokkan jumlah baris dan statusnya.
6. Periksa petugas piket pada hari kerja yang sudah selesai untuk melihat jam keluar pada tanggal berikutnya.

Pada pengujian terkontrol tanggal 21 Oktober 2026 pukul 18.00 WIB, hasil tanggal acuan adalah:

| Hitungan Dashboard | Nilai |
|---|---:|
| Anggota aktif | 74 |
| Hadir | 43 |
| Terlambat, termasuk dalam Hadir | 7 |
| Tidak hadir | 6 |
| Izin, termasuk sakit | 12 |
| Belum masuk, petugas piket malam | 1 |

Enam siswa tanpa jadwal dan enam siswa dengan penugasan yang sudah berakhir tetap aktif, tetapi tidak masuk hitungan status kehadiran tanggal acuan.
Hasil saat seeder dijalankan pada jam lain bisa berbeda. Jam aplikasi tidak diubah dan hasil di atas bukan angka yang dipaksakan ke Dashboard.

## Mengulang dan mengubah data

Menjalankan ulang dengan tanggal, panjang riwayat, versi seeder, dan zona yang sama menghasilkan `already_seeded: true`, tanpa menambah duplikat atau menimpa perubahan penguji.
Seeder menyimpan penanda pada audit `simulation.school_seeded`; ringkasan saat pengulangan menjelaskan hasil pemasangan awal, bukan hitungan terbaru setelah data diedit.
Jika tanggal default sudah berganti hari, gunakan `--date` dengan tanggal semula untuk menjalankan ulang tanpa perubahan.
Parameter lain ditolak bila simulasi sudah ada. Untuk dataset baru, lakukan fresh secara terpisah lalu jalankan seeder kembali. Jangan menghapus penanda audit untuk memaksa pengisian ulang.
Seluruh pengisian memakai satu transaksi: jika gagal, penambahan dibatalkan bersama-sama. Dua pemanggilan bersamaan tidak menggandakan data.

## Wajah dan kamera

Seeder tidak menyimpan foto atau embedding, dan tidak membuka kamera. Anggota memiliki penanda path foto sintetis tanpa berkas foto; lakukan registrasi wajah sendiri bila diperlukan untuk uji pengenalan nyata.
Ketiga perangkat hanya merupakan nama dan jenis perangkat simulasi. Indeks kameranya belum dipilih, dan tidak ada alamat RTSP atau kredensial yang ditambahkan.
Atur perangkat nyata melalui halaman Perangkat sebelum menjalankan kamera. Catatan absensi yang dibuat seeder tidak membuktikan koneksi perangkat tersebut.

## Verifikasi pengembangan

Pengujian menggunakan schema sementara milik test di database test, bukan mengisi database kerja.
Pemeriksaan mencakup jumlah data, toleransi keterlambatan, waktu absensi, piket lintas hari, Dashboard, Laporan, pengulangan, pemanggilan bersamaan, rollback, penolakan database berisi data, dan pemeliharaan akun login.
Gabungan pengujian seeder dan regresi perintah fresh: 27 lulus, tanpa kegagalan atau error. Hasil tersimpan pada `docs/testing/evidence/school-seed.xml`.
