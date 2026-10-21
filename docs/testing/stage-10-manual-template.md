# Template hasil tes mandiri Tahap 10

Salin dokumen ini untuk setiap putaran tes. Isi hasil dengan **LULUS / GAGAL / BELUM DIUJI**, serta waktu dan pesan yang terlihat. Semua hasil di bawah belum diuji; bukti otomatis bukan hasil tes mandiri Anda.

## Identitas pengujian

| Isian | Nilai |
|---|---|
| Tanggal dan waktu mulai | … |
| Sistem operasi | macOS / … |
| Aplikasi sudah ditutup penuh dan dibuka kembali | Ya / Tidak |
| Akun dan peran (tanpa password) | … |
| Kode anggota uji (tanpa foto/embedding) | … |
| Kamera dan nomor yang dipilih | … |
| Zona waktu lokasi / aplikasi | … / … |
| Shift, jam mulai–selesai, toleransi terlambat | … |
| Tanggal mulai–akhir penugasan | … |
| Riwayat awal anggota untuk shift/tanggal ini | … |

## Persiapan sekali

- [ ] PostgreSQL dan aplikasi berjalan; masuk sebagai Admin/Super Admin.
- [ ] Gunakan satu anggota uji aktif, sudah terdaftar lima sudut, dengan persetujuan pemrosesan wajah.
- [ ] Satu penugasan berlaku hari ini, tidak bertumpang tindih; shift sedang berlangsung dan masih menyisakan sekitar 15 menit.
- [ ] Anggota belum mempunyai IN/OUT untuk shift dan tanggal kerja ini, serta tidak mempunyai sesi lama yang belum ditutup.
- [ ] Pengaturan awal: similarity **0,60**, anti-spoof **aktif**, ambang **0,85**, timeout **3 detik**, jeda **60 detik**, awal check-in **Shift**, checkout otomatis **nonaktif**.
- [ ] Catat pengaturan semula bila berbeda: …
- [ ] Pilih kamera yang benar melalui dropdown nama perangkat/lokasi di Kehadiran, lalu klik **Mulai**.

Satu wajah cukup didaftarkan pada satu anggota. Jangan menggandakan wajah yang sama ke beberapa anggota untuk mempercepat tes. Nomor kamera mengikuti perangkat yang terdeteksi; pastikan pratinjau benar.

## Jalur cepat: satu anggota, satu sesi, sekitar 10–15 menit

Kerjakan berurutan. Hentikan kamera sebelum mengganti mode. Untuk setiap event baru, tunggu **61 detik dari event terakhir** dan tinggalkan area kamera minimal satu detik sebelum masuk lagi. Bila percobaan ditolak karena terlalu cepat, tunggu di luar area kamera lalu kembali; jangan terus berdiri sampai jeda habis.

| ID | Tindakan | Hasil yang diharapkan | Hasil aktual, waktu/pesan |
|---|---|---|---|
| C01 | Mode **Masuk**, mulai absensi, tampilkan wajah | Satu IN, pesan sukses dan suara; nama/kode anggota benar | BELUM DIUJI — … |
| C02 | Tetap terlihat kamera selama >60 detik | Tetap satu IN; tidak muncul OUT atau suara sukses tambahan | BELUM DIUJI — … |
| C03 | Selama scan, amati **Muat ulang**, lalu klik sekali | Tombol tidak berkedip karena scan; klik memuat ulang sekali, lalu tombol aktif kembali | BELUM DIUJI — … |
| C04 | Hentikan, mulai lagi dengan mode **Masuk**, scan setelah jeda cukup | IN kedua ditolak; jumlah riwayat tetap satu | BELUM DIUJI — … |
| C05 | Hentikan, pilih **Mulai istirahat**, mulai dan scan | Satu BREAK_OUT; total dua event | BELUM DIUJI — … |
| C06 | Hentikan, pilih **Otomatis**, mulai dan scan sebelum 60 detik dari BREAK_OUT | Ditolak karena jeda; total tetap dua event | BELUM DIUJI — … |
| C07 | Tinggalkan kamera, tunggu 61 detik dari BREAK_OUT, masuk kembali dalam mode **Otomatis** | Satu BREAK_IN; total tiga event | BELUM DIUJI — … |
| C08 | Hentikan, pilih **Keluar**, mulai dan scan setelah jeda cukup | Satu OUT; total empat event; Pulang awal = Ya bila sebelum akhir shift | BELUM DIUJI — … |
| C09 | Hentikan, pilih **Otomatis**, scan lagi setelah jeda cukup | Sesi sudah selesai; tidak ada event kelima | BELUM DIUJI — … |
| C10 | Hentikan; buka Anggota → riwayat, lalu tutup/buka aplikasi dan periksa kembali | Urutan IN → BREAK_OUT → BREAK_IN → OUT tetap tersimpan, sumber Scan | BELUM DIUJI — … |

Waktu event: IN … ; BREAK_OUT … ; BREAK_IN … ; OUT … .

