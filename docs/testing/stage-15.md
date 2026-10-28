# Tahap 15: regresi dan pengukuran awal

Tanggal: 28 Oktober 2026. Dasar aplikasi: commit `52cea60`, installer **0.14.1-research**. Putaran ini menambahkan alat pengujian dan bukti; kode aplikasi hasil installer tetap sama.

## Dasar melanjutkan

Pengguna meminta mencoba versi terbaru di Parallels dan melanjutkan karena deadline. Pengguna kemudian mengonfirmasi dashboard terlihat setelah login dengan akun SMP fiktif. Keputusan D-29 menerima kelanjutan bersyarat ke Tahap15: AMD fisik dan kamera kedua ditunda. Pengujian yang tertunda tetap dicatat sebagai belum diuji.

Installer terbaru dipasang pada akun Windows pemakai. Hash installer diperiksa dan konfigurasi lama dipastikan tetap sama. Ruang uji interaktif baru memakai `%LOCALAPPDATA%\StarGate-Parallels-0141`; tabel dan data dasar dibuat otomatis, lalu seeder SMP dijalankan. Pintasan desktop **StarGate Uji Parallels.cmd** membuka ruang ini. Akun seeder tersedia melalui [panduan seeder](../school-seeder.md); data dan akun tersebut hanya untuk pengujian.

## Uji interaktif dan kamera Windows

| Pemeriksaan | Hasil |
|---|---|
| Instalasi pada akun pemakai, konfigurasi sebelumnya | Lulus; konfigurasi sebelumnya dipertahankan |
| Pemeriksaan runtime/model dari installer | Lulus |
| Setup ruang uji baru dan pemeriksaan schema | Lulus |
| Login dan dashboard pada jendela Windows | Dikonfirmasi pengguna; judul dan form versi terbaru terlihat |
| Inventaris perangkat kamera Windows | FaceTime HD Camera, status OK |
| Kamera indeks0, preview | Lulus; 30 frame pada1280x720, dilepas bersih |
| Kamera indeks0, buka kembali | Lulus; 30 frame pada1280x720, dilepas bersih |
| Indeks kamera yang tidak tersedia | Error terkendali dan proses dilepas |
| Kamera indeks1 | Tidak dapat dibuka; inventaris hanya satu kamera. Pengguna memilih menunda kamera kedua |

Helper kamera memakai modul dan dependensi executable yang dipasang. Berkas pendamping uji tidak masuk installer customer. Frame hanya diproses di memori; tidak menyimpan foto, video atau embedding wajah. Login manual dikonfirmasi pengguna karena alat kendali tidak berhasil meneruskan input ke Windows; hal ini tidak dicatat sebagai kegagalan login aplikasi.

## Regresi dan coverage

Run penuh selesai: **536 PASS,1 SKIP,0 failure/error**,629,48detik. PostgreSQL test nyata, model nyata dan native credential dengan namespace uji diaktifkan. Satu SKIP adalah protected DACL Windows yang tidak dijalankan pada Mac; tes Windows sebelumnya tetap menjadi bukti terpisah. Satu FutureWarning berasal dari API `estimate` InsightFace/skimage; model nyata lulus, tidak mengubah versi dependency pada putaran ini.

Coverage statement gabungan unit/integrasi/UI: **89,70%**,7.941 dari8.853 statement,912 belum tercakup, tanpa exclusion. Branch coverage dan unit-only tidak diukur terpisah. [JUnit regresi](evidence/stage-15-regression.xml) dan [ringkasan coverage per berkas](evidence/stage-15-summary.json) menyimpan hasil aktual. Pemetaan31 user story tersedia pada [peta penerimaan](stage-15-acceptance-map.md).

Coverage mengukur `app`, `database` dan `ai` pada proses utama. Proses anak, executable Windows serta benchmark dicatat melalui hasil terpisah. Tidak menjumlahkan tes Mac dan Windows sebagai jumlah kasus unik atau memakai coverage Mac sebagai coverage executable Windows.

## Baseline pencarian

Alat `scripts/testing/benchmark_search.py` menyiapkan schema sementara dengan10.000 anggota fiktif dan5 embedding512D per anggota, total50.000 vektor acak. Query menggunakan fungsi `identify` produksi dan aturan sampel terbaik per anggota aktif. Seribu probe independen, lima pemanasan, pengukuran query pertama, p50/p95/maksimum dan seluruh latency disimpan. Setiap hasil harus mengembalikan ID fiktif yang diharapkan. Schema sementara dibuang sesudah pengujian, bukan schema public.

