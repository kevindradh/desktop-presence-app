# Hasil Tahap 2 - Fondasi aplikasi

Tanggal: 18 Oktober 2026 (Asia/Jakarta). Status: **Lulus dan disetujui pengguna**. Pengguna memeriksa simulasi error, memastikan perilakunya, lalu menyetujui lanjut pada 18 Oktober 2026.

## Cakupan implementasi

- [x] Struktur app, ai, database, resources, logs dan entrypoint sesuai susunan PRD.
- [x] Kerangka PyQt6 dengan Dashboard dan 9 tujuan navigasi lain, termasuk halaman pemeriksaan untuk review pembangunan.
- [x] Pemisahan presentasi, konfigurasi dan layanan; repository/model/report/adapter AI masih struktur untuk tahap berikutnya.
- [x] Pemuatan default PRD, override dotenv/environment, validasi tipe/rentang/zona waktu/syntax tanpa mencetak input sensitif.
- [x] Worker QObject/QThread dengan progress, result, error, cancellation dan shutdown kooperatif.
- [x] Error terpusat dari worker/callback UI dengan pesan aman dan nomor referensi.
- [x] Log diagnostik berotasi 1 MiB + 5 backup, file mode 0600, penyaringan secret/RTSP/embedding dan traceback tanpa pesan mentah.
- [x] Unit/integrasi komponen, UI offscreen, smoke jendela native dan pemeriksaan screenshot.
- [x] Panduan uji mandiri dan arsitektur diperbarui.
- [x] Pengguna menguji/meninjau tahap ini dan menyatakan lanjut 18 Oktober 2026.

## Lingkungan

macOS arm64, virtual environment Python 3.11.17, PyQt6 6.11.0 / Qt runtime 6.11.2 dari lock Tahap 1. Tidak menambah library atau mengubah lock dependensi. Tidak ada perubahan schema DB, akses kamera, pemuatan AI atau pengumpulan data wajah dalam pengujian tahap ini.

## Hasil pengujian

| ID | Pemeriksaan | Hasil aktual | Status | Bukti |
|---|---|---|---|---|
| FND-01 | Konfigurasi hilang/valid/invalid dan prioritas override | Default hilang memakai PRD; file eksplisit hilang/directory/encoding/syntax/rentang salah ditolak; repr dan pesan tidak membuka secret | PASS | test_config.py dan test_bootstrap.py |
| FND-02 | Entry point, UI error, startup gagal log, shutdown | Proses terisolasi menguji main/event loop, hook exception, error startup dan penutupan bersih; hook dipulihkan dan handler ditutup | PASS | test_bootstrap.py |
| FND-03 | Log privacy/rotation | Password termasuk key prefiks/dict, URL kredensial dan payload vector disaring; exception source/message tidak ditulis; rotasi 2 backup uji dan permission 0600 benar | PASS | test_diagnostic_logging.py |
| FND-04 | Worker di thread terpisah dan GUI hidup | Task berbeda thread; timer GUI tetap berjalan; task kedua ditolak ketika busy; progress/result diterima | PASS | test_tasks_and_ui.py |
| FND-05 | Error, cancel, retry dan cleanup worker | Error aman dengan ref; cancel task menunggu dapat berhenti <1s di test; controller dapat digunakan ulang | PASS | test_tasks_and_ui.py |
| FND-06 | Navigasi dan input | Sepuluh halaman, tombol card dan keyboard navigasi berfungsi; placeholder tidak mempunyai aksi data | PASS | tests dan smoke UI |
| FND-07 | Simulasi sukses tanpa freeze | Progress 100%, hasil sukses; berpindah halaman tetap bekerja, 16 detak UI selama task pada run native | PASS | [Native](evidence/stage-02-smoke-native.json), [offscreen](evidence/stage-02-smoke-offscreen.json) |
| FND-08 | Simulasi kesalahan UI | Pesan aman beserta nomor referensi, aplikasi tetap terbuka dan dapat retry | PASS | Native/offscreen, [screenshot error](evidence/stage-02-diagnostic-error.png) |
| FND-09 | Close saat task aktif | Cancel -> worker settled -> close bersih; sekitar 0,030s native dan 0,016s offscreen pada task simulasi | PASS | Native/offscreen |
| FND-10 | Tampilan dasar | Dashboard, sidebar, cards, pesan error, status/clock diperiksa; clock awal sempat terpotong, sudah diperbaiki dan screenshot native diulang | PASS | [Dashboard](evidence/stage-02-dashboard.png) |
| FND-11 | Suite dan coverage | 26/26 tests lulus; coverage app 87.66% (533/608 statements), threshold 80% lulus | PASS | [JUnit](evidence/stage-02-tests.xml), [coverage](evidence/stage-02-coverage-summary.json) |
| FND-12 | Review pengguna | Diterima dari pengguna 18 Oktober 2026 | PASS | Persetujuan langsung di chat |

