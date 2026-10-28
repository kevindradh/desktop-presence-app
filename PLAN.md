# PLAN - Pembangunan StarGate

Tanggal dibuat: 18 Oktober 2026; pembaruan tahap aktif: 20 Oktober 2026  
Status28 Oktober2026: Tahap0–13 direview pengguna pada cakupan yang tersedia. Windows x64 diuji di Parallels; pengguna mengonfirmasi dashboard dan mengizinkan kelanjutan bersyarat ke Tahap15 (D-29). Regresi akhir538PASS/1SKIP, coverage gabungan89,73%; kandidat0.14.2 terpasang dan p95 exact search50,92ms, tetapi3dari1.000query masih>100ms. Dokumentasi Tahap16 disiapkan. RTSP positif, AMD fisik, statistik biometrik, SLA lengkap, soak, availability dan syarat coverage unit masih terbuka.

Revisi pengguna 21 Oktober 2026: penyiapan Super Admin otomatis sebelum login dan penggantian password opsional untuk seluruh akun, termasuk hasil reset. Migrasi0005 mempertahankan akun, password dan riwayat. Tahap15 kemudian dimulai bersyarat28 Oktober2026.

## 1. Acuan dan tujuan

Membangun aplikasi desktop absensi wajah StarGate secara bertahap sesuai:

1. `StarGate - Face Recognition Attendance System.pdf` (PRD v1.0, 16 halaman).
2. `StarGate - User Stories dan Acceptance Criteria.pdf` (31 user stories, 13 epic, 10 halaman).

Plan ini mengatur urutan implementasi dan verifikasi. Kedua PDF tetap menjadi sumber kebutuhan. Detail yang belum ditetapkan atau bertentangan dicatat dan diputuskan sebelum fitur terkait dikerjakan. Perubahan ruang lingkup harus dicatat; jangan mengubah kebutuhan secara diam-diam.

## 2. Cara kerja dan gerbang setiap tahap

- Kerjakan satu tahap aktif pada satu waktu. Tahap dapat dipecah menjadi sesi kecil.
- Tandai `[x]` hanya setelah pekerjaan benar-benar selesai dan bukti tersedia.
- Pisahkan status implementasi, pengujian, dan persetujuan tahap. Implementasi selesai belum berarti tahap lulus.
- Jalankan pemeriksaan otomatis yang relevan, lalu uji manual bersama pengguna untuk perilaku yang terlihat.
- Catat hasil aktual, lingkungan uji, bukti, dan bug. Jangan menandai pengujian kamera/model nyata berdasarkan mock.
- Jika pengujian gagal: reproduksi -> cari penyebab -> perbaiki -> uji ulang kasus gagal -> jalankan regresi yang terdampak.
- Akhiri sesi dengan memperbarui plan, hasil pengujian, dan langkah berikutnya.
- Lanjut ke tahap berikutnya setelah pengujian tahap lulus dan pengguna menyatakan tahap dapat dilanjutkan.
- Persetujuan plan ini tidak sekaligus memulai instalasi atau implementasi seluruh tahap.

Status yang digunakan: `Belum dimulai`, `Dikerjakan`, `Menunggu pengujian`, `Perbaikan`, `Lulus`, `Terhambat`.

### Checklist wajib sebelum sebuah tahap ditutup

- [ ] Seluruh checklist implementasi tahap selesai.
- [ ] Acceptance criteria yang menjadi cakupan tahap dipetakan dan diuji.
- [ ] Pemeriksaan otomatis yang relevan lulus.
- [ ] Pengujian manual/integrasi yang relevan lulus; keterbatasan lingkungan dicatat.
- [ ] Bug Critical tidak ada yang terbuka; bug lain dan dampaknya dicatat.
- [ ] Hak akses dan audit log diuji untuk fitur yang membutuhkannya.
- [ ] Dokumentasi dan bukti pengujian diperbarui.
- [ ] Hasil tahap ditinjau pengguna dan disetujui untuk lanjut.

## 3. Stack dan batas ruang lingkup

### Stack sesuai PRD

- Bahasa dan UI: Python, PyQt6.
- AI: RetinaFace untuk deteksi; InsightFace/ArcFace untuk embedding 512 dimensi; MiniFASNet untuk liveness.
- Data: PostgreSQL, pgvector, SQLAlchemy ORM. Operasi data aplikasi menggunakan ORM/query terparameterisasi, tanpa raw SQL pada layanan aplikasi.
- Password: bcrypt.
- Laporan: Pandas, OpenPyXL, ReportLab.
- Kamera: internal webcam, USB webcam, IP camera melalui RTSP.

### Alat pendukung yang ditetapkan pada Tahap 0-1

Kandidat: OpenCV, NumPy, ONNX Runtime sesuai format model, psycopg, Alembic, pytest, pytest-cov, serta alat packaging seperti PyInstaller. Ini melengkapi implementasi, bukan mengganti stack PRD. Catat versi, kompatibilitas, dan alasan pemilihan. DDL untuk pemasangan pgvector/migrasi dipisahkan dari query data aplikasi dan didokumentasikan.

### Di luar V1

Mobile app, Cloud SaaS, GPS tracking, payroll, face mask recognition, dan visitor management. Roadmap V2 seperti WhatsApp, cloud synchronization, serta API gateway tidak menjadi prasyarat kelulusan V1.

## 4. Keputusan yang harus diselesaikan sebelum fitur terkait

