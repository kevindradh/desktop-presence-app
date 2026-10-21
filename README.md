# StarGate

Aplikasi desktop absensi wajah sesuai dua PDF pada proyek. Tahap 0–13 telah direview pengguna pada cakupan tersedia; RTSP positif tetap tertunda. Tahap 13 menyediakan audit, cadangan terenkripsi dan pemulihan data dengan registrasi wajah ulang.
Urutan dan gerbang pengujian ada di [PLAN.md](PLAN.md).

## Uji mandiri dan demo Tahap 12

Tutup aplikasi lama, jalankan `main.py` dan buka **Laporan** (Super Admin/Admin/Operator/Viewer). Pilih periode/filter, lalu **Tampilkan laporan**. Excel/PDF berisi seluruh hasil yang dimuat, termasuk halaman berikutnya; ubah filter lalu tampilkan kembali untuk memperbarui hasil.

Demo cepat langsung menyiapkan akun Viewer dan 65 baris sintetis:

```bash
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/demo_reports.py
```

Coba ekspor dari halaman kedua: file tetap berisi 65 baris. [Panduan Tahap 12](docs/testing/stage-12.md) menjelaskan pemeriksaan file, snapshot, pembatalan dan batas font/Windows. Verifikasi: 399 regresi PASS (coverage run 90,11% sebelum perapian visual), 13 tes ekspor final dan 65 native PASS. Review Tahap13 diterima. Installer Tahap14 sudah dibangun/dipasang di Windows Parallels; [uji mandiri Windows](docs/testing/stage-14-manual.md) dan review pengguna masih terbuka.

## Uji mandiri dan demo Tahap 11

Tutup aplikasi lama, jalankan `main.py`, lalu buka **Dashboard** sebagai Super Admin/Admin/Operator. Ringkasan dan aktivitas diperbarui otomatis saat halaman terlihat. Pilih tanggal kerja; untuk shift malam pilih tanggal saat shift dimulai. Terlambat termasuk Hadir, sedangkan Absent baru dihitung setelah akhir shift.

Untuk review cepat dengan lima peserta dan angka awal yang sudah disiapkan:

```bash
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/demo_dashboard.py
```

Klik **Simulasikan check-in terminal lain** dan periksa pembaruan tanpa refresh manual. Demo menggunakan data sintetis di database test terpisah. Verifikasi Tahap 11: **371 tes/89,59% coverage, 59 native PASS**. [Panduan dan definisi Tahap 11](docs/testing/stage-11.md) memuat langkah, batas dan bukti. Review Tahap 11 sudah disetujui; pengujian aktif sekarang Tahap 12.

## Uji mandiri Tahap 10

Jalankan `main.py`, login Super Admin/Admin/Operator lalu buka **Kehadiran**. Admin menyiapkan perangkat, shift dan penugasan anggota terlebih dahulu. Pilih kamera/mode, berikan persetujuan peserta, lalu **Mulai absensi**. Riwayat serta suara sukses muncul setelah transaksi tersimpan. Tinggalkan area kamera minimal satu detik sebelum scan berikutnya dan perhatikan jeda default 60 detik. AUTO mengikuti IN/OUT, mode istirahat tersedia terpisah.

Panduan lengkap termasuk shift malam, konfigurasi, checkout otomatis/catch-up dan pengujian gangguan: [Tahap 10](docs/testing/stage-10.md). Verifikasi awal 334 tes regresi/89,90% coverage dan 47 tes native PASS. Review Tahap 10 sudah disetujui; pengujian aktif sekarang Tahap 11.

## Uji mandiri Tahap 9

Jalankan `main.py`, login Super Admin/Admin dan buka **Pengaturan**. Ubah similarity ke 0,65 lalu simpan; restart aplikasi untuk memeriksa persistensi. **Anggota → Uji wajah tersimpan** memakai konfigurasi database terbaru saat pemeriksaan dibuat. Konfigurasi proses berjalan tetap sampai pemeriksaan ditutup. Registrasi lima sudut tetap liveness aktif/0,85. Aturan absensi akan dijalankan pada Tahap 10.

