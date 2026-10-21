# Tahap 13 — Audit, cadangan dan pemulihan

Tanggal: 20 Oktober 2026. Review Tahap 12 diterima pengguna; Tahap 13 diizinkan. Tahap 14 belum dimulai. Verifikasi teknis PASS; review pengguna diterima 20 Oktober 2026 dan lanjut Tahap14 diizinkan. Status rinci di bagian Bukti.

## Kebijakan yang disetujui

Pengguna menyetujui **retensi operasional 7 hari**, enkripsi dengan kata sandi tersendiri, dan **registrasi wajah ulang sesudah restore**. Foto profil dan embedding ada dalam cadangan terenkripsi untuk cakupan data/validasi, tetapi **tidak diaktifkan atau ditulis ulang saat restore**. Semua `members.photo_path` dipindah ke placeholder; tabel embedding dan sesi kosong. Riwayat attendance, akun beserta hash password, anggota, grup, perangkat, penugasan, izin, kalender, lokasi, settings dan audit dipulihkan. Akun nonaktif tetap mengikuti snapshot cadangan; tinjau kembali hak akses/keaktifan sebelum membuka operasional.

Angka 7 hari adalah keputusan operasional yang telah disetujui pengguna, bukan batas hukum yang diklaim dari dokumentasi library. Risiko biometrik yang sudah dihapus muncul kembali diatasi dengan melewati seluruh biometrik saat restore. Aturan ini juga berlaku pada cadangan pengaman. Untuk membatalkan restore yang sudah sukses, pemulihan cadangan pengaman mengembalikan data bisnisnya, tetapi wajah tetap wajib didaftarkan ulang.

Cadangan yang sudah berusia 7 hari ditolak. Hapus salinan pada folder ekspor, media lepas, cloud, email atau perangkat lain sebelum/ketika masa retensi berakhir; aplikasi tidak dapat menghapus lokasi eksternal yang tidak dikelolanya. Cadangan pengaman pada `.local/backups` dibersihkan setelah 7 hari saat layanan dimulai atau sebelum restore berikutnya. Jika aplikasi berhenti, pembersihan terjadi saat dibuka kembali; pemilik tetap bertanggung jawab atas salinan eksternal. Tidak ada klaim penghapusan forensik terhadap WAL, snapshot disk atau backup OS.

## Audit dan akses

- Super Admin dan Admin: menu **Audit aktivitas**, tanggal inklusif, kode aktivitas persis, username persis dan 100 baris per halaman. Rentang maksimal 366 hari. Klik Tampilkan audit setelah mengubah filter; tidak ada refresh otomatis yang menghilangkan fokus.
- Super Admin: **Cadangan dan pemulihan**. Admin, Operator dan Viewer ditolak pada layanan maupun menu. Viewer tetap hanya Laporan.
- Login/gagal/lockout/logout/sesi, perubahan pengguna, anggota/nonaktif/penghapusan biometrik, jadwal/grup/shift/perangkat/settings, attendance dan ekspor laporan memiliki audit. Backup sukses, restore sukses, restore gagal dan pembatalan juga dicatat. Detail hanya whitelist field/count/nilai settings, tanpa foto, vector, token, password, lokasi file atau isi error.
- Runtime database tetap hanya SELECT/INSERT pada audit; tidak diberi DELETE/UPDATE/DDL untuk restore. Audit dari snapshot dipulihkan, kemudian event `backup.restored` ditambahkan. Aktivitas sesudah tanggal snapshot tersimpan dalam cadangan pengaman, bukan digabungkan diam-diam dengan ID audit lama.

## Format dan cakupan

`.sgbackup` adalah format data logis StarGate versi 1, **bukan dump SQL PostgreSQL**. Bundel JSON bertipe memuat 14 tabel (sesi sengaja kosong), profil PNG yang dirujuk pada direktori kelolaan, hash aset, versi schema dan signature struktur, waktu pembuatan/kedaluwarsa, kebijakan reenroll dan checksum manifest model bila tersedia. JSON dipulihkan hanya melalui metadata tabel aplikasi dan parameter SQLAlchemy; tidak ada SQL, pickle, ekstraksi ZIP atau perintah yang dijalankan dari file cadangan. Pemulihan data mensyaratkan schema hasil migrasi yang sesuai; ini tidak mencadangkan cluster, role PostgreSQL, extension atau sistem operasi.

Enkripsi memakai **AES-256-GCM**, salt acak 16 byte, nonce acak 12 byte, key Scrypt (N=2^17, r=8, p=1) dan header terautentikasi. Password 12–256 byte UTF-8 tidak disimpan. Kedua password saat membuat cadangan harus sama. Kata sandi backup tidak dapat di-reset: simpan melalui password manager terpisah dan uji restore pada lingkungan test. Enkripsi ini melindungi kerahasiaan/integritas file; tidak membuktikan siapa pembuatnya jika orang lain juga memiliki kata sandi. Hanya pilih cadangan dari sumber yang dipercaya.