- [ ] Tetapkan OS/perangkat target pengembangan dan distribusi; ketersediaan webcam, RTSP, CPU/GPU, RAM, dan resolusi uji.
- [ ] Tentukan database lokal atau server LAN, jumlah terminal/kamera, dan perilaku saat database tidak tersedia. Jangan mengasumsikan sinkronisasi offline sudah termasuk V1.
- [ ] Tetapkan versi Python/library serta bobot model RetinaFace, ArcFace, dan MiniFASNet; periksa sumber unduhan, checksum, dan hak penggunaannya tanpa mengganti arsitektur PRD.
- [ ] Selesaikan aturan scan: cooldown 60 detik, penolakan duplicate check-in, dan scan berikutnya sebagai check-out (US-011/012). Tentukan state/event yang membedakan duplicate dengan checkout yang sah.
- [ ] Tentukan pemilihan event IN/OUT/BREAK_OUT/BREAK_IN dan perilaku scan setelah shift selesai.
- [ ] Selesaikan hak akses Users: matriks PRD hanya memberi akses Super Admin, sedangkan US-025/026 menyebut Admin. Catat keputusan dan acceptance test yang mengikuti keputusan tersebut.
- [ ] Perjelas cakupan Operator, Supervisor, dan Auditor. Supervisor/Auditor muncul sebagai persona, tetapi bukan role pada matriks PRD; jangan menambah role otomatis.
- [ ] Tentukan penugasan shift, shift lintas tengah malam, zona waktu, early leave, dan arti batas tepat grace period.
- [ ] Tentukan sumber status Absent/On Leave, hari kerja/libur, serta denominator statistik dashboard.
- [ ] Tentukan aturan group yang masih digunakan, soft delete member, keunikan member ID/username, dan penggantian embedding saat registrasi ulang.
- [ ] Tentukan format/kolom laporan dan ekspor yang masih kosong di PRD, serta arti seluruh data sesuai tampilan ketika laporan memakai pagination.
- [ ] Tetapkan detail remember me, session timeout, account lockout, reset password, dan bootstrap Super Admin.
- [ ] Tetapkan retensi foto/embedding/audit, perlindungan backup dan kredensial RTSP, serta cakupan backup: database saja atau termasuk berkas foto dan konfigurasi.
- [ ] Tetapkan protokol pengukuran akurasi >=98%, spoof detection >=95%, dan availability 99,5%, termasuk dataset, jumlah percobaan, periode observasi, serta lingkungan.
- [ ] Perjelas DoD “Tidak ada bug severity Critical/Open”: catat interpretasi yang disepakati; jangan mengklaim selesai bila aturan bug belum jelas.

## 5. Tahapan pengerjaan

### Tahap 0 - Finalisasi kebutuhan dan skenario uji

Dependensi: tidak ada. Status: Lulus; review disetujui pengguna 18 Oktober 2026. Baseline dan detail lanjutan: `docs/decisions.md`.

- [x] Buat matriks kebutuhan PRD + US-001 sampai US-031, termasuk kebutuhan PRD tanpa user story.
- [x] Catat keputusan bagian 4; baseline disetujui, rincian teknis ditetapkan saat Tahap 1 dan rincian fitur sebelum tahap terkait.
- [x] Buat daftar skenario positif, negatif, batas nilai, dan kegagalan perangkat/jaringan.
- [x] Tetapkan spesifikasi data uji sintetis, akun per role dan prosedur sampel; pengumpulan wajah nyata menunggu izin/retensi sebelum Tahap 7.
- [x] Buat `docs/decisions.md`, `docs/requirements-traceability.md`, `docs/testing/`, dan `docs/bugs.md` saat tahap dijalankan.
- [x] Verifikasi: semua kebutuhan mempunyai tujuan implementasi dan metode uji; konflik yang ditemukan dicatat secara eksplisit (pemeriksaan struktural lulus; penerimaan usulan masih menunggu review).
- [x] Gerbang: cakupan V1, keputusan dasar, dan rencana pengujian disetujui pengguna 18 Oktober 2026.

### Tahap 1 - Instalasi dan pemeriksaan lingkungan

Dependensi: Tahap 0. Status: Lulus; pengguna telah menguji mandiri, meninjau dan menyetujui lanjut 18 Oktober 2026. Bukti: `docs/testing/stage-01.md`.

- [x] Siapkan repository/version control bila belum ada, `.gitignore`, konfigurasi contoh tanpa rahasia, dan direktori lokal yang tidak di-commit.
- [x] Buat virtual environment; kunci versi dependensi yang kompatibel.
- [x] Instal Python/PyQt6, alat uji, database driver, dan library pendukung yang disepakati.
- [x] Instal/siapkan PostgreSQL dan pgvector; gunakan akun aplikasi dengan hak seperlunya.
- [x] Siapkan runtime AI dan bobot model terverifikasi; dokumentasikan kebutuhan jaringan/unduhan awal.
- [x] Veriksa izin kamera dan koneksi perangkat yang tersedia.
- [x] Dokumentasikan instalasi dan troubleshooting di README.
- [x] Uji: import library, jendela PyQt6 minimal, koneksi database, ketersediaan pgvector, load runtime/model, akses kamera.
- [x] Debug: catat kegagalan versi, plugin Qt, driver, permission kamera, atau runtime AI; ulangi pemeriksaan setelah perbaikan.
- [x] Gerbang: instalasi terdokumentasi dan smoke test lulus; review/uji mandiri disetujui pengguna 18 Oktober 2026. Reinstall bersih/Windows tetap Tahap 14.

### Tahap 2 - Fondasi aplikasi, konfigurasi, dan logging

Dependensi: Tahap 1. Status: Lulus dan disetujui pengguna setelah uji mandiri, 18 Oktober 2026. Bukti: `docs/testing/stage-02.md`.

- [x] Buat struktur modular sesuai PRD: `app/{ui,pages,widgets,services,repositories,models,reports,exports,settings}`, `ai/{detector,recognizer,liveness,embedding}`, `database/{migrations,schema,seed}`, `logs`, `resources`, dan entry point.
- [x] Buat application shell, navigasi dasar, pemuatan konfigurasi, dan penanganan error terpusat.
- [x] Pisahkan UI, logika bisnis, repository, dan proses AI/kamera.
- [x] Siapkan worker serta komunikasi signals/slots; perubahan widget hanya dari thread UI.
- [x] Siapkan log diagnostik dengan rotasi; jangan mencatat password, URL RTSP berkredensial, atau embedding mentah.
- [x] Uji: aplikasi buka/tutup bersih, konfigurasi hilang/tidak valid, error worker, dan penghentian worker tanpa hang.
- [x] Gerbang: fondasi berjalan, error dapat didiagnosis, UI tidak freeze; pengguna menyetujui review/uji mandiri 18 Oktober 2026.

### Tahap 3 - Database, migrasi, dan audit dasar

Dependensi: Tahap 2. Status: Lulus dan disetujui pengguna 18 Oktober 2026. Bukti: `docs/testing/stage-03.md`.