Panduan lengkap: [Tahap 9](docs/testing/stage-09.md). Review Tahap 9 sudah diterima dan Tahap 10 diizinkan.

## Uji mandiri Tahap 8

```sh
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python main.py
```

Masuk Super Admin/Admin/Operator lalu buka **Anggota**. Isi ID/nama/grup dan gunakan **Capture lima sudut**. Setelah lima sudut diterima, periksa foto depan dan simpan. Anggota aktif juga memiliki **Registrasi ulang wajah** dan **Uji wajah tersimpan** untuk memeriksa probe baru setelah restart tanpa membuat absensi.

Kebijakan pilihan pengguna: simpan foto profil/lima embedding selama aktif dan diperlukan; nonaktif menghapus biometrik aplikasi, histori tetap. Registrasi ulang mengganti set lama setelah set baru berhasil disimpan. Dasar beberapa sumber resmi dan batas penghapusan ada di [retensi biometrik](docs/biometric-retention.md).

Panduan dan bukti: [Tahap 8](docs/testing/stage-08.md). Review pengguna sudah diterima; rincian skor/jumlah percobaan nyata tidak dilaporkan.

## Demo cepat Tahap 10

Data awal disiapkan otomatis, dengan tombol untuk menjalankan sembilan skenario dan halaman Kehadiran menggunakan kamera/wajah sintetis. Tidak memakai data operasional atau webcam nyata.

```bash
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/demo_attendance.py
```

Klik **Jalankan semua (9 skenario)**, lalu **Simpan hasil JSON**. Untuk mencoba halaman aplikasi, pilih tab **Coba halaman Kehadiran**. [Panduan demo](docs/testing/stage-10-demo.md) menjelaskan kontrol dan batas pengujian.

## Uji mandiri Tahap 7

```sh
.venv/bin/python scripts/demo_ai.py
```

Alat uji ini terpisah dari aplikasi kerja, tanpa login/database. Centang persetujuan peserta, pilih nomor kamera dan mulai. Coba wajah asli, referensi sementara/probe baru, orang berbeda, foto cetak dan replay video. Foto dan embedding hanya di memori; stop/close membuang referensi. Hasil angka tiap percobaan dapat dicatat sementara di alat; tidak ada registrasi anggota atau absensi.

Panduan lengkap dan batas hasil: [Tahap 7](docs/testing/stage-07.md). Review Tahap 7 sudah disetujui pengguna. Pengujian aktif sekarang Tahap 11.

## Uji mandiri Tahap 6

```sh
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/manage_database.py check
.venv/bin/python main.py
```

Masuk sebagai Super Admin/Admin, lalu buka **Perangkat**. Tambahkan webcam dengan nomor 0 atau 1, pilih lokasi, lalu simpan. Pilih baris untuk **Uji koneksi** atau **Mulai pratinjau terpilih**. Kamera hanya dibuka atas tindakan tersebut. Sumber RTSP lengkap disimpan di Keychain/Credential Manager.

Panduan dan checklist: [Tahap 6](docs/testing/stage-06.md). Dua webcam nyata lulus pada 1280×720; RTSP positif nyata dan uji cabut fisik masih tertunda. Tahap 7 sudah mulai atas instruksi pengguna; RTSP tetap tertunda.

## Uji mandiri Tahap 5

Tutup aplikasi lama, lalu jalankan `.venv/bin/python main.py`. Gunakan akun yang
sudah dibuat. Grup/shift dapat dikelola pada data kerja; registrasi wajah sekarang tersedia melalui alur Tahap 8.

Untuk menguji anggota/pagination/riwayat dengan data sintetis terpisah:

```sh
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/demo_administration.py
```

Demo administratif Tahap 5 bertanda MODE UJI SINTETIS; gunakan main.py untuk capture/model nyata Tahap 8. Sebanyak 25 anggota contoh hanya di schema unik database
test. Tutup normal untuk membersihkan data/aset demo; aplikasi kerja tidak diubah.
Peran lain: tambahkan `--role admin`, `--role operator` atau `--role viewer`.
Foto uji tersedia di [resources/samples/profile-test.png](resources/samples/profile-test.png).

