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

## Regresi akhir kandidat0.14.2

Setelah jalur exact top-one dan migrasi penyimpanan diterapkan, regresi sumber menghasilkan **538 PASS,1 SKIP,0 failure/error** dalam610,67detik. Coverage gabungan **89,73%**,7.959 dari8.870 statement,911 belum tercakup dan0 exclusion. SKIP tetap tes DACL native Windows pada Mac; FutureWarning upstream tetap satu. Dua tes database tambahan memeriksa kesetaraan hasil top-one dan pelestarian data lama saat migrasi. [JUnit akhir](evidence/stage-15-final-regression.xml) dan [coverage akhir](evidence/stage-15-final-summary.json) mempertahankan angka aktual terpisah dari baseline.

Tes paket penyerahan dijalankan terpisah dari regresi aplikasi:5 PASS. Tes tersebut memeriksa hash seluruh isi, penolakan installer berubah, penolakan `.env` privat/tautan, dan perlindungan arsip lama. [JUnit assembler](evidence/stage-16-release-assembler.xml).

Penyimpanan vektor inline saja masih memindahkan metadata kecil ke TOAST. Perbaikan menambahkan target tuple4096 dan menulis ulang nilai lama, lalu mempertahankan pencarian exact. Dasar teknis diperiksa melalui dokumentasi resmi pgvector dan PostgreSQL menggunakan Context7: [pgvector](https://github.com/pgvector/pgvector#troubleshooting), [parameter tabel PostgreSQL17](https://www.postgresql.org/docs/17/sql-createtable.html), [TOAST](https://www.postgresql.org/docs/17/storage-toast.html). Percobaan100probe memberi p95 sekitar35ms; angka ini hanya diagnosis dan belum menutup PERF-B001 sebelum pengukuran produksi1.000probe.

## Pemisahan coverage

Pemilihan `not database and not models` menghasilkan207PASS,1SKIP dan336deselected dalam33,21detik. Coverage pada scope terukur adalah **43,56%** (3.794/8.710 statement), tanpa exclusion. Pemilihan ini masih mencakup UI dan native credential sehingga bukan klasifikasi unit murni. Tidak mengklaim target unit-only80% terpenuhi atau mengganti denominator dengan hanya berkas yang mudah diuji. [Ringkasan subset](evidence/stage-15-unit-summary.json), [JUnit subset](evidence/stage-15-unit-regression.xml). Pemetaan suite unit murni dan penambahan pengujian perilaku yang diperlukan tetap menjadi pekerjaan penerimaan; tidak menambah tes yang hanya menyalin implementasi untuk menaikkan angka.

## Paket Windows0.14.2 dan pengukuran produksi akhir

Installer baru berhasil dibangun dan dipasang pada akun Windows standar. Hash salinan Mac cocok. Konfigurasi lama dipertahankan; ruang uji terpisah dimigrasikan ke `0006_search_storage`. Pemeriksaan SQL aktual menemukan80anggota,4akun,2.467peristiwa kehadiran dan0embedding. Ini cocok dengan baseline seeder; bukan perbandingan menyeluruh seluruh data pengguna sebelum/sesudah. Tes data embedding lama berada pada47tes terarah migrasi, menggunakan fixture terisolasi.

Model/Qt/plugin/native library/spawn serta worker AI pada frame kosong lulus dari executable terpasang. Pemeriksaan ini tidak menguji wajah asli atau spoof. Bobot dan runtime database berasal dari bundle; tidak mengandalkan Python proyek untuk menjalankan aplikasi.

Benchmark akhir memakai helper yang memuat PYZ/modul produksi dari hasil build0.14.2. Tidak ada monkeypatch query atau perubahan storage eksperimental pada run ini. Dataset/RNG/jumlah probe tetap sama dengan baseline:10.000anggota,50.000vektor512D,1.000probe setelah5pemanasan. Build/kompresi dan tes model tidak berjalan bersamaan dengan benchmark. Jendela aplikasi ditutup pada run akhir, sedangkan baseline terdahulu mencatat UI tetap terbuka; perbandingan ini belum menjadi eksperimen perangkat yang terkontrol penuh.

| Pengukuran produksi0.14.2 | Hasil |
|---|---|
| Query pertama, bukan OS dingin | 132,26ms |
| p50 | 39,90ms |
| p95 | 50,92ms |
| p99 | 76,27ms |
| Maksimum | 228,82ms |
| Query terukur >100ms | 3dari1.000 |
| ID sintetis sesuai expected | 1.000dari1.000 |
| Schema sementara | Berhasil dibuang |
| Kebijakan storage | PLAIN; heap136.536.064byte, total136.609.792byte |

**p95 sudah di bawah100ms, tetapi seluruh query belum memenuhi batas100ms. PERF-B001 tetap OPEN untuk ekor latency dan query pertama.** Tidak menutup target PRD dengan menghapus tiga hasil lambat atau mengulang sampai mendapatkan run yang terlihat lulus. Profil akhir menunjukkan pembacaan519blok pada query EXPLAIN; cache/I/O dan penjadwalan VM perlu diperiksa bersama pengujian perangkat target. Tidak menyimpulkan tiga lonjakan pasti berasal dari salah satu penyebab tersebut.

Angka ini bukan akurasi wajah100% dan tidak mengukur capture/detection/embedding/save/feedback. Hasil Parallels x64 emulasi tetap terpisah dari AMD fisik. [Bukti akhir Windows](evidence/stage-15-final-windows/) memuat identitas installer, schema, model, hitungan data serta seluruh latency. Installer berukuran484.054.536byte, manifest6227berkas, belum ditandatangani Authenticode. Daftar pekerjaan berikutnya ada pada [gerbang penerimaan](remaining-acceptance.md).

### Kamera pada kandidat0.14.2

Percobaan pertama kamera0 gagal dengan0frame, tetapi shutdown bersih. Inventaris FaceTime HD Camera tetap OK. Probe OpenCV source kemudian dapat membaca frame640x480 dan1280x720. Pengulangan helper frozen, dengan trace metadata tambahan dan kode capture produksi yang sama, lulus preview30frame1280x720 (6,36detik), reopen30frame1280x720 (4,83detik) dan error indeks tak tersedia dengan pelepasan bersih. Tidak menyimpan frame/foto/embedding. [Percobaan pertama](evidence/stage-15-final-windows/cameras-first-attempt.json) dipertahankan di samping [hasil ulang](evidence/stage-15-final-windows/cameras.json). CAM-B004 tetap OPEN karena penyebab kegagalan awal belum terisolasi; uji ulang tidak menghapus kejadian tersebut.

Setelah benchmark, SQL aktual kembali menunjukkan80anggota/4akun/2.467kehadiran/0embedding pada ruang uji. Schema benchmark telah dibuang dan helper executable uji dihapus dari folder aplikasi. Aplikasi produksi dibuka kembali dengan pintasan ruang simulasi yang sama. Konfirmasi login/dashboard pengguna sebelumnya berasal dari0.14.1; tidak mengubahnya menjadi UAT lengkap0.14.2.