- [x] Buat model/migrasi members, member_groups, face_embeddings `vector(512)`, shifts, attendance, devices, users, dan settings sesuai PRD.
- [x] Tambahkan struktur yang diperlukan untuk audit log dan penugasan shift berdasarkan keputusan kebutuhan.
- [x] Tetapkan relasi, foreign key, keunikan, indeks, timestamp/zona waktu, dan soft delete.
- [x] Buat repository, batas transaksi, seed setting default, dan bootstrap Super Admin yang aman.
- [x] Implementasikan pencatatan audit terpisah dari log diagnostik.
- [x] Uji integrasi pada PostgreSQL + pgvector nyata: migrasi database kosong, relasi, rollback, constraint, round-trip embedding, dan persistensi setelah restart.
- [x] Uji kegagalan koneksi dengan pesan yang dapat dipahami dan tanpa penulisan parsial.
- [x] Gerbang: skema dan repository terverifikasi; perubahan skema dapat dilacak melalui migrasi. Pengguna menyetujui lanjut 18 Oktober 2026.

### Tahap 4 - Login, session, role, dan user management

Dependensi: Tahap 3. Cakupan: US-001, 002, 025, 026 dan bagian login US-029. Status: Lulus; pengguna menyelesaikan review dan mengizinkan lanjut 18 Oktober 2026. Bukti: `docs/testing/stage-04.md`.

- [x] Implementasikan login, logout, bcrypt, remember me, change password, session timeout, dan account lockout.
- [x] Implementasikan role Super Admin/Admin/Operator/Viewer sesuai matriks yang disepakati.
- [x] Terapkan otorisasi pada layanan/aksi serta navigasi; menyembunyikan menu saja tidak cukup.
- [x] Implementasikan user CRUD dan reset password; lindungi bootstrap/pengelolaan Super Admin dari kondisi tanpa admin yang dapat login.
- [x] Catat audit login serta pembuatan, perubahan, penghapusan, dan reset akun tanpa menyimpan rahasia.
- [x] Uji login benar/salah, akun terkunci, timeout, remember me setelah restart, password berubah, reset, username duplikat, dan akses langsung tanpa izin.
- [x] Gerbang: seluruh skenario autentikasi dan matriks akses lulus; password tidak tersimpan plaintext. Pengguna menyetujui review setelah perbaikan AUTH-B004, 18 Oktober 2026.

### Tahap 5 - Group, shift, dan data member

Dependensi: Tahap 4. Cakupan: US-005, 006, 007, 015, 016, 019. Status: Lulus; pengguna menyetujui review/uji mandiri dan mengizinkan Tahap 6. Bukti: `docs/testing/stage-05.md`.

- [x] Implementasikan CRUD group dan penugasan member ke group.
- [x] Implementasikan CRUD shift: jam mulai/selesai, grace period, shift malam dan penugasan member; fondasi early leave tersedia, perhitungan event diuji Tahap 10.
- [x] Implementasikan daftar member dengan pagination, pencarian, filter nama/group/status aktif, detail, dan edit.
- [x] Siapkan formulir member: member ID, full name, group, photo wajib; email, phone, position opsional.
- [x] Jangan aktifkan penyelesaian registrasi absensi sebelum capture/embedding Tahap 8 tersedia.
- [x] Implementasikan konfirmasi soft delete dan perlindungan riwayat absensi; siapkan akses riwayat yang disambungkan pada Tahap 10.
- [x] Catat audit mutasi data yang relevan.
- [x] Uji field wajib/duplikat, pencarian dan pagination, relasi group/shift, penghapusan data yang direferensikan, dan penolakan akses tanpa izin.
- [x] Gerbang: pengelolaan data administratif lulus; fitur wajah yang belum aktif jelas statusnya. Review pengguna disetujui setelah ADM-B003.

### Tahap 6 - Devices dan pipeline kamera

Dependensi: Tahap 5. Cakupan: US-017, 018. Status: Review pengguna disetujui; pengguna mengonfirmasi cabut USB aman setelah restart dan mengizinkan lanjut Tahap 7. RTSP positif nyata tetap tertunda, bukan PASS. Bukti: `docs/testing/stage-06.md`.

- [x] Implementasikan registrasi perangkat: nama, tipe, RTSP URL, resolution, dan FPS.
- [x] Implementasikan preview dan test connection untuk webcam internal/USB serta RTSP.
- [x] Implementasikan lifecycle start/stop, timeout, kamera terlepas, stream putus, reconnect terbatas, dan pelepasan perangkat saat keluar.
- [x] Siapkan multi-camera dengan batas konfigurasi dan antrean frame terkendali agar frame lama tidak menumpuk.
- [x] Lindungi kredensial RTSP pada penyimpanan, tampilan, dan log.
- [ ] Lengkapi uji kamera nyata (dua webcam, multi-camera, buka/tutup, sumber tidak tersedia dan RTSP salah lulus; cabut fisik dikonfirmasi pengguna setelah CAM-B003; RTSP positif belum diuji): preview, pindah halaman, buka/tutup berulang, RTSP salah, perangkat tidak tersedia, koneksi terputus, dan beberapa kamera.
- [ ] Gerbang: tiap tipe kamera wajib terbukti pada hardware/stream nyata; ketiadaan perangkat dicatat sebagai pengujian tertunda, bukan lulus.

### Tahap 7 - Engine deteksi, embedding, pencarian, dan liveness

Dependensi: Tahap 6. Status: Review pengguna disetujui setelah panduan uji mandiri dan pengguna mengizinkan Tahap 8; rincian skor/jumlah per kondisi tidak dikirim. RTSP positif Tahap 6 tetap NOT RUN. Bukti: `docs/testing/stage-07.md`.

- [x] Implementasikan RetinaFace, crop/alignment/preprocessing yang sesuai model, dan pemeriksaan kualitas wajah.
- [x] Implementasikan ArcFace melalui InsightFace dengan embedding 512 dimensi; cegah detektor ganda yang tidak diperlukan.
- [x] Implementasikan penyimpanan/pencarian pgvector dengan definisi similarity dan normalisasi yang konsisten.
- [x] Implementasikan MiniFASNet dan interpretasi skor sesuai model yang digunakan.
- [x] Muat konfigurasi awal similarity 0.60, anti-spoof enabled, anti-spoof threshold 0.85, recognition timeout 3 detik, dan max face size Auto sesuai PRD.
- [x] Tangani tidak ada wajah, beberapa wajah, wajah berkualitas rendah, model hilang/rusak, dan timeout; tentukan perilaku multi-face sesuai keputusan.
- [x] Uji unit dengan input terkendali dan integrasi dengan model nyata: embedding valid, identitas dikenal/tidak dikenal, preprocessing konsisten, dan pencarian hanya member aktif.
- [ ] Uji liveness awal menggunakan wajah nyata, foto cetak, dan replay layar/video; catat hasil tiap kondisi, bukan hanya skor rata-rata.
- [ ] Gerbang: semua komponen AI dapat diuji terpisah dan terhubung; uji nyata awal lulus. Target statistik penuh diverifikasi pada Tahap 15.