Panduan langkah demi langkah: [Tahap 5](docs/testing/stage-05.md).
Tahap 5 sudah disetujui; pengujian aktif sekarang Tahap 8.

## Login dan akun (Tahap 4)

Dari folder proyek:

```sh
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python main.py
```

1. Jika belum ada akun, pilih **Buat Super Admin pertama**. Isi username, nama
   dan password awal 12–72 byte UTF-8, lalu ulangi password. Tidak ada akun atau
   password bawaan. Jika sudah membuat akun melalui CLI, gunakan akun tersebut.
2. Masuk dengan akun tadi. Ganti password awal sebelum membuka ruang kerja.
3. Buka **Pengguna** untuk membuat akun Admin, Operator atau Viewer. Akun baru
   wajib mengganti password awal saat pertama masuk. Hanya Super Admin yang
   dapat membuat, mengubah, menonaktifkan atau mereset akun.
4. Coba **Ganti password**, **Keluar akun**, password salah, dan navigasi tiap
   role. Viewer hanya memperoleh Laporan; halaman laporan masih pratinjau.
5. Coba **Ingat saya**, tutup jendela, lalu jalankan aplikasi kembali. macOS
   dapat meminta izin Keychain. Token disimpan aman; password tidak disimpan.
   Jika penyimpanan aman tidak tersedia, login biasa tetap dapat digunakan.

Checklist rinci dan hasil aktual: [laporan Tahap 4](docs/testing/stage-04.md).
Tahap 4 sudah disetujui; review yang aktif sekarang Tahap 8.

Lima kegagalan login mengunci akun selama 15 menit. Idle 15 menit mengakhiri sesi;
animasi/timer tidak memperpanjangnya. Logout, timeout, reset/change password,
nonaktif atau perubahan akun mencabut token lama. Ingat saya berlaku 30 hari,
dengan sesi interaktif terpisah; tutup aplikasi normal mempertahankan remember,
sedangkan logout dan timeout mencabutnya. Password reset tampil sekali dan wajib
diganti. Menonaktifkan akun mempertahankan riwayat audit.

Pada menu **Pemeriksaan aplikasi** (Super Admin/Admin/Operator), simulasi sukses,
error dan batal dari Tahap 2 tetap tersedia. Error simulasi sengaja menampilkan
pesan aman dengan referensi; aplikasi tetap merespons. Grup/shift/administrasi anggota sudah aktif; kamera/absensi/laporan masih
pratinjau. Aplikasi belum membuka kamera atau memuat AI.

Konfigurasi berasal dari `.env` lokal; `STARGATE_*` mengungguli nilainya. Validasi
konfigurasi dapat dijalankan tanpa GUI:

```sh
.venv/bin/python main.py --check-config
.venv/bin/python main.py --config /absolute/path/to/test.env --check-config
```

Log diagnostik: `logs/stargate.log`, rotasi 1 MiB + lima backup, mode 0600.
Audit bisnis/auth tersimpan di database. Jangan bagikan `.env`, password, token
atau data biometrik. Nomor referensi menghubungkan error tak terduga dengan log.

Pengujian otomatis lengkap:

```sh
.venv/bin/python -m pytest --run-db --run-models --cov=app --cov=database --cov=ai --cov-fail-under=80 --cov-report=term-missing
```

Uji native Keychain dijalankan terpisah secara opt-in di macOS (membuat lalu
menghapus token sintetis pada namespace uji unik):

```sh
STARGATE_TEST_NATIVE_KEYCHAIN=1 .venv/bin/python -m pytest --run-db tests/test_keychain_native.py -q
```

Smoke fondasi historis masih bisa dijalankan dengan
`.venv/bin/python scripts/smoke_foundation.py`. Ia memakai principal/guard
sintetis untuk menguji UI/task, tidak mengakses database dan bukan bukti login.
Entry point produk selalu melalui layar login.

## Lingkungan awal

- Pengembangan: macOS Apple Silicon, Python 3.11 (virtual environment `.venv`).
- Distribusi target: Windows; installer dan validasi Windows pada Tahap 14.
- PostgreSQL 17 + pgvector lokal untuk satu komputer dahulu.
- PyQt6; RetinaFace melalui OpenCV DNN; ArcFace melalui InsightFace/ONNX Runtime;
  MiniFASNetV2 melalui PyTorch. Semua inference awal memakai CPU.
