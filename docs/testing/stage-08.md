# Tahap 8 — registrasi lima sudut dan registrasi ulang

Tanggal: 19 Oktober 2026. Status: review pengguna disetujui dan Tahap 9 diizinkan. Rincian skor/jumlah percobaan nyata per kondisi tidak dilaporkan.

Pengguna menyetujui review Tahap 7 dan mengizinkan lanjut. Pengguna juga mengizinkan penyimpanan data nyata, memilih penggantian/penghapusan embedding lama setelah set baru lengkap, serta mendelegasikan rekomendasi retensi berbasis beberapa sumber resmi. Kebijakan dan batas sumber: [retensi biometrik](../biometric-retention.md). Izin uji sementara Tahap 7 tidak digunakan diam-diam sebagai izin menyimpan permanen.

## Implementasi

- Halaman Anggota terhubung ke dialog capture dari aplikasi kerja setelah login; Super Admin/Admin/Operator dapat mendaftar/registrasi ulang, Viewer ditolak di layanan.
- Form wajib ID, nama dan grup; email/telepon/jabatan tetap opsional. Validasi form/ID duplikat diperiksa sebelum capture dan kembali saat menyimpan untuk menangani perubahan/race.
- Foto profil wajib berasal dari crop depan yang berhasil; bukan sekadar memilih foto profil tanpa capture. Penggantian file foto profil pada anggota yang sudah ada tetap didukung.
- Lima pose berurutan FRONT/LEFT/RIGHT/UP/DOWN. Setiap sampel memerlukan satu wajah, kualitas layak, live class 1 dan live score >=0,85. Pengecekan keaslian registrasi tetap aktif meskipun konfigurasi anti-spoof lain dimatikan.
- Landmark lima titik diproyeksikan ke sumbu mata sehingga rasio pose relatif tidak berubah hanya karena translasi/zoom gambar; roll >20° ditolak. Front mengalibrasi rasio hidung/mata/mulut; kiri/kanan memerlukan perubahan horizontal >=0,12, atas/bawah perubahan rasio vertikal >=0,10. Ini heuristik awal, bukan estimasi derajat yaw/pitch atau klaim akurasi pose terkalibrasi; uji nyata dibutuhkan untuk menilai panduan/ambang.
- Pose yang sama tidak bisa memenuhi lima slot. Sampel berikutnya harus memiliki cosine similarity >=0,60 dengan depan, agar pergantian subjek ditolak. Threshold ini guard awal, bukan jaminan tidak pernah tertukar.
- Draft 15 menit hanya di memori proses model. Handoff lengkap memuat lima embedding dan PNG depan, dibatasi ukuran, ditandatangani HMAC dengan key acak per proses aplikasi serta terikat token login/nonce/member/revision. Replay, session berbeda, stale edit, incomplete/tampered packet ditolak. Ini bukan attestation perangkat dan tidak melindungi dari administrator yang menguasai proses/host.
- Foto/anggota/lima embedding/audit disimpan melalui satu transaksi layanan yang memvalidasi izin terkini. File baru disiapkan privat 0600 sebelum commit; jika transaksi gagal, file baru dibuang. Crash dapat meninggalkan file yang belum direferensikan; pembersihan mencoba menghapus orphan saat daftar anggota dimuat, tanpa menganggap filesystem dan DB memiliki transaksi fisik bersama.
- Registrasi ulang menghapus set embedding lama dan memasukkan set lengkap dalam transaksi DB yang sama. Sampai commit berhasil, kegagalan mempertahankan revision/foto/set lama. ID anggota dan histori attendance tetap sama. Foto lama dihapus setelah commit jika tidak dipakai anggota lain.
- Nonaktif anggota menghapus embedding dalam transaksi, mengganti foto dengan placeholder, mempertahankan histori attendance dan audit; penghapusan file dilakukan setelah commit. Gagal menghapus file ditandai pending dan dicoba kembali saat daftar dimuat. Tidak mengklaim secure erase WAL/backup/media; Tahap 13 harus memperhitungkan retensi saat restore.
- Tombol Uji wajah tersimpan membuat probe sementara yang ditandatangani dan terikat sesi/anggota/revision. Layanan membaca gallery aktif versi model yang sama dan membandingkan hasil dengan anggota terpilih; tidak menyimpan probe atau membuat attendance.
- Batal, ganti password, logout, timeout, navigasi yang meninggalkan halaman, serta close menghentikan kamera/model dan membuang draft. Tombol Simpan hanya aktif setelah seluruh set diterima. Save yang sudah disubmit ditunggu selesai; menutup dialog tidak membatalkan commit yang sudah berjalan.

