# Matriks kebutuhan dan pengujian StarGate

Tanggal: 18 Oktober 2026. Status: pembangunan bertahap; Tahap 0–7 direview pengguna pada cakupan tersedia; RTSP positif tetap tertunda, Tahap 8 aktif.

Sumber: PRD = `StarGate - Face Recognition Attendance System.pdf`; US = `StarGate - User Stories dan Acceptance Criteria.pdf`. Nomor halaman di tabel adalah halaman PDF sumber, dimulai dari 1.

Setiap baris mempunyai ID test yang sama dengan akhiran ID kebutuhan. Status mengikuti tiap baris; SCHEMA/QUERY sudah diuji pada Tahap 3, AUTH/ROLE/USER serta US-001/002/025/026 diverifikasi pada Tahap 4; AC tahap lain tetap **NOT RUN**. Skenario bersyarat keputusan belum boleh dianggap final. Detail langkah dan hasil dicatat saat tahap terkait dijalankan.

## User stories

Pembaruan28 Oktober2026: [peta penerimaan Tahap15](testing/stage-15-acceptance-map.md) menghubungkan seluruh31user story dengan run regresi terbaru dan pengujian nyata yang masih terbuka. Status historis setiap tahap di bawah tetap dibedakan dari UAT Windows/AMD penuh.

| ID | Halaman US | Tahap | Hasil wajib / acceptance criteria | ID test | Keputusan | Status |
|---|---|---|---|---|---|---|
| US-001 | 1 | 4 | Login benar membuka Dashboard dan membuat session; password salah menampilkan error dan ditolak | TC-US-001 | D-16 | PASS |
| US-002 | 1-2 | 4 | Viewer ditolak pada Users/Settings dan diizinkan Reports | TC-US-002 | D-09,D-10 | PASS |
| US-003 | 2 | 8 | Field wajib lengkap + capture berhasil menyimpan member dan embedding; nama kosong disable Save; tanpa wajah tidak lanjut | TC-US-003 | D-14 | PARTIAL: alur/atomisitas/izin PASS sintetis; capture nyata menunggu uji mandiri |
| US-004 | 2 | 8 | Capture depan/kiri/kanan/atas/bawah dengan minimal 5 sampel tersimpan | TC-US-004 | D-14,D-23 | PARTIAL: lima pose/duplikat/guard identitas PASS terkendali; pose nyata belum diterima |
| US-005 | 3 | 5 | Daftar member tampil dengan pagination dan pencarian | TC-US-005 | — | PASS |
| US-006 | 3 | 5 | Edit member lalu Save tersimpan | TC-US-006 | D-14 | PASS |
| US-007 | 3 | 5/10 | Delete meminta konfirmasi, menonaktifkan member dan mempertahankan attendance | TC-US-007 | D-14 | NOT RUN |
| US-008 | 3-4 | 10 | Wajah dikenal + liveness valid menyimpan attendance, suara dan notifikasi sukses | TC-US-008 | D-07,D-08 | PASS teknis; UAT kamera/audio tertunda |
| US-009 | 4 | 7/10 | Foto palsu dan replay video ditolak untuk attendance | TC-US-009 | D-05,D-19 | PARTIAL: gate liveness PASS; serangan nyata tertunda |
| US-010 | 4 | 10 | Wajah tidak terdaftar tidak disimpan dan muncul Face Not Recognized | TC-US-010 | D-19 | PASS teknis; UAT kamera/audio tertunda |
| US-011 | 4 | 10 | Absensi ulang dalam 60 detik ditolak | TC-US-011 | D-07 | PASS teknis; UAT kamera/audio tertunda |
| US-012 | 5 | 10 | Scan kembali setelah check-in menghasilkan check-out dan menyimpan jamnya | TC-US-012 | D-07,D-08 | PASS teknis; UAT kamera/audio tertunda |
| US-013 | 5 | 11 | Dashboard menampilkan Present, Absent, Late | TC-US-013 | D-10,D-13 | PASS teknis; review pengguna tertunda |
| US-014 | 5 | 11 | Attendance tersimpan memperbarui dashboard otomatis tanpa refresh manual | TC-US-014 | D-03 | PASS teknis lintas penulis/terminal database sama; review pengguna tertunda |
| US-015 | 5 | 5 | Group baru tersimpan | TC-US-015 | D-10,D-14 | PASS |
| US-016 | 6 | 5 | Relasi member-group tersimpan | TC-US-016 | D-14 | PASS |
| US-017 | 6 | 6 | Webcam yang ditambahkan muncul di daftar device | TC-US-017 | D-02 | PASS: CRUD/UI dan dua webcam; lihat Tahap 6 |
| US-018 | 6 | 6 | RTSP valid menampilkan preview; invalid menampilkan error | TC-US-018 | D-02,D-17 | PARTIAL: error/secret/retry PASS; RTSP positif nyata NOT RUN |
| US-019 | 6 | 5 | Shift valid berhasil dibuat | TC-US-019 | D-11,D-12 | PASS |
| US-020 | 6-7 | 10 | Shift 08:00 + grace 10: 08:05 Present dan 08:11 Late | TC-US-020 | D-11,D-12 | PASS teknis; UAT kamera/audio tertunda |
| US-021 | 7 | 12 | Filter tanggal menampilkan laporan harian | TC-US-021 | D-11,D-15 | PASS teknis; review pengguna diterima 20 Oktober 2026 |
| US-022 | 7 | 12 | Filter group menampilkan hanya data group tersebut | TC-US-022 | D-15 | PASS teknis, termasuk grup historis; review pengguna diterima 20 Oktober 2026 |
| US-023 | 7 | 12 | File XLSX terbentuk dan seluruh data sesuai hasil laporan | TC-US-023 | D-15 | PASS teknis semua halaman/snapshot/Viewer; review pengguna diterima 20 Oktober 2026 |
| US-024 | 7 | 12 | File PDF laporan berhasil dibuat | TC-US-024 | D-15 | PASS teknis/multipage/Unicode dan render macOS; Windows terpisah |
| US-025 | 8 | 4 | Form user valid membuat akun | TC-US-025 | D-09,D-16 | PASS |
| US-026 | 8 | 4 | Reset membuat password baru dan user dapat login dengannya | TC-US-026 | D-09,D-16 | PASS |
| US-027 | 8 | 9 | Threshold 0.65 tersimpan dan dipakai engine | TC-US-027 | D-19 | PASS teknis Tahap 9 |
| US-028 | 8 | 9/10 | Mengaktifkan anti-spoof mewajibkan liveness untuk setiap attendance | TC-US-028 | D-19 | PASS teknis attendance/policy; UAT tertunda |
| US-029 | 8-9 | 3/4/9/10/13 | Login, member delete, settings change dicatat; auditor dapat memeriksa | TC-US-029 | D-10,D-17 | PASS teknis: inspeksi/filter SA/Admin dan audit lintas fitur; review Tahap 13 diterima |
| US-030 | 9 | 13 | Tombol Backup menghasilkan file backup database | TC-US-030 | D-18 | PASS teknis: cadangan terenkripsi/role/aset/error; review Tahap 13 diterima |
| US-031 | 9 | 13 | File backup valid memulihkan database | TC-US-031 | D-18 | PASS teknis: restore terisolasi/rollback/crash; biometrik sengaja dilewati sesuai persetujuan; review Tahap 13 diterima |