- Dataset nyata belum dikumpulkan. Model smoke memakai array sintetis.

## Instalasi development di macOS

Jalankan dari folder proyek. Python sistem tidak perlu diganti.

```sh
brew install python@3.11 postgresql@17 pgvector
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos-arm64.lock.txt
.venv/bin/python -m pip check
```

`requirements.in` menyatakan dependensi langsung dan batas versi. Lock mencatat
hasil resolusi macOS arm64 yang diuji; versi Python dan PostgreSQL dicatat pada
laporan Tahap 1. Jika mengubah dependensi, ulangi smoke test sebelum memperbarui
lock. Lock macOS tidak menjadi bukti kompatibilitas Windows.

## Database dan migrasi

Migrasi `0004_devices` sudah diterapkan pada database development/test lokal.
Terdapat **14 tabel aplikasi** dan satu tabel versi Alembic. Seed awal hanya
konfigurasi dan lokasi; tidak membuat member, wajah, absensi atau akun default.

Untuk pengujian mandiri:

```sh
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/manage_database.py check
.venv/bin/python scripts/manage_database.py check --database test
```

Hasil yang diharapkan: `at_head: true`, `schema_valid: true`,
`application_table_count: 14`, serta missing_tables/missing_columns kosong.
`check` hanya membaca metadata dan melakukan SELECT dengan akun aplikasi.
Login, Users, grup/shift, administrasi anggota dan perangkat/kamera sudah aktif; registrasi wajah/absensi masih menunggu tahap terkait.

Uji regresi lengkap dengan PostgreSQL nyata:

```sh
.venv/bin/python -m pytest --run-db --run-models --cov=app --cov=database --cov=ai --cov-fail-under=80 --cov-report=term-missing
```

Tanpa `--run-db`, test integrasi database akan **SKIPPED**, bukan dianggap lulus.
Uji native Keychain juga SKIPPED kecuali STARGATE_TEST_NATIVE_KEYCHAIN=1.
Pengujian memakai schema unik `stage3_test_*` di database test, lalu membersihkannya.
Jangan menjalankan tes ketika ada migrasi atau uji restart lain yang berlangsung.

Uji persistensi opsional berikut merestart cluster development lokal sebentar;
jalankan ketika tidak ada operasi database lain yang aktif:

```sh
.venv/bin/python scripts/smoke_database_persistence.py --restart-local
```

Data sintetis ditempatkan dalam schema sementara, dibandingkan sebelum/sesudah
restart, lalu dihapus bersama schema tersebut. Data di public tidak dihapus.
Tidak ada kamera atau model nyata yang dipakai.

Untuk pemasangan baru, sesudah provisioning Tahap 1:

```sh
.venv/bin/python scripts/manage_database.py upgrade
.venv/bin/python scripts/manage_database.py seed
.venv/bin/python scripts/manage_database.py upgrade --database test
.venv/bin/python scripts/manage_database.py seed --database test
```

Seed aman diulang dan tidak menimpa setting yang sudah diubah. Migrasi tidak
dijalankan otomatis ketika GUI dibuka. Jangan edit revision yang sudah diterapkan;
buat revision berikutnya untuk perubahan schema.

Bootstrap akun awal disiapkan melalui terminal interaktif:

```sh
.venv/bin/python scripts/manage_database.py bootstrap-admin
```

Perintah meminta username, nama dan password dua kali tanpa menampilkan password.
Tidak ada password default; jika Super Admin aktif sudah ada, bootstrap ditolak
untuk melindungi akun tersebut. Ini membuat akun nyata pada database development;
alternatif dari tombol **Buat Super Admin pertama** pada layar login.
Akun yang sudah dibuat lewat salah satu cara dapat langsung dipakai pada GUI.
Jangan mengirimkan password atau isi `.env` melalui chat.

Panduan struktur/keamanan: [database](docs/database.md).
Hasil dan checklist: [Tahap 3](docs/testing/stage-03.md).

## Database development

