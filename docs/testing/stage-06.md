# Hasil Tahap 6 — perangkat dan pipeline kamera

Tanggal: 19 Oktober 2026. **Implementasi dan pengujian pada perangkat tersedia selesai; gerbang penuh belum lulus.** Tahap 5 sudah disetujui pengguna. Review pengguna kemudian disetujui dan Tahap 7 diizinkan. RTSP nyata belum tersedia; cabut USB dikonfirmasi aman oleh pengguna setelah restart/CAM-B003.

## Implementasi

- [x] CRUD perangkat: nama unik, jenis internal/USB/RTSP, nomor kamera lokal, lokasi, resolusi dan FPS, revision/stale edit, konfirmasi hapus dan perlindungan riwayat.
- [x] Izin Super Admin/Admin ditegakkan di layanan dan navigasi; Operator/Viewer ditolak.
- [x] Uji koneksi berhenti setelah satu frame; preview eksplisit, dua kamera default, batas 1–4 via konfigurasi.
- [x] Capture OpenCV di proses spawn; satu slot frame terbaru maksimal 960×540 RGB per kamera, tanpa backlog video.
- [x] Timeout, read macet, retry RTSP terbatas, gambar basi dibersihkan, stop/reap proses tanpa memblokir GUI.
- [x] Keluar halaman, logout, ganti password, sesi berakhir dan close menghentikan capture. Jalur UI diuji memakai sumber sintetis.
- [x] URL RTSP penuh disimpan native Keychain/Credential Manager; DB/DTO hanya safe host/port dan reference. Input disamarkan dan tidak dipulihkan ke formulir. Log capture native dibisukan karena dapat memuat URL.
- [x] Migrasi 0004_devices diterapkan dev/test; seluruh kolom/data lama, termasuk akun/hash/sesi, dibandingkan sebelum/sesudah di memori dan tetap sama.
- [ ] Uji RTSP positif pada stream nyata, putus/reconnect sumber RTSP nyata.
- [x] Uji cabut USB dan review pengguna dikonfirmasi setelah perbaikan CAM-B003; pengguna mengizinkan lanjut Tahap 7.

Tidak ada dependensi baru. Lingkungan macOS arm64, Python 3.11.17, PyQt6 6.11.0/Qt 6.11.2, OpenCV 4.11.0 dengan AVFoundation dan FFmpeg, PostgreSQL 17.11/pgvector 0.8.7. Windows belum diuji.

## Hasil dan bukti

| Cakupan | Hasil | Bukti |
|---|---|---|
| Regresi unit/integrasi/UI, DB nyata dan native Keychain | 191 PASS, 0 skip/failure; coverage app+database 92,37% (3391/3671 statement) | [JUnit](evidence/stage-06-tests.xml), [Ringkasan](evidence/stage-06-summary.json) |
| GUI macOS asli: perangkat, autentikasi, administrasi | 27 PASS | [JUnit native](evidence/stage-06-native.xml) |
| Dua webcam lokal: preview sedikitnya 60 frame, buka ulang/test, multi-camera | PASS, keduanya 1280×720; sumber FaceTime HD Camera dan C922 tersambung saat pengujian | [Metadata saja](evidence/stage-06-cameras.json) |
| Kamera lokal index 15 tidak tersedia; RTSP localhost port tertutup | PASS: gagal aman, proses dilepas | Metadata kamera; bukan bukti RTSP positif |
| Read/open macet, batas retry, pemulihan retry, slot terbaru/drop backlog, batas multi-camera | PASS dengan worker sintetis | tests/test_cameras.py |
| CRUD/duplikat/stale/referensi/validasi/otorisasi, rollback secret, masking URL | PASS dengan DB nyata dan vault double; roundtrip vault native diuji terpisah | tests/test_devices.py, test_devices_validation.py, test_keychain_native.py |
| Migrasi/model/downgrade/upgrade dan preservation data lama | PASS | [Deployment dev/test](evidence/stage-06-deployment.json) |
| RTSP nyata, cabut fisik, Windows, soak panjang/performa produksi | NOT RUN | Memerlukan sumber/perangkat/lingkungan dan tahap pengujian terkait |