Tidak ada dependensi atau migrasi baru. Database tetap revision 0004_devices. Tidak ada akun/password/default member yang dibuat pada database kerja oleh pengujian otomatis.

## Hasil dan bukti

Regresi final **260 PASS, 0 failure/error/skip**, coverage **90,17% (4539/5034 statement)**. **28 tes GUI/auth/administrasi macOS native PASS**; satu FutureWarning upstream tetap terlihat. Ringkasan angka final: [summary](evidence/stage-08-summary.json). Regresi lengkap: [JUnit](evidence/stage-08-tests.xml); GUI macOS native: [JUnit](evidence/stage-08-native.xml). Cakupan coverage tetap app+database+ai, termasuk proses anak dalam denominator meskipun eksekusinya tidak seluruhnya terukur oleh parent.

| Cakupan | Hasil |
|---|---|
| Lima pose lengkap, duplikat pose, perubahan identitas, TTL, frame invalid/liveness/quality gagal | PASS, input terkendali |
| Save atomik/5 vector/PNG privat, HMAC tamper/replay/session binding, field wajib/duplikat | PASS, database nyata + data sintetis |
| Registrasi ulang gagal menjaga set lama; sukses mengganti tepat lima embedding tanpa mengubah attendance | PASS, database nyata + data sintetis |
| Nonaktif menghapus biometrik tetapi menjaga attendance; kegagalan hapus file dilaporkan dan retry | PASS, database nyata + data sintetis |
| Hak semua role, revoked session, stale revision, cancel draft | PASS, database nyata + data sintetis |
| Pencarian anggota tersimpan dari proses Python baru dan tombol uji setelah restart jendela | PASS, probe sintetis; tidak menyatakan identitas wajah nyata sudah diterima |
| UI capture/register/re-register, save belum lengkap disabled, cancel/logout/password/close/timeout | PASS, Qt offscreen dan macOS; sumber kamera/AI sintetis |
| Worker capture model nyata menerima gambar blank dan menolak capture tanpa wajah, tidak mengekspor partial packet | PASS, [bukti model](evidence/stage-08-model-worker.json) |
| Registrasi lima sudut wajah nyata, kecocokan probe baru setelah aplikasi restart, pose guidance pada webcam target | NOT RUN oleh agent; memerlukan uji mandiri pengguna |
| RTSP positif, akurasi/anti-spoof statistik penuh, Windows | Tetap tertunda; Tahap 6/15/14 terkait |

Bukti visual [capture sintetis](evidence/stage-08-capture-synthetic.png) hanya memakai gambar bidang warna dan hasil model buatan. Tidak ada foto/embedding wajah nyata dimasukkan bukti Git atau database oleh tes otomatis.

## Debug dan keterbatasan

- Setup awal delapan tes service gagal karena fixture merujuk AuthService.db, padahal namanya database. Fixture diperbaiki; bukan kegagalan migrasi atau data aplikasi. Uji ulang layanan lulus.
- Smoke helper sementara awal tidak memakai guard __main__ sehingga proses spawn mencoba menjalankan helper lagi. Guard diperbaiki; entry point aplikasi kerja sudah memiliki guard. Uji worker nyata kemudian lulus.
- Review visual memperbaiki status selesai agar foto depan tetap bisa diperiksa sebelum Simpan, sementara kamera sudah dihentikan. Foto preview hanya di memori sampai save.
- Edit foto untuk anggota nonaktif ditolak di UI dan service; edit metadata biasa tetap diizinkan, sehingga kebijakan penghapusan tidak dapat dibatalkan lewat upload foto.
- FutureWarning scikit-image dari InsightFace alignment tetap seperti Tahap 7; tidak disembunyikan dan dependensi tidak diganti.
- Saat capture gagal, beberapa sampel sebelumnya tetap di memori untuk melanjutkan sudut yang belum selesai; Batal/Stop/close membuang semuanya. Kegagalan SQL setelah set lengkap boleh dicoba ulang dengan packet yang sama selama sesi/TTL/revision masih valid; packet habis setelah commit sukses.
- Kegagalan penghapusan file lama setelah commit tidak mengubah transaksi sukses menjadi pesan gagal palsu. UI menampilkan pekerjaan pembersihan yang tertunda saat daftar dimuat. File yang masih direferensikan anggota lain tidak dihapus.

## Uji mandiri

Tutup aplikasi versi lama dan aplikasi lain yang memakai kamera. Dari folder proyek:

```sh
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/manage_database.py check
.venv/bin/python main.py
```

1. Masuk Super Admin/Admin/Operator, buat/pilih grup yang akan dipakai. Operator memerlukan grup yang sudah disiapkan Admin. Buka Anggota, klik Form registrasi baru.
2. Kosongkan ID/nama/grup: Capture tidak aktif. Isi seluruh field wajib. Simpan perubahan biasa masih tidak aktif untuk anggota baru; registrasi diselesaikan melalui Capture lima sudut.
3. Klik Capture lima sudut. Periksa ID/nama peserta pada dialog, lalu centang persetujuan penyimpanan. Pilih nomor kamera yang benar dan klik Mulai pemeriksaan. Nomor 0/1 bukan identitas hardware tetap.
4. Hadapkan wajah lurus di tengah gambar; tunggu satu wajah lolos kualitas/liveness, lalu klik Ambil sudut ini. Counter menjadi sudut berikutnya. Mencoba pose depan lagi seharusnya ditolak sebagai sudut belum sesuai, bukan menambah counter.
5. Ikuti panduan kiri/kanan sesuai arah yang ditulis di gambar, lalu atas/bawah, tanpa memiringkan seluruh kepala. Gerakkan perlahan; jangan terlalu ekstrem hingga hidung/mata/mulut tidak dapat dipetakan atau liveness menolak. Klik Ambil sudut ini setiap pose layak.
6. Coba wajah tidak terlihat, dua orang, wajah buram/kecil, foto layar atau orang berbeda di tengah capture: slot baru seharusnya tidak diterima. Jangan menganggap no face/blur sebagai bukti anti-spoof terhadap serangan yang layak.
7. Sebelum lima slot lengkap, Simpan tidak aktif dan anggota belum muncul di daftar. Klik Batalkan pada percobaan terpisah: tidak ada anggota atau foto tersimpan.
8. Setelah lima slot lengkap, kamera berhenti dan foto depan bisa diperiksa. Klik Simpan anggota dan lima sampel. Setelah transaksi berhasil, dialog menutup dan anggota muncul. Pilih anggota lalu pastikan metadata/foto tersimpan. Menekan Simpan dua kali tidak membuat dua anggota.
9. Tutup/buka aplikasi: anggota/foto tetap ada. Pilih anggota lalu klik **Uji wajah tersimpan**. Centang persetujuan probe sementara, mulai kamera, hadapkan satu wajah asli, klik **Periksa wajah ini**, kemudian **Bandingkan dengan database**. Diharapkan cocok dengan anggota terpilih setelah probe layak/liveness lolos. Ulangi dengan peserta lain yang setuju: harus tidak cocok. Probe tidak disimpan, jumlah sampel tetap lima dan tidak ada absensi baru. Ini memakai gallery DB, berbeda dari referensi sementara alat Tahap 7. Penerimaan wajah nyata setelah restart tetap perlu Anda konfirmasi.
10. Pilih anggota aktif, klik Registrasi ulang wajah. Batalkan setelah 1–4 sudut: data lama tetap. Selesaikan lima sudut dan simpan: ID/metadata anggota tetap satu, set baru mengganti lama, histori attendance tetap. Jangan menghapus anggota untuk registrasi ulang.
11. Mulai capture lalu coba Batalkan, ganti password/logout (atau timeout sesi), atau tutup aplikasi. Model/kamera harus dilepas tanpa anggota setengah jadi; jika save sudah dikirim, tunggu hasil transaksi.
12. Coba ID duplikat, email tidak valid, dan akun Viewer: validasi/izin harus menolak; jangan menghapus data nyata untuk menguji error.
13. Untuk data uji yang sudah tidak diperlukan, pilih Nonaktifkan anggota dan baca konfirmasi. Foto/embedding aplikasi dihapus, histori tetap. Penggunaan biometrik kembali memerlukan registrasi yang sesuai; saat ini tidak ada tombol aktivasi ulang anggota.

Jangan membagikan foto/embedding peserta melalui chat atau memasukkan berkas biometrik ke Git. Laporkan langkah, kondisi kamera, pesan/skor dan hasil yang muncul. Durasi uji awal/threshold bukan bukti target statistik produksi Tahap 15.

## Review pengguna

Pada 19 Oktober 2026, setelah panduan uji mandiri, pengguna menyatakan review sudah OK dan mengizinkan lanjut Tahap 9. Persetujuan dicatat tanpa menambahkan skor atau hasil per kondisi yang tidak dilaporkan; bukti otomatis tetap berlabel sintetis/model smoke sesuai asalnya.