Script di bawah mengelola cluster khusus proyek, bukan cluster default Homebrew.
Server hanya mendengarkan `127.0.0.1:55432`; tidak otomatis aktif saat login.
Perintah init/start membutuhkan izin shared memory dan socket pada lingkungan
yang membatasi proses. Jangan menjalankan PostgreSQL sebagai root.

```sh
.venv/bin/python scripts/local_postgres.py init
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/provision_local_db.py
```

Provisioning membuat `stargate_dev`, `stargate_test`, pgvector, akun migrator dan
akun aplikasi terbatas. Kredensial acak disimpan dalam `.env` dengan mode `0600`,
tidak dicetak. Jalankan provisioner sekali; jika `.env` sudah ada, jangan jalankan
ulang untuk mengganti kredensial. Akun aplikasi tidak boleh membuat tabel
permanen atau mengelola role/database. Tabel aplikasi dibuat lewat migrasi eksplisit Tahap 3 di atas.

```sh
.venv/bin/python scripts/local_postgres.py status
.venv/bin/python scripts/local_postgres.py stop
```

Data cluster berada di `.local/postgres`, socket `.local/pgsocket`, log server
`.local/postgres.log`. Folder `.local` dan `.env` diabaikan Git. Jangan menghapus
folder data untuk memperbaiki masalah koneksi. Bila provisioning terputus,
periksa role/database dan konfigurasi yang sudah terbentuk sebelum melanjutkan;
script sengaja menolak menimpa resource yang sudah ada.

## Model AI

```sh
.venv/bin/python scripts/download_models.py
```

Downloader memeriksa SHA-256 sesuai [manifest](models/manifest.json), menyimpan
model lokal, dan tidak menjalankan training. Hash dipin dari unduhan HTTPS awal,
bukan tanda tangan publisher. Flag `--record-initial-hashes` hanya dipakai saat
memilih aset baru yang belum dipin, bukan untuk melewati checksum mismatch.

- RetinaFace: `Widerface-RetinaFace.caffemodel` + `deploy.prototxt` dari MiniVision.
- ArcFace: `w600k_r50.onnx`; landmark alignment `2d106det.onnx` dari InsightFace
  release v0.7. Arsip buffalo_l disimpan di cache `.local/downloads`, tetapi
  model SCRFD di dalamnya tidak diekstrak/dimuat.
- MiniFASNetV2: checkpoint `2.7_80x80_MiniFASNetV2.pth`, definisi jaringan upstream
  dipin di `third_party/minifasnet`; pemuatan menggunakan `weights_only=True`.

File dan checksum lengkap: [manifest](models/manifest.json). Provenance dan lisensi
kode: [third_party](third_party/minifasnet/README.md). Pretrained InsightFace
dibatasi untuk penelitian nonkomersial kecuali ada lisensi terpisah; model untuk
distribusi produksi harus diselesaikan sebelum rilis. Lisensi PyQt/Qt serta
komponen lain juga dicatat ulang pada Tahap 16.

## Smoke test Tahap 1

```sh
.venv/bin/python scripts/smoke_environment.py --output docs/testing/evidence/stage-01-environment.json
.venv/bin/python scripts/smoke_environment.py --only qt --visible --output docs/testing/evidence/stage-01-qt-native.json
.venv/bin/python scripts/smoke_environment.py --only camera --camera-index 0 --output docs/testing/evidence/stage-01-camera-0.json
.venv/bin/python scripts/smoke_environment.py --only camera --camera-index 1 --output docs/testing/evidence/stage-01-camera-1.json
```

Default memeriksa import, hash password uji sementara, database/pgvector 512D,
hak akses akun, checksum/model inference sintetis dan event loop Qt offscreen.
Database test memakai temporary table yang dibuang saat commit; tidak membuat
member atau attendance. Test Qt native membuka jendela delapan detik lalu menutup.
Test kamera membaca frame untuk memeriksa koneksi lalu melepaskan kamera; tidak
menyimpan atau menampilkan frame. macOS mungkin meminta izin kamera untuk host
terminal/aplikasi. Indeks 0/1 belum tentu sama dengan nama hardware tertentu;
konfirmasikan mapping saat uji perangkat.