## Kebutuhan tambahan PRD dan DoD

| ID | Halaman PRD kecuali disebut | Tahap | Kebutuhan | ID test | Keputusan | Status |
|---|---|---|---|---|---|---|
| PRD-AUTH | 3-4,11 | 4 | Remember me, change password, timeout, lockout, bcrypt | TC-PRD-AUTH | D-16 | PASS |
| PRD-ROLE | 10 | 4 | Matriks izin lima fitur dan empat role | TC-PRD-ROLE | D-09,D-10 | PASS |
| PRD-DASH | 4 | 11 | Total registered, On Leave, grafik per shift/group dan tren harian/bulanan | TC-PRD-DASH | D-13 | NOT RUN |
| PRD-MEMBER | 4-5 | 5/8/10 | ID/nama/group/photo wajib; email/phone/position opsional; filter nama/group/aktif; history; re-register | TC-PRD-MEMBER | D-14 | NOT RUN |
| PRD-GROUP | 6 | 5 | Create/edit/delete group; multi-group organisasi | TC-PRD-GROUP | D-14 | PASS |
| PRD-DEVICE | 6-7 | 6 | Internal/USB/RTSP, nama/tipe/URL/resolusi/FPS, preview, multi-camera | TC-PRD-DEVICE | D-02,D-23 | NOT RUN |
| PRD-EVENT | 7-8 | 10 | IN, OUT, BREAK_OUT, BREAK_IN, cooldown, duplicate, feedback | TC-PRD-EVENT | D-07,D-08 | NOT RUN |
| PRD-SHIFT | 8 | 5/10 | Grace, late, early leave; shift 08-17 dan 20-04 | TC-PRD-SHIFT | D-11,D-12 | NOT RUN |
| PRD-REPORT | 9 | 12 | Daily/weekly/monthly/custom; date from/to/group/member/shift/status | TC-PRD-REPORT | D-15 | NOT RUN |
| PRD-USER | 10 | 4 | User CRUD; username/full name/role/password wajib | TC-PRD-USER | D-09,D-16 | PASS |
| PRD-CONFIG | 10 | 9 | Default .60, Auto, 3s; anti-spoof on/.85; window 60s, start Shift, auto checkout opsional | TC-PRD-CONFIG | D-19 | PASS teknis konfigurasi dan aturan attendance |
| PRD-SCHEMA | 12-13 | 3 | Delapan tabel dan seluruh kolom yang tercantum di PDF | TC-PRD-SCHEMA | D-11,D-13,D-14 | PASS |
| PRD-ARCH | 13-15 | 2/3/7 | Layer/struktur folder; PyQt6/RetinaFace/ArcFace/MiniFASNet/ORM/PostgreSQL/pgvector | TC-PRD-ARCH | D-01,D-05 | NOT RUN |
| PRD-AUDIT | 11 | 3/4/9/10/13 | Login, Attendance, User Create/Delete, Settings Change | TC-PRD-AUDIT | D-17 | NOT RUN |
| PRD-QUERY | 11 | 3 | SQLAlchemy ORM; query terparameterisasi; no raw SQL aplikasi | TC-PRD-QUERY | D-06 | PASS |
| PRD-LOCATION | 1,15-16 | 3/6/15 | Tujuan multi-lokasi, tanpa cloud sync V1 | TC-PRD-LOCATION | D-03,D-22 | NOT RUN |
| PRD-OVERTIME | 2,15 | 5/10/12 | Kebutuhan lembur disebut; payroll V2 | TC-PRD-OVERTIME | D-22 | NOT RUN |
| PRD-DETECT | 11 | 7/15 | Face detection <300 ms | TC-PRD-DETECT | D-20 | NOT RUN |
| PRD-RECOGNIZE | 11 | 7/15 | Recognition <500 ms | TC-PRD-RECOGNIZE | D-20 | NOT RUN |
| PRD-SAVE | 11 | 10/15 | Attendance save <200 ms | TC-PRD-SAVE | D-20 | NOT RUN |
| PRD-STARTUP | 11 | 14/15 | Startup <5 detik | TC-PRD-STARTUP | D-20 | NOT RUN |
| PRD-SPEED | 1,15 | 15 | Absensi <2s di ringkasan dan <=2s di MVP | TC-PRD-SPEED | D-20,D-21 | NOT RUN |
| PRD-ACCURACY | 1,15 | 15 | Recognition >98% di ringkasan dan >=98% di MVP | TC-PRD-ACCURACY | D-20,D-21 | NOT RUN |
| PRD-LIVENESS | 15 | 7/15 | Spoof detection >=95% | TC-PRD-LIVENESS | D-05,D-20 | NOT RUN |
| PRD-SEARCH | 15 | 3/7/15 | Search <=100 ms untuk 10.000 member | TC-PRD-SEARCH | D-14,D-20 | Belum memenuhi target pada Parallels:10.000anggota/50.000vektor,1.000probe,p95=364,83ms; PERF-B001 OPEN. AMD belum diuji; lihat Tahap15 |
| PRD-AVAILABILITY | 11 | 15 | Availability 99.5% | TC-PRD-AVAILABILITY | D-20 | NOT RUN |
| PRD-DONE | US h.9-10 | 15/16 | US/AC selesai; coverage >=80%; integration lulus; bug/audit/akses/docs/SLA/UAT | TC-PRD-DONE | D-20 | NOT RUN |
| PRD-SCOPE | 3,15-16 | 0/16 | V1 tanpa mobile/SaaS/GPS/payroll/mask/visitor; roadmap V2 terpisah | TC-PRD-SCOPE | D-01,D-22 | NOT RUN |