### Tahap 8 - Registrasi wajah multi-angle dan registrasi ulang

Dependensi: Tahap 5 dan 7. Cakupan: US-003, 004. Status: Review pengguna disetujui dan lanjut Tahap 9 diizinkan. Rincian per-skenario/skor uji nyata tidak dilaporkan. Bukti: `docs/testing/stage-08.md`.

- [x] Sambungkan formulir member dengan kamera dan engine AI.
- [x] Buat panduan capture depan/kiri/kanan/atas/bawah; validasi minimal lima sampel dari sudut yang diminta.
- [x] Simpan foto, data member, dan embedding secara konsisten; cegah data parsial jika capture/simpan gagal.
- [x] Implementasikan re-register face dengan kebijakan penggantian embedding yang disepakati.
- [x] Uji otomatis dengan data sintetis: field wajib kosong, wajah tidak terdeteksi, sampel kurang, pembatalan, kamera putus, database gagal, registrasi berhasil, dan registrasi ulang.
- [x] Gerbang diterima melalui review pengguna setelah panduan uji mandiri, termasuk pengenalan dari data tersimpan setelah restart; rincian hasil nyata tidak dilaporkan dan tidak diubah menjadi metrik akurasi.

### Tahap 9 - Settings dan konfigurasi aktif

Dependensi: Tahap 7-8. Cakupan: US-027, 028 dan perubahan setting US-029. Status: Review pengguna disetujui dan lanjut Tahap 10 diizinkan. Regresi 284 tes/90,37% coverage dan 37 tes native PASS. Bukti: `docs/testing/stage-09.md`. US-028 absensi end-to-end tetap Tahap 10.

- [x] Implementasikan setting recognition, anti-spoof, duplicate window 60 detik, check-in start berdasarkan shift, dan auto checkout opsional.
- [x] Validasi rentang/tipe nilai; definisikan kapan perubahan berlaku pada worker aktif.
- [x] Pastikan perubahan similarity ke 0.65 disimpan dan benar-benar digunakan engine.
- [x] Terapkan anti-spoof aktif/nonaktif pada engine dan tampilkan status dengan jelas; registrasi tetap aktif/0.85. Kewajiban liveness pada setiap transaksi absensi diuji saat pipeline Tahap 10 tersedia (US-028 belum PASS end-to-end).
- [x] Catat audit nilai lama/baru untuk setting yang bukan rahasia.
- [x] Uji akses role, nilai tidak valid, persistensi setelah restart, dan penerapan setting pada engine.
- [x] Gerbang review pengguna Tahap 9 disetujui; lanjut Tahap 10 diizinkan. Rincian hasil uji mandiri per kondisi tidak dilaporkan.

### Tahap 10 - Absensi lengkap dan aturan shift

Dependensi: Tahap 8-9. Cakupan: US-008 sampai US-012, US-020. Status: Review pengguna disetujui 20 Oktober 2026; 334 regresi/89,90% coverage dan 47 native PASS pada verifikasi awal, ditambah perbaikan tombol/demo yang diuji terpisah. Bukti: `docs/testing/stage-10.md`.

- [x] Implementasikan alur kamera -> deteksi -> liveness -> recognition -> validasi -> simpan.
- [x] Tolak commit hasil scan yang memakai kebijakan pengaturan kedaluwarsa; setelah anti-spoof diaktifkan, setiap attendance baru harus memiliki bukti liveness sesuai kebijakan aktif. Uji perubahan konfigurasi ketika scan sedang berjalan.
- [x] Implementasikan state/event IN, OUT, BREAK_OUT, BREAK_IN sesuai keputusan; tolak transisi tidak sah.
- [x] Terapkan cooldown default 60 detik dan duplicate prevention secara transaksional, termasuk scan bersamaan dari dua kamera/terminal.
- [x] Implementasikan late/grace period, early leave, shift lintas hari, dan auto checkout jika diaktifkan.
- [x] Tampilkan feedback sukses/gagal dan suara sukses; jangan tampilkan sukses sebelum transaksi tersimpan.
- [x] Hubungkan riwayat absensi pada halaman member; pastikan soft delete tidak menghapus riwayat.
- [x] Audit event absensi tanpa membocorkan data biometrik mentah.
- [x] Uji otomatis dengan input sintetis/fixture berlabel: wajah dikenal/tidak dikenal, spoof, member nonaktif, cooldown sebelum/tepat/setelah batas, duplikasi bersamaan, checkout, break, dan database gagal. Percobaan wajah/foto/replay nyata tetap pada gerbang UAT.
- [x] Uji contoh US-020: shift 08:00, grace 10 menit; 08:05 Present, 08:11 Late; uji 08:10 sesuai keputusan batas.
- [x] Sediakan aplikasi demo Tahap 10: sembilan skenario satu klik, data otomatis pada schema test sementara, halaman Kehadiran sintetis, jam simulasi dan ekspor hasil. Panduan: `docs/testing/stage-10-demo.md`; 11 tes demo/native PASS. Tidak menggantikan UAT kamera/wajah/speaker nyata.
- [x] Gerbang review pengguna Tahap 10 diterima dan lanjut diizinkan. Rincian/jumlah hasil kamera, foto/replay dan speaker tidak dilaporkan; bukti otomatis tetap tidak menggantikan hasil fisik tersebut.

### Tahap 11 - Dashboard dan monitoring real-time

Dependensi: Tahap 10. Cakupan: US-013, 014. Status: Review pengguna disetujui 20 Oktober 2026; 371 tes/89,59% coverage dan 59 native PASS. Definisi D-13 disetujui pengguna. Bukti: `docs/testing/stage-11.md`.