Coverage proses anak capture tidak tercakup penuh oleh run pytest parent; pengujian hardware langsung dicatat terpisah. Angka coverage bukan bukti kamera/model AI end-to-end. Tidak ada frame wajah nyata disimpan; bukti visual hanya bidang warna sintetis: [form](evidence/stage-06-devices-synthetic.png), [preview](evidence/stage-06-preview-synthetic.png).

## Temuan dan batas

1. Insert RTSP awal mengisi camera_index 0 dari default ORM meskipun diminta NULL, sehingga no-op save terhitung berubah. Kolom memakai evaluates_none; regression no-op/revision lulus.
2. Pergantian jenis RTSP ke webcam dapat membawa input sumber lama. Pergantian jenis sekarang membersihkan input dan mengembalikan penyamaran; tes klik tombol lulus.
3. Tes close awal memeriksa visibility sebelum callback close terjadwal selesai. Tes diperbaiki menunggu close selesai; proses kamera tetap dilepas dan uji native lulus.
4. Pembukaan hardware pertama index 0 sempat gagal setelah dua frame; penyebab belum terisolasi. Buka ulang dan multi-camera pada run itu berhasil. [Bukti awal](evidence/stage-06-cameras-first-attempt.json) dipertahankan. Run ulang lebih panjang dengan sedikitnya 60 frame/kamera seluruhnya PASS, tanpa perubahan driver atau menurunkan batas penerimaan. Uji mandiri/soak tetap diperlukan.
5. Nomor kamera dapat berubah setelah sambung ulang; jenis yang dipilih pengguna tidak menjamin index tertentu. Resolusi/FPS merupakan permintaan, perangkat dapat memberikan nilai lain; status menampilkan resolusi aktual.
6. Penghapusan secret lama setelah commit bersifat best effort. Vault terkunci dapat meninggalkan item tidak direferensikan. Backup DB saja tidak memulihkan RTSP vault; prosedur restore Tahap 13 belum tersedia.

## Uji mandiri Tahap 6

Tutup aplikasi lama. Dari folder proyek:

```sh
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/manage_database.py check
.venv/bin/python main.py
```

- [ ] Check menunjukkan current/expected revision **0004_devices**, at_head/schema_valid true; tidak perlu reset database atau membuat ulang akun.
- [ ] Masuk sebagai Super Admin/Admin, buka **Perangkat**. Halaman dapat digulir untuk melihat tombol dan pratinjau di bawah formulir.
- [ ] Tambah “Webcam uji”: jenis sesuai perangkat, nomor kamera **0**, lokasi aktif, resolusi 1280×720, FPS 30. Simpan; pilih baris. Nama/lokasi wajib; nama duplikat ditolak.
- [ ] Klik **Uji koneksi**. Setelah satu frame status berhasil dan kamera berhenti; tidak menampilkan video terus-menerus.
- [ ] Klik **Mulai pratinjau terpilih**. Gambar bergerak dan hitungan frame meningkat; coba **Hentikan semua**, lalu mulai lagi. Bila nomor 0 bukan kamera yang dimaksud, coba 1 dan simpan perubahan.
- [ ] Tambahkan webcam kedua dengan nomor berbeda. Cmd+klik dua baris (Ctrl+klik di Windows), mulai pratinjau; keduanya berjalan. Memilih dua baris menonaktifkan uji koneksi tunggal.
- [ ] Saat preview aktif, pindah Dashboard lalu kembali: preview berhenti. Coba ulang dengan **Ganti password**, **Keluar akun** dan menutup jendela. Setelah stop selesai, kamera bisa dibuka kembali. Proses aplikasi tidak tertinggal hanya karena kamera aktif.
- [ ] Coba nomor kamera tidak tersedia, misalnya **15**: muncul status gagal aman tanpa membuka ulang nomor kamera secara otomatis; UI tetap merespons. Kembali ke nomor yang benar lalu simpan.
- [ ] Saat webcam USB aktif, cabut USB: gambar lama dibersihkan dan kamera berhenti dengan petunjuk mulai manual; tidak boleh otomatis membuka kamera laptop. Sambungkan lagi, periksa nomor kamera dan mulai manual. Catat hasil aktual.
- [ ] Edit nama/resolusi/FPS; muat ulang dan pilih kembali. Hapus perangkat uji: **Tidak** membatalkan, **Ya** menghapus jika belum ada riwayat.
- [ ] Masuk Operator/Viewer: menu Perangkat tidak tersedia.