## Aturan keterlacakan

- Penambahan kebutuhan mendapatkan ID baru, sumber/keputusan dan test terkait.
- PASS hanya diberikan dengan bukti aktual, tidak disimpulkan dari keberadaan kode.
- Pengujian hardware/DB/model belum tersedia diberi BLOCKED atau NOT RUN, bukan digantikan mock tanpa label.
- Data schema PRD diperiksa kolom demi kolom pada Tahap 3; tabel tambahan hanya untuk kebutuhan yang terdokumentasi.

Bukti Tahap 3: schema/ORM-query groups diverifikasi pada [laporan database](testing/stage-03.md).

Bukti Tahap 4: [laporan autentikasi dan matriks akses](testing/stage-04.md). PASS teknis tidak menggantikan gerbang review pengguna. US-029/PRD-AUDIT masih NOT RUN penuh: audit login/user sudah PASS, tetapi audit keseluruhan dan layar inspeksi tetap tahap berikutnya. Viewer mendarat di Reports sesuai baseline, bukan Dashboard.

Bukti Tahap 5: [laporan administrasi](testing/stage-05.md). US-007/PRD-MEMBER/PRD-SHIFT masih belum PASS penuh: soft delete/riwayat tersimpan dan jadwal administratif diuji Tahap 5; registrasi wajah serta pengenalan/nonaktif/early leave end-to-end tetap Tahap 8/10.