- [x] Tampilkan total anggota aktif, Hadir, Terlambat, Absent, Izin dan Belum masuk sesuai definisi D-13.
- [x] Implementasikan live activity feed otomatis dari event committed, termasuk dari terminal lain pada database sama.
- [x] Implementasikan grafik attendance per shift/group serta tren harian/bulanan memakai Qt, tanpa dependensi baru.
- [x] Tangani data kosong dan pergantian tanggal kerja/shift malam tanpa menghitung break/OUT sebagai jumlah orang.
- [x] Uji tanpa refresh manual, kecocokan dengan data sumber PostgreSQL, beberapa event/sesi tanpa duplikasi orang, shift malam, penulis terminal lain, fokus/rollover/filter/stale/revoke dan kamera sintetis; regresi lengkap serta native PASS.
- [x] Sediakan demo cepat lima anggota dan tombol simulasi check-in terminal lain, terpisah dari data operasional; grafik/native ditinjau visual.
- [x] Gerbang review pengguna Tahap 11 disetujui dan lanjut diizinkan. Bukti statistik/feed/fokus/kamera sintetis tersedia; persetujuan tidak dijadikan metrik fisik yang tidak dilaporkan.

### Tahap 12 - Laporan dan ekspor Excel/PDF

Dependensi: Tahap 10-11. Cakupan: US-021 sampai US-024. Status: Review pengguna disetujui 20 Oktober 2026; 399 regresi PASS, 13 ekspor final dan 65 native PASS. Coverage 90,11% dari run lengkap sebelum perapian visual, detail pada bukti. Format ringkasan per anggota/shift/tanggal dan ekspor seluruh hasil filter disetujui pengguna 20 Oktober 2026. Bukti: `docs/testing/stage-12.md`.

- [x] Implementasikan laporan harian/mingguan/bulanan/custom.
- [x] Implementasikan filter tanggal inklusif, grup, anggota, shift dan status; metadata zona dan waktu pemuatan.
- [x] Implementasikan XLSX Pandas/OpenPyXL (ringkasan + event) dan PDF ReportLab sesuai format yang disetujui.
- [x] Gunakan snapshot immutable terikat sesi agar ekspor seluruh halaman sesuai hasil yang dimuat; perubahan filter mewajibkan pemuatan ulang.
- [x] Jalankan ekspor di worker, tangani lokasi gagal ditulis, file lama, revoke, pembatalan dan publikasi atomik file lengkap.
- [x] Sediakan demo Viewer dengan 65 baris/dua halaman dan data sintetis otomatis di database test terpisah.
- [x] Cocokkan database, snapshot, UI dan ekspor: filter, kosong, nama panjang, Unicode, shift malam, nonaktif/grup historis, status, pagination, hak sesi dan pembatalan.
- [x] Buka ulang/validasi XLSX dua sheet dan render; periksa 71 baris/24 halaman PDF final, semua ID/header/footer, halaman awal/tengah/akhir dan native Viewer. Verifikasi Microsoft Excel/reader Windows tetap Tahap 14.
- [x] Gerbang: isi dan tampilan hasil ekspor terverifikasi serta akses Viewer sesuai ketentuan. Review pengguna diterima; lanjut Tahap 13 diizinkan.

### Tahap 13 - Audit lengkap, backup, dan restore

Dependensi: Tahap 12. Cakupan: US-029, 030, 031. Status: Review pengguna diterima 20 Oktober 2026; 442 regresi/90,64% coverage dan 69 native PASS. Kebijakan 7 hari/reenroll disetujui pengguna. Bukti/panduan: `docs/testing/stage-13.md`.

- [x] Verifikasi audit lintas fitur: login, attendance, member delete, user create/delete, dan settings change; lengkapi event penting lain yang disepakati.
- [x] Sediakan akses inspeksi/filter audit sesuai role yang disepakati.
- [x] Implementasikan backup/restore untuk Super Admin dengan validasi file dan penanganan error.
- [x] Pastikan cakupan foto/embedding/konfigurasi sesuai keputusan, dan dokumentasikan keterbatasannya.
- [x] Siapkan pengamanan restore: konfirmasi eksplisit, backup sebelum perubahan, hentikan penulisan aktif, dan prosedur pemulihan jika gagal.
- [x] Uji backup lalu restore pada database uji terpisah; bandingkan akun, member, embedding, absensi, settings, audit, dan aset yang tercakup.
- [x] Uji backup rusak, versi tidak kompatibel, akses ditolak, dan proses terputus.
- [x] Gerbang: data terbukti dapat dipulihkan; file backup berhasil dibuat saja belum memenuhi kelulusan.

- [x] Gerbang review pengguna Tahap 13 diterima; lanjut Tahap 14 diizinkan.

### Tahap 14 - Packaging, instalasi bersih, dan pemulihan operasional

Dependensi: Tahap13. Status28 Oktober2026: installer terbaru **0.14.1-research**, aplikasi x64 dengan PostgreSQL17.11/pgvector0.8.7 bawaan, berhasil dibangun dan diuji pada Windows11 ARM64 Parallels. Setup data kosong, model, migrasi0005, bootstrap/login, dashboard, native credential, repair ketika database hidup dan uninstall/reinstall mempertahankan data lulus. Tes terarah Windows29PASS/3SKIP dan Mac29PASS/3SKIP; bukan run regresi penuh baru. Bukti terbaru: `docs/testing/stage-14-auto-20261028.md`; uji mandiri: `docs/testing/stage-14-auto-manual.md`. Hasil paket lama dan regresi455PASS/2timeout/1SKIP tetap tercatat pada `docs/testing/stage-14.md`. Uji AMD fisik/perangkat/alur lengkap belum selesai. Pengguna mengizinkan lanjut bersyarat ke Tahap15 melalui Parallels sesuai D-29 dan mengonfirmasi dashboard setelah login.

