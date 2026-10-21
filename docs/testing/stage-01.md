# Hasil Tahap 1 - Instalasi dan smoke test

Tanggal: 18 Oktober 2026 (Asia/Jakarta). Status: **Lulus dan disetujui pengguna**. Pengguna telah meninjau, mendapat panduan uji mandiri, lalu menyatakan “sudah saya review dan sudah OK, bisa dilanjutkan” pada 18 Oktober 2026. Tahap 2 diizinkan.

## Lingkungan yang diuji

- OS teramati: macOS 27.0.1 arm64; Python proyek 3.11.17 dalam `.venv`. Python sistem 3.14 tidak diganti.
- PostgreSQL 17.11 (Homebrew), pgvector server 0.8.7. Cluster terpisah `.local/postgres` pada 127.0.0.1:55432, tanpa service login otomatis.
- Database `stargate_dev` dan `stargate_test`; role aplikasi terbatas `stargate_app`, role migrasi `stargate_migrator`. Kredensial acak `.env` mode 0600, diabaikan Git.
- PyQt6 6.11.0, Qt runtime 6.11.2; SQLAlchemy 2.0.55, psycopg 3.3.6, pgvector Python 0.5.1.
- InsightFace 2.1, ONNX Runtime 1.31.0, OpenCV 4.11.0.86, PyTorch 2.14.1, NumPy 1.26.4. Seluruh versi transitif ada di `../../requirements-macos-arm64.lock.txt`.
- Kamera terdeteksi: C922 Pro Stream Webcam dan FaceTime HD Camera. Dua indeks OpenCV berhasil mengirim frame 1920x1080. Urutan Qt tidak dipakai sebagai jaminan mapping indeks OpenCV.

## Implementasi lingkungan

- [x] Git diinisialisasi dan `.gitignore` melindungi environment, kredensial, cluster, bobot, data wajah dan backup lokal.
- [x] Virtual environment dan dependensi terpasang; lock versi macOS dibuat.
- [x] PostgreSQL/pgvector, role terpisah, development/test DB disiapkan tanpa tabel produk.
- [x] Aset RetinaFace Caffe, ArcFace 512D, landmark alignment pendukung dan MiniFASNetV2 dipin; tujuh checksum sumber/bobot diverifikasi.
- [x] Definisi jaringan MiniFASNet disimpan dari commit upstream tetap dengan lisensi dan atribusi.
- [x] Script setup, download, smoke, start/stop/status disediakan.
- [x] README instalasi, batas Windows dan troubleshooting dibuat.
- [x] Smoke test dan perbaikan lingkungan dijalankan; bukti tersanitasi tersimpan.
- [x] Pengguna meninjau hasil Tahap 1 dan menyatakan lanjut ke Tahap 2.

## Hasil aktual

| ID | Pemeriksaan / expected | Hasil aktual | Status | Bukti |
|---|---|---|---|---|
| ENV-01 | Python 3.11 dan semua import dependensi berhasil | Seluruh 19 dependensi langsung berhasil diimpor; bcrypt hash/verify menerima benar dan menolak salah | PASS | [Imports](evidence/stage-01-imports.json) |
| ENV-02 | Dependensi konsisten dan rahasia lokal terlindungi | pip check tidak menemukan dependensi rusak; `.env` 0600; environment/data/model diabaikan Git | PASS | [Dependencies/privacy](evidence/stage-01-dependencies-privacy.json) |
| ENV-03 | Dua database dapat diakses, pgvector aktif, vector 512D round-trip dan urutan cosine benar | Vektor sintetis identik berjarak 0 dan berlawanan berjarak 2; nearest ID benar di dev/test | PASS | [Database](evidence/stage-01-database.json) |
| ENV-04 | App role tanpa superuser/createdb/createrole/CREATE permanen | Flag administratif false; schema CREATE tidak diberikan; percobaan CREATE ditolak SQLSTATE 42501; temporary table terhapus setelah commit | PASS | [Database](evidence/stage-01-database.json) |
| ENV-05 | Cluster dapat stop/start dan konfigurasi/koneksi bertahan | Stop/start/status exit 0; smoke database setelah restart PASS; server ditinggalkan running | PASS | [Lifecycle](evidence/stage-01-db-lifecycle.json) |
| ENV-06 | Aset cocok hash dan model dapat dimuat/dijalankan | 7 checksum cocok; RetinaFace forward, ArcFace output 1x512 finite, MiniFASNetV2 output 1x3 finite; landmark model loaded | PASS | [Models](evidence/stage-01-models.json) |
| ENV-07 | PyQt6 event loop dan timer berjalan offscreen lalu exit bersih | PASS | PASS | [Offscreen Qt](evidence/stage-01-qt-offscreen.json) |
| ENV-08 | Jendela native dibuka, event loop/timer berjalan dan menutup bersih | Jendela diagnostic 8 detik, exit 0; penilaian tampilan aplikasi belum termasuk tahap ini | PASS | [Native Qt](evidence/stage-01-qt-native.json) |
| ENV-09 | Dua kamera terdeteksi | C922 Pro Stream Webcam dan FaceTime HD Camera; device serial tidak dicatat | PASS | [Inventory](evidence/stage-01-camera-inventory.json) |
| ENV-10 | Kamera indeks 0 dapat dibuka, membaca frame, lalu release | 1920x1080, frame tersimpan 0 | PASS setelah perbaikan izin | [Camera 0](evidence/stage-01-camera-0.json) |
| ENV-11 | Kamera indeks 1 dapat dibuka, membaca frame, lalu release | 1920x1080, frame tersimpan 0 | PASS setelah USB disambungkan | [Camera 1](evidence/stage-01-camera-1.json) |
| ENV-12 | Persetujuan pengguna untuk menutup tahap | Diterima dari pengguna 18 Oktober 2026 | PASS | Persetujuan langsung di chat |

