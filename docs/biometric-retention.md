# Retensi biometrik StarGate — keputusan produk

Tanggal: 19 Oktober 2026. Pengguna mengizinkan data nyata untuk Tahap 8 dan mendelegasikan rekomendasi retensi dengan syarat memakai beberapa sumber nyata. Pengguna secara khusus memilih penghapusan embedding lama setelah registrasi ulang lengkap berhasil, tanpa menghapus data anggota/riwayat absensi.

## Dasar sumber dan batas penerapan

1. [UU 27 Tahun 2022, naskah resmi BPK](https://peraturan.bpk.go.id/Home/Download/224884/UU%20Nomor%2027%20Tahun%202022.pdf): Pasal 4 menyebut biometrik sebagai data pribadi spesifik. Pasal 43 mencakup penghapusan ketika tidak diperlukan lagi untuk tujuan pemrosesan, persetujuan ditarik, atau ada permintaan subjek sesuai ketentuan yang berlaku. Pasal 16 memuat pembatasan tujuan/pemrosesan. Ini tidak menetapkan satu angka retensi universal untuk seluruh aplikasi absensi wajah.
2. [ICO — keamanan data biometrik, minimisasi dan storage limitation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/biometric-data-guidance-biometric-recognition/how-do-we-keep-biometric-data-secure/): batasi data sesuai kebutuhan, tinjau referensi biometrik dan hapus yang tidak lagi diperlukan; pertimbangkan apakah sampel asli memang perlu dipertahankan. Dipakai sebagai praktik teknis, bukan pernyataan hukum UK otomatis berlaku di Indonesia.
3. [GDPR, Pasal 5(1)(c)/(e), EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng): prinsip minimisasi dan pembatasan penyimpanan selama diperlukan untuk tujuan. Dipakai sebagai pembanding desain, tanpa menganggap GDPR otomatis berlaku pada deployment proyek ini.

Sumber diakses pada 19 Oktober 2026. Prinsip sumber dibedakan dari pemetaan status aplikasi dan parameter teknis di bawah; sumber tidak mewajibkan lima embedding, batas 15 menit, atau definisi status anggota StarGate.

## Kebijakan yang diterapkan berdasarkan mandat pengguna

| Kondisi | Perilaku StarGate | Dasar pemilihan |
|---|---|---|
| Anggota aktif dan masih memerlukan absensi wajah | Simpan satu foto profil depan serta satu embedding untuk masing-masing lima sudut; tidak menyimpan video atau foto mentah kelima sudut | Foto wajib/lima sudut berasal dari PDF; pembatasan salinan mengikuti minimisasi |
| Anggota dinonaktifkan | Hapus embedding pada transaksi nonaktif dan ganti referensi foto dengan placeholder; hapus salinan foto aplikasi setelah commit | Untuk produk ini, nonaktif berarti keperluan identifikasi wajah absensi berakhir; ini keputusan produk berdasarkan purpose limitation, bukan frasa literal undang-undang |
| Registrasi ulang | Set lama tetap berlaku selama capture belum lengkap atau save gagal. Setelah set baru lengkap, ganti seluruh embedding dan foto dalam satu transaksi DB; hapus foto lama setelah commit | Pilihan eksplisit pengguna dan kebutuhan mencegah kehilangan set lama akibat kegagalan |
| Capture dibatalkan, gagal atau kedaluwarsa | Tidak membuat anggota/embedding/foto tersimpan; draft hanya di memori dan dibuang ketika proses dihentikan | Tidak perlu menyimpan sampel gagal untuk tujuan registrasi |
| File foto lama gagal dihapus karena izin/I/O | Referensi DB sudah dihapus/diganti; file dianggap pekerjaan pembersihan tertunda, dicoba kembali saat daftar anggota dimuat. UI menampilkan peringatan bila masih tertunda | Jangan mengklaim file sudah terhapus jika penghapusan fisik gagal |
| Riwayat absensi, audit dan metadata anggota | Tidak ikut dihapus oleh penghapusan biometrik | Kebutuhan histori PDF; retensi records nonbiometrik harus ditentukan terpisah sebelum operasional/distribusi |

Tidak menetapkan masa tunggu 30/90 hari setelah nonaktif karena belum ada kebutuhan atau aturan sektoral yang mendukung angka tersebut. Status aktif bukan izin menyimpan selamanya ketika tujuan sebenarnya sudah berakhir; pemilik data harus menonaktifkan anggota yang tidak lagi membutuhkan absensi wajah. Cuti/ketidakhadiran sementara jangan diperlakukan sebagai keluar dari keanggotaan hanya untuk memicu penghapusan.

Batas sesi capture 15 menit adalah parameter teknis freshness dan pencegahan replay draft, bukan angka retensi yang diwajibkan hukum. Pengambilan ulang diperlukan setelah lewat batas itu.

## Batas implementasi

- Penghapusan berkas menyasar salinan PNG privat yang dikelola aplikasi; tidak menghapus file foto asli di luar direktori aplikasi.
- Pembersihan memeriksa referensi seluruh anggota di dalam transaksi layanan yang diserialkan, agar tidak menghapus foto yang masih dipakai anggota lain atau foto baru yang belum commit.
- Pengecekan checksum model, hak akses dan konsistensi transaksi tidak menggantikan penetapan dasar pemrosesan dan pemberitahuan organisasi kepada peserta. Dialog menjelaskan penyimpanan dan masa berlakunya secara konkret.
- Penghapusan logis database/file aplikasi bukan jaminan forensic secure erase dari media, WAL, snapshot OS atau backup. Prosedur backup/restore dan penghapusan kembali setelah restore wajib dirancang pada Tahap 13; belum ada klaim penghapusan seluruh backup.
- Jalur permintaan penghapusan karena hak subjek di luar nonaktif memerlukan alur operasional tersendiri sebelum penggunaan produksi. Tahap 8 bukan pernyataan kepatuhan hukum menyeluruh atau dasar penyimpanan tanpa batas.

## Keputusan cadangan Tahap 13

Pada 20 Oktober 2026 pengguna menyetujui cadangan terenkripsi dengan retensi operasional 7 hari dan registrasi wajah ulang setelah restore. Foto/embedding yang ada dalam snapshot tidak diaktifkan kembali; seluruh referensi profil menjadi placeholder dan gallery dikosongkan. Cadangan lewat masa berlaku ditolak. Salinan pengaman kelolaan dibersihkan pada pembukaan layanan/restore berikutnya; ekspor eksternal memerlukan penghapusan oleh pemiliknya. Angka ini keputusan operasional pengguna, bukan klaim batas hukum. [Rincian prosedur dan keterbatasan](testing/stage-13.md).