Untuk mencoba penanganan RTSP gagal tanpa IP camera, buat perangkat RTSP dengan alamat sintetis `rtsp://127.0.0.1:9/stream`. Ini seharusnya **gagal**; keberhasilan penanganan error tidak berarti RTSP positif sudah lulus. Saat sumber nyata tersedia, masukkan kredensial langsung di aplikasi, pilih lokasi, simpan, uji koneksi/preview, putus-sambung sumber lalu periksa pemulihan. Setelah tersimpan, sumber lengkap tidak kembali ke input; field kosong mempertahankan sumber lama. Keychain dapat meminta izin.

Pengujian metadata kamera otomatis (membuka kamera nyata, tanpa menyimpan gambar):

```sh
.venv/bin/python scripts/check_cameras.py --indices 0 1
```

Default hasil di .local/stage-06-cameras.json. Tes ini tidak mencabut kabel dan tidak memverifikasi stream RTSP positif. Tutup preview aplikasi lain sebelum menjalankannya. Laporkan perangkat/nomor, langkah dan hasil jika ada kegagalan. Gerbang Tahap 6 tetap tertunda sampai cakupan hardware yang diwajibkan selesai atau perubahan scope secara eksplisit disepakati.

## Perbaikan uji mandiri — CAM-B003

Pengguna melaporkan USB pada index 0 dicabut lalu retry membuka kamera laptop. Nomor index OpenCV bukan identitas fisik yang stabil. Perbaikan menghentikan retry otomatis untuk seluruh webcam lokal (INTERNAL/USB), termasuk kegagalan open/read. UI menampilkan petunjuk memeriksa perangkat/nomor dan mulai kembali manual. Retry terbatas hanya berlaku untuk sumber RTSP yang memiliki alamat. Ini mitigasi sebelum dukungan identitas lokal stabil; pemilihan manual yang salah tetap dapat membuka kamera berbeda, sehingga pengguna harus memverifikasi gambar.

Regresi mensimulasikan index yang setelah gagal akan mengembalikan sumber lain bila dibuka ulang: USB dan INTERNAL harus berhenti dengan attempts 0, tanpa frame/proses/buffer tertinggal. RTSP tetap diuji reconnect/recover. Tombol mulai manual dan pesan halaman perangkat ikut diuji. Hasil uji tambahan dicatat di evidence/stage-06-local-disconnect.xml dan evidence/stage-06-local-disconnect-native.xml. Run 191/coverage di atas adalah baseline sebelum CAM-B003; bukti tambahan tidak mengubah angka baseline tersebut. Cabut fisik setelah perbaikan masih perlu diuji ulang pengguna.

Webcam dapat dijadikan sumber RTSP melalui publisher video (misalnya FFmpeg) dan server RTSP (misalnya MediaMTX), kemudian StarGate membaca URL stream itu. Memilih jenis RTSP tidak membuat publisher/server secara otomatis. Referensi melalui MCP Context7: [MediaMTX generic webcams](https://github.com/bluenviron/mediamtx/blob/main/docs/3-publish/15-generic-webcams.md). Pengujian protokol dengan sumber webcam ini berbeda dari pengujian kamera IP, firmware dan jaringan target.

## Review pengguna dan kelanjutan

Pengguna mengonfirmasi perpindahan USB ke kamera laptop telah terselesaikan setelah restart aplikasi. Pengguna kemudian menyatakan review OK dan mengizinkan lanjut. Uji cabut USB diterima berdasarkan konfirmasi pengguna, bukan bukti hardware otomatis tambahan. RTSP positif tetap NOT RUN karena belum tersedia. Instruksi lanjut menjadi izin mengerjakan Tahap 7 dengan kekurangan RTSP tetap terbuka; tidak mengubah hasil RTSP menjadi PASS.