Query pertama sesudah pengisian data tidak disebut kondisi OS dingin. Benchmark tidak memasukkan capture, deteksi wajah, pembuatan embedding, simpan absensi atau feedback. Vektor acak tidak mengukur pengenalan wajah manusia. p95 dibandingkan dengan target100ms sebagai pengamatan awal; protokol SLA lengkap pada [strategi penerimaan](acceptance-strategy.md) tetap dipisahkan dari sertifikasi hasil.

Pencarian tetap exact. Dokumentasi resmi [pgvector](https://github.com/pgvector/pgvector#querying) yang diperiksa melalui Context7 menjelaskan bahwa indeks approximate menukar sebagian recall dengan kecepatan; putaran awal ini mempertahankan metode produksi untuk mengukur baseline.

Hasil pada **Windows11 ARM64 Parallels, executable x64**:

| Pengukuran | Hasil |
|---|---|
| Anggota dan vektor | 10.000 anggota,50.000 vektor,512 dimensi |
| Probe terukur setelah5pemanasan | 1.000 |
| Query pertama | 775,26ms; bukan klaim OS dingin |
| Median/p50 | 305,32ms |
| p95 | **364,83ms** |
| Maksimum | 957,27ms |
| Hasil ID fiktif | 1.000/1.000 sesuai data yang ditanam |
| Perbandingan target100ms | **Belum terpenuhi pada VM** |
| Pembersihan | Schema sementara berhasil dibuang |

Benchmark berjalan setelah regresi selesai; jendela StarGate tetap terbuka. Hasil ini belum membuktikan latency pada AMD fisik. Tidak menyatakan akurasi wajah100% dari kecocokan vektor sintetis. Temuan **PERF-B001** tetap terbuka; langkah berikutnya memeriksa query plan dan biaya query produksi sebelum memilih perbaikan. Tidak mengubah algoritme atau target untuk membuat hasil terlihat lulus.

Rig awal menamai schema dengan prefix baru yang ditolak pengaman engine. Rig kemudian menggunakan prefix schema uji yang sudah diizinkan. Pengaman produksi tetap sama; percobaan tersebut tidak masuk1.000sampel hasil akhir.

## Bukti Windows dan cara melanjutkan uji

Bukti nonbiometrik berada di [folder uji Parallels](evidence/parallels-interactive-20261028/): [instalasi](evidence/parallels-interactive-20261028/install.json), [schema](evidence/parallels-interactive-20261028/schema.json), [kamera](evidence/parallels-interactive-20261028/cameras.json), [inventaris](evidence/parallels-interactive-20261028/camera-inventory.json), dan [seluruh latency pencarian](evidence/parallels-interactive-20261028/search-scale.json).

Pintasan desktop **StarGate Uji Parallels.cmd** tetap tersedia dan membuka data SMP pada ruang terpisah. Akun contoh Super Admin: `smp.superadmin`; password uji yang sudah tercantum pada seeder: `SmpSuperadmin2026!`. Gunakan kredensial ini hanya pada data simulasi. Pintasan Start Menu biasa mengikuti konfigurasi lama yang dipertahankan, sehingga pintasan uji digunakan untuk putaran ini.

Helper camera/search yang dibuat khusus pengujian sudah dihapus dari folder aplikasi sesudah selesai. Aplikasi dan database uji tetap tersedia untuk pengguna. Frame kamera tidak disimpan dan schema50.000vektor benchmark sudah dibuang; data SMP tetap ada.

## Masih terbuka

- PERF-B001: target pencarian100ms belum terpenuhi pada kapasitas10.000anggota di VM; perlu profiling dan perbaikan terukur.
- AMD fisik, USB kedua/cabut fisik dan RTSP positif.
- Registrasi lima sudut dan alur IN/OUT wajah nyata, audio serta pembaca laporan Windows.
- Startup20run, latency deteksi/recognition/save/end-to-end dan pengujian antrean.
- Akurasi genuine/impostor serta foto cetak/replay dengan jumlah percobaan tercatat.
- Soak8jam dan observasi availability; tidak diklaim dari smoke test.

Tahap15 belum dinyatakan selesai. Kelanjutan karena deadline tidak mengubah hasil yang belum tersedia menjadi lulus.

## Pemeriksaan copy

- PASS: angka kamera berasal dari metadata run, sedangkan konfirmasi dashboard berasal dari jawaban pengguna.
- PASS: tujuan dokumen adalah membedakan hasil aktual, pengujian sintetis dan hal yang ditunda.
- PASS: tidak mengubah desain antarmuka atau menambah klaim akurasi dari data fiktif.
- PASS: istilah statistik dibatasi pada hasil terukur; protokol dan sumber resmi disebutkan.