[Ringkasan environment](evidence/stage-01-environment.json) menggabungkan pemeriksaan yang dijalankan secara terpisah. Tidak mengklaim satu run gabungan jika tidak dijalankan demikian.

## Debug dan perbaikan yang dilakukan

1. Inisialisasi cluster pertama ditolak sandbox pada shared memory. Ulangi dengan izin proses yang sesuai; cluster berhasil dibuat dengan autentikasi local peer dan host SCRAM, tanpa melonggarkan menjadi trust.
2. Uji kamera awal BLOCKED karena izin belum diberikan macOS. Pengguna mengaktifkan izin; pembacaan frame indeks 0 kemudian lulus.
3. Indeks 1 sempat BLOCKED karena sistem hanya melihat satu kamera. Pengguna menyambungkan USB; inventory dan kedua indeks kemudian lulus. Bukti JSON menyimpan hasil terbaru; riwayat awal dipertahankan di laporan ini.
4. Laporan Qt awal memakai versi compile sebagai runtime. Perbaiki menggunakan `qVersion()`; ulangi import check. Runtime aktual 6.11.2, compile API 6.11.0.
5. Inventaris `system_profiler` dari sandbox sempat kosong walau OpenCV sudah menerima frame. Gunakan enumerasi Qt Multimedia dengan izin perangkat; inventory akhirnya dua kamera. Hasil kosong tidak dipakai untuk menyimpulkan perangkat tidak tersedia.

Peringatan cache/telemetry ONNX Runtime atau cache pip yang tidak dapat ditulis di sandbox tidak menggagalkan import/inference. Tidak ada perubahan izin global cache untuk menghilangkan peringatan.

## Batas hasil dan pekerjaan tertunda

- Belum ada login, halaman produk, member, attendance atau schema produk. Semua TC-US-* tetap NOT RUN.
- Inferensi menggunakan array sintetis: tidak mengukur akurasi, spoof rejection, alignment pada wajah nyata, atau SLA.
- Kamera diuji berurutan; penggunaan bersamaan/multi-camera, kualitas frame, deteksi dan RTSP diuji pada Tahap 6-7. RTSP tidak tersedia pada tahap ini dan bukan dinyatakan lulus.
- Lock adalah macOS arm64; reinstall bersih lengkap dan packaging/Windows tetap perlu bukti pada Tahap 14. Tidak ada pengujian Windows yang diklaim.
- Lisensi penggunaan/distribusi bobot ArcFace harus dipenuhi sebelum distribusi produksi. Model saat ini dipakai untuk evaluasi development; data relawan belum dikumpulkan.
- Tidak menjalankan coverage fitur karena belum ada kode fitur; tidak membuat klaim coverage >=80% dari script smoke.

## Cara pengguna meninjau tahap

Baca tabel hasil dan README. Jika ingin mengulang pemeriksaan, gunakan perintah smoke pada README; jendela native dapat dilihat selama delapan detik. Akses kamera hanya memeriksa frame tanpa menyimpannya. Tahap berikutnya adalah fondasi aplikasi, konfigurasi, logging dan lifecycle worker, setelah review Tahap 1 diterima.