- [x] Paket/installer Windows dengan PyQt6/plugin/runtime AI/model/resource, manifest4615file dan hash output; NotSigned, cakupan penelitian/internal.
- [x] Pisahkan bundle dari data/config/log per-user; DACL privat Windows diuji, file .env/data privat ditolak dari paket.
- [x] PostgreSQL lokal/vector, role minimal, konfigurasi privat, upgrade/seed/check aktual pada instance uji Windows.
- [x] Prosedur upgrade/migrasi eksplisit/pengaman/recovery; repair versi sama dan pemulihan transaksi diuji. Upgrade/rollback lintas rilis belum dapat diuji pada rilis Windows pertama.
- [x] Akun Windows standar baru: bootstrap/login, native credential lintas proses, runtime model/DB, ekspor/backup/restore sintetis dan uninstall/reinstall mempertahankan data. Paket terbaru mengikuti alur ganti password opsional; PATH proses tanpa Python pengembangan.
- [x] Kamera laptop/USB dan simultan melalui runtime frozen lulus setelah USB dihubungkan kembali; tanpa menyimpan gambar.
- [x] Adaptor jaringan diputus: probe worker AI dan PostgreSQL lokal PASS, jaringan dikembalikan Up.
- [ ] Uji mandiri Windows: registrasi wajah/IN-OUT, cabut USB fisik, audio, Excel/reader dan alur lengkap tanpa internet.
- [x] Izin lanjut bersyarat 28 Oktober2026: installer terbaru dipasang pada akun pengguna di Parallels, pengguna mengonfirmasi dashboard setelah login. Pengguna menerima penundaan AMD dan kamera kedua untuk mulai Tahap15; pengujian perangkat/fitur yang belum dilakukan tetap terbuka sesuai D-29.
- [x] Siapkan kode installer opsional dengan PostgreSQL17/pgvector bawaan, provisioning/config/password otomatis, migrasi/data dasar, pemeriksaan runtime dan start cluster saat aplikasi dibuka. Pengaman serta SQL/lifecycle cluster terpisah diuji di Mac; lihat `docs/windows-auto-setup.md`.
- [x] Build ulang aplikasi terbaru dengan PostgreSQL17/pgvector dan model penelitian pada Windows11 ARM64 Parallels, paket x64 versi0.14.1. Setup dari data kosong pada akun standar, model, migrasi0005, bootstrap/login, dashboard, toast dan credential native lintas proses lulus. Lock Windows diperbaiki. Bukti: `docs/testing/stage-14-auto-20261028.md`.
- [x] Perbaiki dan uji ulang repair saat database kelolaan hidup: hentikan cluster sebelum mengganti DLL, lanjutkan setup/pemeriksaan, pertahankan konfigurasi dan data.
- [x] Uninstall/reinstall installer otomatis: database dihentikan, konfigurasi tetap, 80 anggota/5 akun/2.467 catatan sintetis tetap utuh setelah pemasangan ulang.
- [ ] Uji mesin AMD customer, restart Windows, perangkat nyata dan alur offline lengkap. Panduan: `docs/testing/stage-14-auto-manual.md`. Installer lama tanpa nomor versi tetap merupakan artefak historis.

### Tahap 15 - Validasi performa, keamanan, regresi, dan UAT

Dependensi: Tahap14 dengan pengecualian D-29. Status28 Oktober2026: sedang dikerjakan. Pengujian AMD fisik/kamera kedua ditunda atas pilihan pengguna; hasil Parallels dipisahkan. Regresi akhir538PASS/1SKIP dan coverage gabungan89,73% selesai. Baseline p95 pencarian364,83ms diperbaiki menjadi50,92ms pada paket0.14.2 dengan10.000anggota/50.000vektor/1.000probe. Masih3query>100ms (maks228,82ms), sehingga PERF-B001 tetap OPEN untuk batas seluruh query. Akurasi wajah, liveness, soak dan availability belum tersertifikasi. Laporan: `docs/testing/stage-15.md`.

- [x] Petakan seluruh31 user story ke bukti otomatis dan pengujian nyata yang masih terbuka: `docs/testing/stage-15-acceptance-map.md`.
- [ ] Selesaikan seluruh acceptance criteria US-001 sampai US-031 serta kebutuhan PRD tambahan, termasuk uji nyata yang belum tersedia.
- [x] Regresi akhir sumber:538PASS/1SKIP, PostgreSQL dan model nyata, native credential,610,67detik. Coverage gabungan89,73% (7.959/8.870 statement), tanpa exclusion; Windows DACL SKIP pada Mac ditopang bukti Windows terpisah.
- [x] Ukur subset tanpa database/model secara terpisah:207PASS/1SKIP, coverage43,56%; subset masih mencakup UI/native credential dan bukan klasifikasi unit murni.
- [ ] Penuhi dan buktikan syarat unit test coverage≥80% sesuai DoD; coverage gabungan89,73% tidak menggantikannya.
- [ ] Ukur face detection <300 ms, recognition <500 ms, attendance save <200 ms, startup <5 detik.
- [x] Ukur baseline pencarian pada runtime Windows terpasang:10.000anggota/50.000embedding512D,1.000probe; p50=305,32ms,p95=364,83ms,max=957,27ms. Semua ID fiktif benar dan schema sementara dihapus; bukan ukuran akurasi wajah.
- [x] Terapkan dan verifikasi optimasi exact search di paket0.14.2: p95=50,92ms,1.000hasil sintetis benar, schema uji dibuang.
- [ ] Penuhi batas100ms pada seluruh query/query pertama (PERF-B001 masih3lonjakan) dan ukur absensi end-to-end <=2detik; startup/deteksi/recognition/save tetap terpisah.
- [ ] Ukur recognition accuracy >=98% dengan protokol yang disepakati; laporkan false accept/false reject dan kondisi pengujian.
- [ ] Ukur spoof detection >=95% dengan serangan foto/video dan kamera target; sertakan penolakan pengguna asli.
- [ ] Jalankan pengujian durasi panjang/multi-camera: memori, antrean frame, respons UI, stream putus, restart database, dan pemulihan aplikasi.
- [ ] Evaluasi availability 99,5% berdasarkan periode observasi yang disepakati; jangan menyatakannya terbukti dari smoke test singkat.
- [x] Regresi otomatis otorisasi, session, lockout, hashing password, kredensial RTSP, akses biometrik dan backup lulus pada run penuh; pemeriksaan DACL Windows dicatat terpisah.
- [ ] Perbaiki bug, ulangi kasus gagal dan regresi terkait, lalu jalankan UAT bersama pengguna.
- [ ] Gerbang: seluruh target yang diwajibkan dan DoD lulus dengan bukti; pengecualian membutuhkan keputusan terdokumentasi dan tidak boleh diberi status lulus penuh.

### Tahap 16 - Dokumentasi final dan rilis V1

Dependensi penerimaan: Tahap15. Dokumentasi dan kandidat penyerahan disiapkan paralel; gerbang V1 menunggu bukti Tahap15.