Bukti Tahap 6: [laporan perangkat/kamera](testing/stage-06.md). 191 tes otomatis lulus; webcam nyata dan error RTSP localhost diverifikasi. Gerbang hardware penuh belum lulus karena sumber RTSP positif belum tersedia; uji cabut USB dan review dikonfirmasi pengguna setelah CAM-B003.

Bukti Tahap 7: [engine AI dan alat uji](testing/stage-07.md). Adapter/model, pipeline pada fixture publik dan pencarian numerik PostgreSQL sudah diuji; wajah asli layak/foto cetak/replay melalui kamera belum diterima. US-009/PRD-LIVENESS/PRD-ACCURACY tetap NOT RUN penuh. Tidak menyimpulkan SLA/akurasi produksi dari repeat embedding gambar yang sama.

Bukti Tahap 8: [registrasi wajah](testing/stage-08.md) dan [kebijakan retensi](biometric-retention.md). Simpan/registrasi ulang/rollback/retensi/izin diuji dengan PostgreSQL nyata dan data sintetis. Probe sintetis setelah restart membaca gallery tanpa menambah embedding/attendance. Lima sudut wajah nyata dan kecocokan setelah restart tetap menunggu pengujian pengguna, bukan PASS dari counter buatan.

Bukti Tahap 9: [pengaturan dan snapshot engine](testing/stage-09.md). Ambang 0,65 diterapkan pada query pgvector nyata dengan probe sintetis 0,625; konfigurasi .60 menerima sedangkan .65 menolak. Liveness engine mengikuti konfigurasi dan menolak embedding saat gagal. US-028 tidak dinyatakan PASS untuk setiap attendance sebelum pipeline Tahap 10 tersedia. Perubahan settings/audit atomik, konflik perubahan dan role diuji; UI inspeksi audit tetap Tahap 13.

Bukti Tahap 10: [absensi dan shift](testing/stage-10.md). Pipeline sintetis kamera/inference → pgvector → transaksi → feedback diuji; suara diminta setelah row committed. Jeda lintas terminal, state/break, grace, early leave, shift malam, auto checkout, perubahan policy, expiry selama DB, replay dan penutupan sumber daya diuji. Uji model worker nyata memakai frame tanpa wajah; tidak menggantikan absensi fisik/serangan cetak/replay/speaker, RTSP dan Windows. Dashboard real-time dan inspeksi audit tetap tahap berikutnya.

Bukti Tahap 11: [Dashboard dan monitoring](testing/stage-11.md), 371 tes/89,59% coverage dan 59 native PASS. Statistik memakai orang unik dari IN, Terlambat termasuk Hadir, Absent pada akhir shift dan Izin dari sumber jadwal/izin. Feed dari commit terminal lain diperbarui tanpa refresh. Tanggal kerja/shift malam, tren harian/bulanan, grup historis, filter/fokus, sumber gagal, revoke dan lifecycle diuji; render grafik/native ditinjau. Review Tahap 10 diterima pengguna; jumlah percobaan fisik tambahan tidak dilaporkan. Tahap 12 belum dimulai.

Bukti Tahap 12: [laporan dan ekspor](testing/stage-12.md), 399 regresi PASS (coverage run 90,11% sebelum perapian visual), 13 ekspor final dan 65 native PASS. Snapshot per anggota/shift/tanggal diekspor seluruh halaman, termasuk dari halaman kedua demo Viewer 65 baris. Grup historis, inactive, malam, filter/status, no data, typed dates/teks literal, Unicode/nama panjang, PDF multipage/header/footer/ID utuh, pembatalan/error/revoke dan atomic publication diuji. File XLSX dibuka/dirender dan PDF final dirender/diperiksa. Review Tahap 12 diterima 20 Oktober 2026; lanjut Tahap 13 diizinkan.

Bukti Tahap 13: [audit dan pemulihan](testing/stage-13.md). 442 regresi PASS/90,64% coverage dan 69 native PASS. Perbandingan tabel/aset, kebijakan reenroll/sesi, pengaman, file rusak/versi/expired/role, transaksi gagal, cancel, crash proses dan penulis bersamaan diuji pada schema test terpisah. Tidak ada restore database kerja. Retensi 7 hari dan registrasi ulang disetujui pengguna; review hasil Tahap13 diterima; persiapan Windows Tahap14 berikutnya.