Batas format lokal saat ini: **128 MiB** terenkripsi, **200.000 record** total, satu foto maksimal 10 MiB dan batas gabungan foto. Data melampaui batas menghasilkan penolakan, bukan cadangan terpotong. Perlu desain cadangan streaming untuk volume lebih besar; benchmark skala besar tetap Tahap 15.

Tidak dicadangkan: `.env`, kredensial database/migrasi, token Keychain/Credential Manager, sumber RTSP lengkap, log, file ekspor, foto asli luar direktori aplikasi, blob model dan berkas aplikasi. Settings nonrahasia berasal dari tabel settings; lokasi/zona dan konfigurasi perangkat berasal dari tabel terkait. Referensi rahasia perangkat dikosongkan, sehingga RTSP harus diprovisikan ulang; model diunduh ulang dari manifest versi yang sesuai. Import foto eksternal tidak membuat file asli ikut tersapu saat cleanup.

File cadangan ditulis ke file sementara privat 0600, di-flush/fsync lalu dipublikasikan atomik tanpa menimpa file yang ada. Direktori pengaman 0700. Filesystem tujuan harus mendukung hard link; penolakan simpan tidak merusak file lama. ACL/instalasi Windows perlu diverifikasi pada Tahap 14.

## Prosedur pemulihan

1. **Gunakan demo/database test dahulu.** Pada aplikasi utama, restore mengganti data operasional. Jangan menjalankan simulasi kerusakan pada database kerja.
2. Masukkan kata sandi dan klik **Pilih dan periksa cadangan**. Periksa tanggal, batas berlaku, jumlah record/anggota, dan pemberitahuan registrasi ulang. Pastikan Anda mengetahui akun/password Super Admin yang ada dalam cadangan tersebut.
3. Ketik persis **PULIHKAN**. Tombol tetap nonaktif jika belum diperiksa atau kata sandi berubah. File diverifikasi lagi melalui digest dan schema saat dijalankan.
4. Aplikasi menghentikan kamera/scan/enrollment dan menunggu pekerjaan aktif selesai; navigasi/ganti password/logout sementara ditahan. Penulis resmi lintas terminal memakai advisory lock yang sama; restore juga mengambil lock tabel eksklusif. Penulisan yang tertahan gagal aman atau ditolak sebagai sesi lama setelah restore; restart terminal lain setelah selesai.
5. Helper owner memvalidasi target lokal yang dikonfigurasi. Kredensial owner tetap dibaca oleh modul administrasi terpisah; tidak masuk AppConfig atau argumen command line, tidak diberikan ke akun runtime. Desktop memerlukan konfigurasi owner lokal yang telah dipakai migrasi. Model provisioning/penyimpanan owner untuk paket distribusi diputuskan dan diuji Tahap 14.
6. Cadangan pengaman terenkripsi dibuat dan dibaca ulang di `.local/backups/<id>.sgbackup`, memakai **kata sandi cadangan yang sedang dipulihkan**. Tanpa cadangan pengaman valid, data tidak dihapus. Jika aset saat ini tidak lengkap, perbaiki aset terlebih dahulu; jangan menghapus data untuk melewati pengamanan.
7. Semua penggantian tabel dan restart identity dilakukan dalam satu transaksi. Error, cancel atau proses mati sebelum commit menyebabkan rollback PostgreSQL; pengaman tetap tersedia. Saat commit sudah berhasil, pembatalan tidak dilaporkan sebagai batal. Jika koneksi hilang ketika konfirmasi commit sedang diterima, status dapat ambigu: login kembali dan periksa data sebelum mencoba ulang; jangan menganggap rollback pasti terjadi.
8. Setelah sukses, semua sesi/remember token dalam database telah berakhir. Masuk memakai akun/password dalam cadangan. Foto kelolaan lama dibersihkan sebagai orphan; jika cleanup gagal, pesan meminta tindak lanjut. Riwayat tetap ada, pengenalan wajah belum berfungsi sampai registrasi ulang. Atur ulang sumber RTSP dan tinjau hak/keaktifan akun serta anggota.

Pemulihan memerlukan database yang hidup dengan schema yang cocok dan akun Super Admin yang dapat login. Untuk kerusakan total, siapkan database kosong, jalankan migrasi/seed/bootstrap pada lingkungan pemulihan terpisah, lalu login dan pulihkan file yang valid. Provisioning, distribusi dan prosedur bencana sistem operasi lengkap tetap Tahap 14/16; membuat file saja tidak membuktikan pemulihan.

## Demo cepat dan uji mandiri

```bash
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/demo_backups.py
```

Demo membuat schema sementara di database test terpisah, 25 anggota serta riwayat sintetis; kamera tidak dibuka. Akun pengujian dan login awal disiapkan otomatis. Tutup normal menghapus hanya schema milik demo. File yang Anda ekspor ke lokasi pilihan tetap ada; hapus setelah pengujian. Cadangan pengaman berada dalam direktori sementara demo dan ikut dihapus saat demo ditutup.