Exit code 0 hanya jika semua check yang dipilih PASS. Kamera yang tidak tersedia
atau izinnya ditolak diberi BLOCKED dan exit nonzero; bukan PASS. Output JSON hanya
memuat metadata teknis tersanitasi. Tidak ada klaim akurasi/liveness/SLA dari smoke.

## Windows

Siapkan Python 3.11 x64, PostgreSQL 17 beserta extension pgvector, lalu virtual
environment. Script cluster/provisioning saat ini ditujukan untuk macOS dengan
Unix socket/peer authentication; jangan menjalankannya sebagai setup Windows.
Prosedur Windows, pin platform dan installer akan diverifikasi pada Tahap 14.
Script smoke Python dapat dipakai setelah koneksi `.env` dan model tersedia;
pengujian Windows tetap tertunda sampai ada lingkungan Windows nyata.

## Troubleshooting

| Gejala | Pemeriksaan |
|---|---|
| Import dari Python yang salah | Gunakan `.venv/bin/python`; versi proyek 3.11 |
| `could not create shared memory segment` | Jalankan init/start dengan izin proses yang memadai; jangan ganti autentikasi menjadi trust |
| Port 55432 dipakai | Periksa proses yang memiliki port; jangan hentikan service lain secara otomatis |
| Koneksi ditolak | Jalankan `local_postgres.py status`, periksa log dan `.env` lokal tanpa membagikan password |
| Extension `vector` tidak ada | Pastikan pgvector terpasang untuk PG17; provisioning membuat extension dengan akun administratif |
| Qt platform plugin gagal | Periksa virtual environment dan paket PyQt6/Qt6; jangan menyalin plugin dari instalasi Qt lain |
| Kamera BLOCKED | Periksa USB/perizinan macOS dan aplikasi lain yang memakai kamera; ulangi test indeks yang sesuai |
| Model/hash gagal | Periksa manifest, download sumber resmi dan cache; jangan menerima hash baru secara otomatis |
| Model bisa dimuat tetapi hasil wajah buruk | Evaluasi preprocessing, alignment dan data nyata pada Tahap 7; smoke bukan uji kualitas |

Hasil aktual: [laporan Tahap 1](docs/testing/stage-01.md).
Keputusan kebutuhan: [decisions](docs/decisions.md).

## Audit dan cadangan Tahap 13

Review Tahap 12 diterima. Super Admin dapat membuat cadangan terenkripsi dan memulihkan data; Admin/Super Admin dapat memfilter audit. Restore mengakhiri sesi dan mewajibkan registrasi wajah ulang, sesuai kebijakan retensi 7 hari yang disetujui.

Demo sintetis terpisah dari data kerja:

```bash
.venv/bin/python scripts/demo_backups.py
```

Verifikasi final: **442 regresi PASS/90,64% coverage dan 69 native macOS PASS**. Restore diuji pada schema test terpisah; database kerja tidak dipulihkan untuk pengujian. [Panduan dan batas pemulihan](docs/testing/stage-13.md). Review Tahap 13 diterima. Installer Tahap14 sudah dibuat dan dipasang di Windows; hasil teknis pada [Tahap14](docs/testing/stage-14.md), [uji mandiri/review](docs/testing/stage-14-manual.md) masih terbuka.

## Persiapan Windows / Parallels Tahap14

[Petunjuk build dan instalasi Windows](docs/windows-install.md) dan [checklist UAT](docs/testing/stage-14.md). Kit sumber dibuat dengan `scripts/prepare_windows_kit.py`; ini bukan executable Windows. Model penelitian hanya masuk melalui flag eksplisit. Folder data pengguna terpisah dari binary dan tidak dihapus saat uninstall recipe. Windows harus dibangun/diuji di Windows; gate tahap ini tetap terbuka hingga hasil guest tersedia.

Verifikasi persiapan Tahap14 di macOS: **452 regresi PASS/89,97% coverage**, **69 native PASS**, probe worker model lokal dan 8 tes codec portabilitas PASS. Windows/Parallels belum dibangun/diuji karena VM gagal start akibat kapasitas disk dan pengguna memilih mengujinya kemudian. Status ini tidak menyatakan gerbang Tahap14 lulus.
