# Halaman Kehadiran

Permintaan pengguna: kamera besar seperti dialog registrasi, dropdown perangkat/lokasi di atas, tindakan mulai di kanan, serta daftar hasil yang langsung bertambah. Hilangkan pengantar, checkbox persetujuan berulang, rincian similarity/anti-spoof, dan uraian AUTO. Muat ulang dipertahankan sementara sampai review berikutnya.

Arah mengikuti halaman Anggota/Grup/Shift: warna hijau StarGate dan font sistem, ENERGY 1 / RHYTHM 2 / MOTION 1. Kontrol ringkas di atas memberi ruang utama pada preview. Kamera minimum 480×360 tanpa batas tinggi 300 px sebelumnya; ruang sisa diberikan pada kamera. Bingkai kosong memakai warna yang sama dengan dialog registrasi. Riwayat tetap di bawah dengan tinggi 180–220 px dan gulir tabel sendiri. Pada jendela pendek, halaman tetap bisa digulir.

Dropdown memuat nama perangkat dan lokasi, dengan pilihan Semua kamera bila tersedia beberapa perangkat. Pilihan tunggal membuka satu stream; Semua kamera membuka daftar perangkat yang tersedia melalui validasi batas stream lama. Preview beberapa kamera disusun vertikal agar masing-masing tetap lebar. Nama panjang tidak memaksa lebar halaman. Perangkat/mode terkunci selama proses. Kamera tetap hanya dimulai setelah pengguna menekan Mulai, dan tetap berhenti saat meninggalkan halaman/logout/timeout/tutup.

Penghapusan checkbox mengikuti persetujuan awal yang dinyatakan pengguna. Ini tidak mematikan pemeriksaan keaslian, ambang pengenalan, atau aturan absensi. Nilai konfigurasi tetap digunakan layanan, hanya rincian teknisnya yang dihapus dari layar. Hasil scan, penolakan, dan galat perangkat/model tetap ditampilkan. Riwayat dimuat otomatis setelah transaksi sukses; Muat ulang tidak diperlukan untuk melihat hasil scan baru.

## Bukti pengujian

- `evidence/attendance-layout.xml`: 22 tes UI/demo lulus. Mencakup scan masuk/keluar, satu event pada dua kamera, suara setelah commit, spoof tidak tersimpan, perubahan pengaturan, penghentian/logout/timeout/tutup, serta Muat ulang tanpa berkedip dan permintaan reload digabung.
- `evidence/attendance-layout-sizes.xml`: pemeriksaan lanjutan lulus pada 1000×740, 1180×820 dan 1440×900. Preview minimum terpenuhi, kontrol di dalam halaman, tidak ada gulir horizontal halaman, pilihan kamera dipertahankan, dan bingkai kosong kembali setelah Hentikan. Tab serta fungsi mode memakai kontrol Qt yang sama.
- `evidence/attendance-layout/stage-10-attendance-synthetic.png`: hasil render ditinjau. Warna di kamera adalah frame sintetis, bukan wajah nyata. Gambar diambil sebelum label mode dipendekkan dari Otomatis (masuk / keluar) menjadi Otomatis.

## Delivery Gate

- PASS, Hard Gate: aplikasi dijalankan; kontrol dropdown/Mulai/Hentikan/Muat ulang dan siklus hidup diuji melalui alur database terpisah. Pemeriksaan ukuran dan gambar membuktikan batas kamera/kontrol; tabel lebar memakai gulir internal. Tema/kontras dan fokus Qt mengikuti komponen yang sama. Status kosong, proses, hasil dan galat dipertahankan. Tidak ada aset atau klaim baru.
- PASS, Purpose-Gate: susunan, ukuran, warna bingkai dan alasan mempertahankan Muat ulang dijelaskan di atas. Tidak menambah ikon, badge, efek atau animasi.
- PASS, Liveliness: dial eksplisit; kamera menjadi fokus, kontrol atas dan riwayat bawah membentuk urutan kerja. Aksen hijau dan bingkai mengikuti identitas StarGate.
- PASS, Craftsmanship: tombol tetap terhubung ke layanan berizin; tes memastikan penyimpanan mendahului suara/riwayat dan dua kamera tidak menggandakan event. Kamera dimulai secara eksplisit dan dihentikan sesuai siklus sesi. Perubahan ukuran berlaku untuk aplikasi desktop.
- PASS, Copywriting: label langsung menyebut tindakan/perangkat/lokasi; tanpa klaim, jargon baru, atau penjelasan AUTO berulang. Teks teknis hanya dihapus dari presentasi, aturan pemrosesan tetap digunakan.

Pengujian memakai kamera/wajah sintetis; belum merupakan uji webcam atau akurasi wajah nyata untuk layout baru ini.

## Revisi pesan scan

Atas review pengguna, label status di bawah setiap frame dihapus sepenuhnya. Hasil pemeriksaan wajah dan pesan transaksi biasa (berhasil, scan berulang, check-in kedua ditolak, dan penolakan aturan absensi) tidak lagi ditampilkan di bawah dropdown. Pencatatan, suara sukses dan pembaruan daftar tetap berjalan. Label pesan atas disembunyikan saat kosong agar tidak menyisakan ruang. Pesan gangguan kamera/model/database, suara yang tidak tersedia, atau pengaturan berubah yang memerlukan mulai ulang tetap ditampilkan.

Delivery Gate untuk revisi ini: PASS, penghapusan teks dan ruang sesuai arahan pengguna, tanpa aset/dekorasi/kontrol baru. Tema dan urutan keyboard tetap sama. Tes UI menguji hasil tersimpan tanpa pesan scan, penerimaan respons spoof tanpa penyimpanan, galat database, perubahan pengaturan, siklus sesi dan dua kamera. Bukti: `evidence/attendance-no-scan-messages.xml`. Gambar di atas merupakan tampilan sebelum penghapusan kedua area pesan scan.