- [x] Lengkapi panduan instalasi, operasional per role, registrasi wajah, kamera/RTSP, shift, laporan, backup/restore, dan troubleshooting: `docs/operations.md`.
- [x] Perbarui arsitektur, ERD, migrasi, konfigurasi, manifest dependensi/model dan notice lisensi; penetapan lisensi kode pengguna/distribusi tetap pada pemilik.
- [ ] Lengkapi laporan UAT, pengukuran SLA, daftar bug, batasan, serta release notes.
- [x] Siapkan installer kandidat0.14.2 terverifikasi (SHA256/manifest6227berkas) dan prosedur pemulihan; bukan penerimaan V1 penuh.
- [x] Arsip kandidat `dist/releases/StarGate-Research-Windows-x64-0.14.2.zip` dibuat dan seluruh89berkas/217source diverifikasi melalui SHA256; bukti `docs/testing/evidence/stage-16-release.json`. Snapshot PLAN dalam source kit dibuat sebelum penandaan hasil arsip ini.
- [x] Tinjau Definition of Done kedua PDF dan checklist penutupan tahap: `docs/testing/stage-16.md`; persyaratan tanpa bukti tetap terbuka.
- [ ] Gerbang: pengguna menerima hasil V1; distribusi/pemasangan produksi dilakukan sebagai langkah yang disepakati secara terpisah.

## 6. Pemetaan user story ke tahap

| User story | Cakupan | Tahap utama |
|---|---|---|
| US-001, US-002 | Login dan role-based access | 4 |
| US-003, US-004 | Registrasi dan lima sudut wajah | 8 |
| US-005, US-006, US-007 | Daftar, edit, soft delete member | 5; riwayat diverifikasi 10 |
| US-008, US-009, US-010 | Check-in, anti-spoof, wajah tidak dikenal | 7, 10 |
| US-011, US-012 | Cooldown/duplikasi dan checkout | 10 |
| US-013, US-014 | Statistik dan live feed | 11 |
| US-015, US-016 | Group dan penugasan member | 5 |
| US-017, US-018 | Webcam dan RTSP | 6 |
| US-019, US-020 | Shift dan keterlambatan | 5, 10 |
| US-021, US-022, US-023, US-024 | Laporan, filter, XLSX, PDF | 12 |
| US-025, US-026 | User management dan reset password | 4 |
| US-027, US-028 | Threshold dan anti-spoof settings | 9 |
| US-029 | Audit | 3, 4, 9, 10, 13 |
| US-030, US-031 | Backup dan restore | 13 |
| Seluruh US dan DoD | Regresi, SLA, UAT, dokumentasi | 15-16 |

Kebutuhan PRD tanpa US khusus tetap wajib: remember me/change password, account lockout/session timeout, grafik dashboard, registrasi ulang, filter member, CRUD group/shift/device/user, riwayat member, break events, early leave, auto checkout opsional, multi-camera, semua filter/periode laporan, serta kebutuhan nonfungsional. Detailnya dilacak pada matriks kebutuhan Tahap 0.

## 7. Format catatan hasil pengujian tahap

Gunakan satu berkas `docs/testing/stage-NN.md` per tahap saat dikerjakan.

```text
Tahap / tanggal:
Versi kode / versi model:
OS / Python / database / perangkat / kamera:
Status: Belum dimulai | Dikerjakan | Menunggu pengujian | Perbaikan | Lulus | Terhambat
Checklist implementasi yang selesai:
ID kebutuhan / ID test:
Langkah pengujian:
Hasil yang diharapkan:
Hasil aktual:
Jenis bukti: log tersanitasi / screenshot / laporan test / hasil ekspor
Hasil: PASS | FAIL | BLOCKED | NOT RUN
Bug dan akar penyebab:
Perbaikan:
Hasil uji ulang dan regresi:
Pengujian yang masih tertunda:
Keputusan pengguna untuk lanjut / tanggal:
Langkah berikutnya:
```

## 8. Posisi pengerjaan saat ini

- [x] Kedua PDF dibaca dan kebutuhan utama diidentifikasi.
- [x] Plan bertahap dibuat.
- [x] Dokumen Tahap 0, matriks 31 US + 28 kebutuhan tambahan dan 59 kelompok test disiapkan.
- [x] Target dikonfirmasi: macOS development, Windows distribution, PostgreSQL lokal satu komputer.
- [x] Review/pengujian dokumen Tahap 0 diselesaikan dan pengguna menyetujui lanjut.
- [x] Instalasi Tahap 1 dimulai setelah persetujuan pengguna.

Fondasi UI dan persistensi database tersedia. Pengguna menyetujui Tahap 3 dan mengarahkan lanjut ke Tahap 4. Login, session, role dan user management selesai diverifikasi; Pengguna menyetujui Tahap 4 setelah uji mandiri; Tahap 5 sudah disetujui; Tahap 6 sudah direview pengguna; RTSP positif tetap tertunda. Tahap 7 menyediakan engine/alat uji; gerbang nyata awal belum lulus. Migrasi 0003_admin, 147 tes/93,23% coverage serta 21 tes GUI native lulus; demo administratif terpisah disiapkan. Bukti: `docs/testing/stage-03.md` dan `docs/testing/stage-04.md`. Dokumentasi library diperbarui melalui MCP Context7 sesuai arahan pengguna.

- [x] Pemeriksaan teknis Tahap 1 lulus: import, database/pgvector, model, Qt native/offscreen, dua webcam.
- [x] Pengguna menguji mandiri, meninjau Tahap 1 dan mengarahkan lanjut ke Tahap 2.

- [x] Fondasi Tahap 2 dan 26 pengujian otomatis lulus; smoke Qt native/offscreen lulus.
- [x] Pengguna menguji mandiri/meninjau Tahap 2 dan mengarahkan lanjut ke Tahap 3.

- [x] Tahap 3: 13 tabel aplikasi, repository/seed/bootstrap/audit, 75 tes dan uji persistensi setelah restart lulus.
- [x] Pengguna meninjau Tahap 3 dan mengarahkan lanjut ke Tahap 4, 18 Oktober 2026.

- [x] Tahap 4: autentikasi/role/Users, migrasi 0002_auth, 100 tes, Keychain lintas proses dan 10 tes GUI macOS lulus.
- [x] Pengguna menyelesaikan uji mandiri/review Tahap 4 dan mengarahkan lanjut ke Tahap 5, 18 Oktober 2026.