Coverage mencakup seluruh package app tanpa pengecualian untuk menaikkan angka. Startup di subprocess dan kode Python pada native Qt thread tidak seluruhnya terukur oleh run coverage parent; karena itu coverage bootstrap masih 0% dalam laporan meskipun skenario startup dijalankan terpisah. Smoke bukan pengukuran SLA produk.

## Uji mandiri pengguna

Dari folder proyek:

```sh
.venv/bin/python main.py
```

- [ ] Jendela terbuka dengan Dashboard dan label pratinjau; menu berpindah tanpa error.
- [ ] Buka Pemeriksaan aplikasi -> Jalankan pemeriksaan: progress dan detak UI bergerak; hasil sukses muncul sekitar tiga detik.
- [ ] Selama pemeriksaan, pindah halaman lalu kembali; UI tidak macet.
- [ ] Jalankan lagi -> Batalkan: status pembatalan muncul, tombol dapat digunakan lagi.
- [ ] Simulasikan kesalahan: pesan bernomor referensi muncul; klik Tutup pesan dan jalankan pemeriksaan kembali.
- [ ] Tutup saat pemeriksaan masih berjalan: jendela menutup tanpa crash/hang dan dapat dibuka ulang.
- [ ] Tampilan pada layar pengguna terbaca; laporkan bagian yang terpotong atau tidak nyaman.

Opsional otomatis:

```sh
.venv/bin/python main.py --check-config
.venv/bin/python -m pytest --cov=app --cov-fail-under=80 --cov-report=term-missing
.venv/bin/python scripts/smoke_foundation.py --visible --output docs/testing/evidence/stage-02-smoke-native.json
```

## Debug dan batasan

- Pemeriksaan visual menemukan clock header terlalu sempit saat teks berubah dari kosong; minimum width diperbaiki dan screenshot native memverifikasi perbaikan.
- Review logging menemukan pola credential berprefiks/berbentuk dictionary perlu penyaringan lebih luas; pola diperbaiki dan regression test ditambahkan.
- Parser konfigurasi memvalidasi syntax sebelum dotenv_values sehingga baris rusak tidak diam-diam dianggap konfigurasi default.
- No critical defect ditemukan pada skenario fondasi yang dijalankan; ini bukan klaim seluruh produk bebas bug.
- Aksi bisnis, login/role, database schema/audit bisnis, kamera/AI terintegrasi, laporan dan backup belum diimplementasikan. Semua US produk tetap NOT RUN.
- Menu operasional adalah placeholder berlabel, bukan fitur yang sudah selesai. Pemeriksaan memakai task sintetis dan tidak membuktikan kualitas pengenalan wajah atau liveness.
- Cancellation bergantung task kooperatif; adapter native AI/I/O berikutnya wajib memakai timeout/batas operasi. Jangan menggeneralisasi angka close task simulasi ke model yang macet.
- Pengujian Windows dan installer tetap Tahap 14. Log diagnostik tahap ini terpisah dari audit bisnis Tahap 3.

Referensi arsitektur dan Context7: [architecture](../architecture.md). Hasil Tahap 1 telah disetujui pengguna sebelum tahap ini dimulai.