## Preview mirror dan notifikasi sukses sementara

Review berikutnya menghapus judul Kehadiran terbaru dan meminta preview mirror. Hanya pixmap yang ditampilkan dibalik horizontal; frame sumber dan array BGR yang dikirim ke AI tetap pada orientasi asli. Orientasi ini mengikuti preview dialog registrasi yang sudah disetujui pengguna.

Notifikasi sukses kini muncul di dalam frame selama 3 detik, dengan panel hijau pucat dan teks 18 px mengikuti panduan pada dialog registrasi. Panel diposisikan kembali saat frame berubah ukuran. Ini memberi konfirmasi yang jelas tanpa menambah teks permanen di luar kamera. Tidak ada animasi/aset baru; arah dan dial sebelumnya tetap berlaku.

Notifikasi hanya dipicu oleh hasil transaksi dengan saved=true dan event_id, bukan oleh setiap hasil deteksi wajah. Event yang sama tidak memulai ulang timer atau menampilkan panel lagi. Event baru yang berhasil dapat mengganti panel, sehingga peserta berikutnya tetap mendapat konfirmasi. Penahan scan saat wajah terus terlihat dan jeda absensi tetap mengikuti layanan sebelumnya; tidak menambah jeda buatan yang menahan peserta lain. Notifikasi serta timer dibersihkan saat kamera dihentikan atau frame tidak tersedia.

Verifikasi: dua tes presentasi menguji warna asimetris untuk preview mirror tanpa membalik input AI, posisi panel saat resize, habisnya timer, event sama tidak muncul kembali, event baru dapat muncul, serta pembersihan panel. Regresi UI memeriksa notifikasi setelah penyimpanan, hilang otomatis saat wajah sintetis terus terlihat walau jam absensi dimajukan 61 detik, tidak muncul saat spoof, dan daftar/suara serta siklus kamera tetap benar. Bukti: `evidence/attendance-notice-presentation.xml`, `evidence/attendance-notice-ui.xml`, dan `evidence/attendance-notice/stage-10-attendance-synthetic.png`.

Delivery Gate: PASS, Hard Gate berdasarkan uji presentasi/scan dan render sintetis yang ditinjau; timer serta teks panel tidak mengambil fokus keyboard. PASS, Purpose-Gate karena posisi, ukuran, warna dan durasi mempunyai tujuan konfirmasi sementara di atas. PASS, Liveliness mengikuti dial dan fokus kamera yang sama. PASS, Craftsmanship karena sukses baru tampil setelah commit, data AI tidak terbalik, dan event berulang tidak memperpanjang notifikasi. PASS, Copywriting karena pesan menyebut nama serta hasil transaksi nyata, tanpa klaim baru. Ini bukan pengukuran akurasi wajah atau pengujian kamera fisik.

## Notifikasi Sudah absen

Pesan Sudah absen kini ditampilkan sekali selama 3 detik untuk scan yang sudah tertahan sebagai tercatat, masih dalam jeda absensi, atau sesi/check-in yang sudah selesai. Layanan memberi kode hasil terpisah dari teks; UI tidak menebak keadaan dari potongan kalimat. Galat jadwal lain tidak diberi label Sudah absen. Aturan transaksi dan jeda absensi tetap sama.

Setiap kamera mengingat anggota terakhir yang sudah diberi notifikasi. Hasil berulang tidak menampilkan ulang panel maupun memperpanjang timer. Notifikasi sukses ikut menandai anggota tersebut, sehingga tidak langsung disusul pesan Sudah absen ketika wajah tetap terlihat. Kamera kedua yang melihat anggota sama juga tidak mengulang pesan. Penanda dilepas setelah paket tanpa wajah yang sah dari worker (minimal satu detik tanpa wajah); jika kamera lain masih menandai anggota tersebut, notifikasi tetap tidak diulang. Anggota berbeda dapat menerima notifikasi sendiri tanpa menunggu jeda buatan.

Verifikasi tambahan: tes integrasi mencatat satu IN, memulai kamera kembali pada mode Masuk, memeriksa pesan Sudah absen dan berakhirnya timer sambil wajah tetap terlihat, lalu memastikan tetap satu event dan satu suara sukses. Tes presentasi menguji pengulangan pada dua kamera, kembalinya pesan setelah semua kamera tidak melihat wajah, pergantian anggota, serta sukses yang tidak disusul pesan berulang. Bukti akhir: `evidence/attendance-already-ui.xml` (15 tes lulus), `evidence/attendance-already-presentation.xml` (3 tes presentasi lulus), dan `evidence/attendance-already-service.xml` (layanan).

Run gabungan awal (`evidence/attendance-already-notice.xml`) mengalami satu timeout 12 detik saat kamera sintetis dimulai kembali, setelah 40 tes lulus dan satu tes model dilewati. Run ulang antarmuka secara terpisah lulus tanpa perubahan waktu tunggu atau aturan aplikasi. Tes model nyata tetap di luar cakupan revisi ini.

Delivery Gate revisi: PASS, Hard Gate dan Craftsmanship berdasarkan pengujian scan/layanan/presentasi, tanpa kontrol, aset atau klaim baru. PASS, Purpose-Gate dan Liveliness mengikuti panel sementara, warna, ukuran dan dial yang sudah diperiksa pada revisi sebelumnya. PASS, Copywriting karena Sudah absen hanya dipicu oleh hasil layanan yang sesuai, bukan setiap wajah yang lolos. Render panel sebelumnya tetap menjadi bukti bentuk/posisi; isi pesan mengikuti kasus baru ini.