Jika sebuah event yang diharapkan belum tersimpan, jangan menghitung jumlah berikutnya sebagai lulus. Catat temuan dan selesaikan masalah terlebih dahulu. Sesudah OUT, sesi yang sama tidak dapat diulang untuk membuat IN lagi.

## Pelengkap sebelum review tahap

Untuk skenario yang membutuhkan IN baru, gunakan anggota lain dengan peserta berbeda yang setuju, atau anggota yang sama pada tanggal penugasan berikutnya. Jangan menumpuk penugasan atau menghapus riwayat untuk mengulang tes. Jalur cepat di atas tidak menggantikan seluruh pengujian ini.

| ID | Skenario dan persiapan | Hasil yang diharapkan | Hasil aktual |
|---|---|---|---|
| P01 | Peserta yang belum terdaftar, dengan persetujuannya | Tidak dikenali; tidak ada event/suara sukses | BELUM DIUJI — … |
| P02 | Foto cetak anggota terdaftar, anti-spoof aktif | Ditolak, tidak ada sukses; catat jumlah percobaan dan yang lolos | BELUM DIUJI — … dari … percobaan |
| P03 | Replay wajah terdaftar dari layar/video, anti-spoof aktif | Ditolak, tidak ada sukses; catat jumlah percobaan dan yang lolos | BELUM DIUJI — … dari … percobaan |
| P04 | USB dan laptop dipilih bersama; sesi baru, mode Masuk, wajah sama terlihat kedua kamera | Hanya satu IN, termasuk saat terus terlihat >60 detik | BELUM DIUJI — … |
| P05 | Saat USB berjalan, cabut USB | Scan berhenti dengan pesan; tidak berpindah otomatis ke kamera laptop | BELUM DIUJI — … |
| P06 | Saat scan berjalan, coba Hentikan, pindah menu, logout dan tutup aplikasi (uji terpisah) | Kamera/model berhenti; tidak ada scan baru setelah penghentian | BELUM DIUJI — … |
| P07 | Sesi baru dengan shift mulai beberapa menit ke depan; coba sebelum mulai, lalu setelah jam mulai | Sebelum mulai ditolak; setelah mulai dapat IN; waktu tepat batas diuji otomatis | BELUM DIUJI — … |
| P08 | Sesi baru; scan pertama setelah batas toleransi terlambat | IN berstatus Late; status tetap pada event berikutnya | BELUM DIUJI — … |
| P09 | Sesi baru: shift singkat, IN dahulu; hentikan kamera, aktifkan checkout otomatis, biarkan login sampai akhir | Setelah sekitar 10 detik bila aplikasi senggang, Muat ulang menampilkan satu OUT Otomatis dengan waktu akhir shift | BELUM DIUJI — … |
| P10 | Sesudah P09, Muat ulang dan login ulang | Tidak menambah OUT kedua | BELUM DIUJI — … |
| P11 | Pada sesi lain yang sudah OUT manual, aktifkan checkout otomatis dan lewati akhir shift | OUT manual tetap sumber Scan; tidak diganti/ditambah | BELUM DIUJI — … |
| P12 | Admin lain mengubah pengaturan saat scan berjalan | Scan lama ditolak, diminta mulai ulang; konfigurasi terbaru digunakan setelah mulai ulang | BELUM DIUJI — … / belum ada Admin kedua |

Untuk P02/P03, bila sesi sudah OUT, penolakan karena sesi selesai **tidak membuktikan anti-spoof bekerja**. Gunakan sesi yang masih memungkinkan event berikutnya, setelah jeda, dan catat pesan penolakan keaslian. Setiap serangan yang lolos tetap merupakan temuan walaupun tes lain lulus.

Checkout otomatis memerlukan aplikasi terbuka dan akun berhak Kehadiran sudah login; kamera boleh dihentikan. Setelah tes, hentikan kamera dan pulihkan pengaturan semula. Jangan mengubah jam sistem atau mematikan database development untuk memaksakan kegagalan.

## Format laporan masalah

- ID tes: …
- Waktu kejadian dan zona waktu: …
- Mode, kamera, pengaturan yang berbeda dari awal: …
- Langkah sebelum masalah: …
- Pesan yang terlihat: …
- Riwayat sebelum → sesudah (jenis event dan waktu): …
- Hasil yang diharapkan dibanding hasil aktual: …
- Dapat diulang: Ya / Tidak / Belum dicoba.

Tidak perlu mengirim password, kredensial RTSP, foto wajah atau embedding. Jika memakai tangkapan layar, tutupi data pribadi yang tidak diperlukan.

## Ringkasan review

- LULUS: …
- GAGAL: …
- BELUM DIUJI beserta alasannya: …
- Temuan yang masih terbuka: …
- Pengaturan telah dipulihkan dan kamera dihentikan: Ya / Tidak.
- Keputusan pengguna: Perlu perbaikan / Review disetujui / Belum diputuskan.

Rincian perilaku dan bukti otomatis tersedia pada [panduan Tahap 10](stage-10.md). Template ini tidak membuat data atau menandai hasil secara otomatis. Tahap 11 menunggu review pengguna.