1. Pada **Cadangan dan pemulihan**, isi kata sandi sendiri minimal 12 byte dan ulangi. Klik Buat cadangan; pilih nama baru. Simpan kata sandi untuk langkah selanjutnya.
2. Klik tombol demo **Ubah satu anggota sesudah backup**. Buka Anggota; anggota pertama bernama `DIUBAH SESUDAH BACKUP`.
3. Buka **Audit aktivitas**. Pilih tanggal hari ini, tampilkan. Coba `member.updated` atau `backup.created`. Fokus mengetik tetap stabil; filter berubah tidak menjalankan pencarian berulang.
4. Kembali ke Cadangan. Isi password file, pilih/periksa file pada langkah 1. Periksa ringkasan dan ketik PULIHKAN; lalu Pulihkan data.
5. Harus kembali ke login. Klik tombol demo **Masuk ulang akun demo**. Buka Anggota: nama kembali ke snapshot sebelum diubah. Foto menjadi placeholder; riwayat tetap tersedia. Audit memuat `backup.restored`.
6. Untuk login manual di demo: username `demo_recovery`, password `Demo-recovery-2026!`. Ini hanya akun sintetis demo dan jangan dipakai di aplikasi utama.
7. Ulangi pilih file dengan password berbeda: harus ditolak. Salin file ke nama uji lain dan ubah/hapus sebagian byte menggunakan editor; pilih salinan rusak itu: harus ditolak tanpa mengubah anggota. Jangan merusak satu-satunya cadangan.
8. Buat cadangan lagi menggunakan nama yang sudah ada: aplikasi menolak menimpa file lama. Pilih nama baru.
9. Coba menu utama dengan Admin/Operator/Viewer: Cadangan tidak tersedia, audit hanya Admin/Super Admin. Pengujian penolakan layanan juga otomatis.

Pembatalan dan crash mungkin terlalu cepat dilakukan manual pada data kecil; tes otomatis menghentikan proses pada titik yang terkontrol. Tidak perlu mencabut koneksi atau mematikan PostgreSQL kerja.

## Bukti

Verifikasi final setelah perbaikan antrean klik demo/startup guard:

| Lapisan | Hasil | Bukti |
|---|---|---|
| Regresi lengkap, database test, model lokal dan keychain uji | **442 PASS**, 0 failure/error/skip; 588,43 detik | [stage-13-tests.xml](evidence/stage-13-tests.xml) |
| Coverage app + database + ai | **90,64%**; 7.080/7.811 statement, 731 miss | [Ringkasan](evidence/stage-13-summary.json); JSON lengkap di .local/stage-13-coverage.json |
| Fokus backup/audit/ekspor (run awal) | **47 PASS**, 127,65 detik | [stage-13-focused.xml](evidence/stage-13-focused.xml) |
| Native macOS Cocoa final | **69 PASS**, 0 failure/error/skip; 260,01 detik | [stage-13-native.xml](evidence/stage-13-native.xml) |
| Native ulang race/fokus | **3 PASS** | [stage-13-native-retry.xml](evidence/stage-13-native-retry.xml) |
| Target/helper lokal baca-saja | Schema 0004_devices, 14 tabel dan koneksi owner PASS; tanpa restore database kerja | [Ringkasan](evidence/stage-13-summary.json) |

Run native awal memiliki 67 PASS/2 FAIL: klik demo Dashboard bertabrakan dengan poll sesi, serta prasyarat aktivasi jendela Cocoa gagal. Antrean klik dan guard startup diperbaiki; uji kini memblokir poll lalu membuktikan satu klik diantrikan. Kasus fokus ulang dan native lengkap final lulus. [Bukti awal tetap disimpan](evidence/stage-13-native-initial.xml); run penuh diulang pada sumber final, sehingga coverage di atas sesuai versi akhir. Satu FutureWarning upstream InsightFace/skimage tetap ada; tidak ada failure/error/skip pada run final.

[Antarmuka konfirmasi native](evidence/stage-13-backup.png) diperiksa visual: kebijakan, field, tombol dan ringkasan terbaca. Dependensi baru cryptography 46.0.7 beserta cffi/pycparser dicatat pada lockfile; pip check PASS. File *.sgbackup diabaikan Git, tetapi tetap harus disimpan privat.

Cakupan: perbandingan seluruh tabel, aset/checksum terenkripsi, kebijakan foto/embedding/sesi, identity, cadangan pengaman, rollback constraint/cancel/crash, lock penulis lain, file rusak/versi/kedaluwarsa, izin, fokus dan lifecycle UI, demo, regresi lengkap/coverage dan native macOS. Tidak ada restore database operasional untuk verifikasi.

## Referensi implementasi

Dokumentasi terbaru diperiksa melalui Context7: [SQLAlchemy transaksi](https://docs.sqlalchemy.org/en/20/core/connections.html#connect-and-begin-once-from-the-engine), [AESGCM dan InvalidTag](https://cryptography.io/en/latest/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM), [Scrypt](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#scrypt). Referensi tersebut mendukung mekanisme library, bukan menetapkan angka retensi. Kebijakan retensi biometrik dan sumber data minimization tetap [biometric-retention.md](../biometric-retention.md).