- [x] Perbaikan hasil uji mandiri AUTH-B004: pemeriksaan sesi tidak lagi mengganggu fokus input; 2 tes fokus native + regresi lengkap 102 PASS, coverage 91.47%. Menunggu pengguna menguji ulang Tahap 4.

- [x] Tahap 5: grup/shift/anggota/assignment/audit, migrasi 0003_admin, demo terisolasi, 147 tes dan 21 tes native lulus.
- [x] Pengguna menyelesaikan review/uji mandiri Tahap 5 dan mengarahkan lanjut ke Tahap 6.

- [x] Perbaikan uji mandiri ADM-B003: tombol Tetapkan shift/Akhiri penugasan segera mengikuti pilihan dropdown; 19 tes regresi administrasi dan 1 skenario native PASS. Review Tahap 5 kemudian disetujui pengguna.

- [x] Tahap 6: migrasi 0004_devices, CRUD perangkat, vault RTSP, capture terisolasi, 191 tes/92,37% coverage dan dua webcam 1280×720 lulus.
- [ ] Lengkapi gerbang hardware Tahap 6: RTSP nyata tetap tertunda; cabut fisik/review dikonfirmasi pengguna dan Tahap 7 diizinkan.

- [x] CAM-B003: retry otomatis webcam lokal dinonaktifkan agar index yang berubah tidak membuka kamera lain; retry RTSP dipertahankan. Regresi index remap dan UI diuji; cabut fisik perlu uji ulang pengguna.

- [x] Pengguna mengonfirmasi CAM-B003 terselesaikan setelah restart, menyetujui review Tahap 6 dan mengizinkan Tahap 7. RTSP positif tetap NOT RUN.
- [x] Pengguna menyetujui pemrosesan uji wajah Tahap 7 hanya di memori; tidak menyimpan foto/embedding nyata ke DB/berkas. Foto cetak dan replay diuji pengguna sendiri.

- [x] Tahap 7: RetinaFace, alignment/ArcFace 512D, MiniFASNet dan pencarian pgvector; alat uji sementara tanpa penyimpanan wajah, 233 tes/91,14% coverage dan 7 tes native PASS.
- [x] Review Tahap 7 disetujui pengguna setelah panduan uji dan Tahap 8 diizinkan. Rincian jumlah/skor per kondisi tidak dikirim; target statistik Tahap 15 tetap belum terbukti.

- [x] Pengguna menyetujui review Tahap 7 dan mengizinkan Tahap 8; izin penyimpanan nyata dan kebijakan ganti embedding lama diberikan terpisah.
- [x] Retensi biometrik dipilih berdasarkan mandat pengguna dan sumber resmi: aktif selama diperlukan; nonaktif hapus biometrik, histori dipisah. Dasar dan batas di `docs/biometric-retention.md`.
- [x] Review Tahap 8 disetujui pengguna dan Tahap 9 diizinkan; rincian uji nyata tidak dikirim, tidak diklaim sebagai metrik statistik.

- [x] Tahap 8: registrasi lima sudut/registrasi ulang, penyimpanan atomik dan rollback, uji gallery setelah restart, retensi biometrik; 260 tes/90,17% coverage dan 28 tes native PASS. Review pengguna kemudian disetujui; rincian hasil nyata tidak dilaporkan.

- [x] Tahap 9: delapan pengaturan tersimpan, snapshot engine/probe, audit batch/konflik dan liveness; 284 regresi/90,37% coverage serta 37 tes native PASS. Perbaikan timer join Qt dan prasyarat aktivasi jendela diuji. Review Tahap 9 kemudian disetujui pengguna dan Tahap 10 diizinkan.

- [x] Tahap 10: absensi wajah, mode/state, cooldown lintas kamera, shift/grace/early leave, auto checkout, fresh policy/probe dan notifikasi pascacommit; 334 tes/89,90% coverage, 47 native PASS pada verifikasi awal. Perbaikan tombol dan demo diuji tambahan. Review pengguna diterima 20 Oktober 2026; rincian percobaan fisik tidak dilaporkan.
- [x] Tahap 11: Dashboard orang unik, feed otomatis, grafik, filter tanggal kerja/shift malam dan demo lima anggota; 371 tes/89,59% coverage serta 59 native PASS. Review pengguna disetujui 20 Oktober 2026, lanjut Tahap 12 diizinkan.
- [x] Tahap 12: laporan/filter, snapshot semua halaman, XLSX/PDF, worker/cancel/atomic publication dan demo Viewer 65 baris; 399 regresi PASS (coverage run 90,11%), 13 tes ekspor final dan 65 native PASS. Review pengguna diterima 20 Oktober 2026; lanjut Tahap 13 diizinkan.

- [x] Tahap 13: inspeksi/filter audit SA/Admin; backup AES-GCM/Scrypt, retensi 7 hari dan restore SuperAdmin dengan pengaman/lock/transaksi. Seluruh biometrik/sesi dilewati sesuai persetujuan pengguna, akun/riwayat/settings/audit pulih. 442 regresi PASS/90,64% coverage, 69 native PASS; demo terpisah tersedia. Review pengguna diterima 20 Oktober 2026; lanjut Tahap 14 diizinkan.

- [x] Tahap14: installer Windows x64 dibangun/dipasang; akun standar/ACL, native credential, model, DB, kedua kamera, ekspor/backup/restore sintetis, probe offline dan repair/uninstall/reinstall PASS. Bukti dan kegagalan/recheck dicatat di docs/testing/stage-14.md. Pengguna kemudian mengonfirmasi dashboard Parallels dan mengizinkan Tahap15 bersyarat sesuai D-29; UAT/perangkat yang belum diuji tetap terbuka.


Pembaruan28 Oktober2026: paket0.14.2 dipasang pada akun pengguna Parallels; model/schema0006 lulus, baseline80anggota/4akun/2.467kehadiran masih ada. Pencarian p95=50,92ms tetapi3/1.000query>100ms, sehingga PERF-B001 masih OPEN. Kamera0 gagal pertama lalu preview/reopen ulang lulus; CAM-B004 masih OPEN untuk isolasi penyebab. Dokumentasi operasi/arsitektur/ERD/notice/DoD dan daftar gerbang tersisa disiapkan. Bukti: `docs/testing/stage-15.md`, `docs/testing/stage-16.md`, `docs/testing/remaining-acceptance.md`. Tidak ada penerimaan V1 penuh.
