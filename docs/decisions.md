# Keputusan kebutuhan dan arsitektur StarGate

Diperbarui: 20 Oktober 2026. Tahap 0–13 direview/disetujui pengguna pada cakupan tersedia; RTSP positif tetap tertunda. Tahap 14 persiapan distribusi Windows/Parallels dikerjakan; rincian jumlah percobaan fisik tidak disimpulkan dari persetujuan review.

Pengguna menyatakan “sudah saya review dan sudah OK, bisa dilanjutkan”. Seluruh usulan terdefinisi diterima sebagai baseline. Rincian yang belum berisi nilai, hardware Windows, retensi, dan hasil validasi tetap harus diselesaikan pada batas tahap masing-masing; persetujuan tidak berarti pengujian sudah lulus.

## Aturan status

- **Tetap dari PDF**: ketentuan eksplisit; bukan perubahan scope.
- **Usulan**: detail implementasi untuk mengisi kekosongan; belum keputusan pengguna.
- **Menunggu jawaban**: informasi kebutuhan yang tidak dapat ditentukan dari proyek.
- Keputusan final mencatat tanggal, pemberi keputusan, alasan, dan test terdampak. Jangan mengubah usulan menjadi final tanpa bukti.

Tambahan implementasi Tahap 11 (20 Oktober 2026): tanggal dashboard mengikuti work_date; pilih tanggal awal untuk shift malam. Penugasan tidak memiliki location_id, sehingga jadwal/Absent pada deployment satu lokasi memakai zona organisasi dan kalender LOCAL. Hadir historis tetap dari IN meskipun anggota kemudian nonaktif; total anggota aktif adalah kondisi sekarang. Grafik bulanan memakai hari-kehadiran, ringkasan/harian orang unik; grup mengikuti group_id saat IN. Polling 2 detik hanya saat terlihat, tanpa memperpanjang sesi. Ini rincian implementasi D-11/D-13, bukan penambahan deployment multi-lokasi atau klaim latensi produksi. Bukti: testing/stage-11.md, tests/test_dashboard.py dan tests/test_dashboard_ui.py.

## Daftar keputusan

| ID | Topik dan dasar | Usulan / ketentuan | Status | Batas penyelesaian |
|---|---|---|---|---|
| D-01 | Stack utama, PRD h.1, 13-14 | Python + PyQt6 + RetinaFace + InsightFace/ArcFace + MiniFASNet + PostgreSQL/pgvector + SQLAlchemy; bcrypt, Pandas/OpenPyXL/ReportLab. Tidak mengganti PyQt6 dengan PySide6. | Tetap dari PDF | Sekarang |
| D-02 | OS dan hardware | Pengguna menetapkan macOS untuk pengembangan dan Windows untuk distribusi pada 18 Oktober 2026. Host teramati Darwin arm64. Hardware Windows, webcam dan RTSP belum terinventarisasi; uji distribusi tetap wajib di Windows. | OS disetujui; inventaris pending | Sebelum Tahap 1 |
| D-03 | Topologi database | Pengguna menetapkan PostgreSQL lokal untuk satu komputer dahulu pada 18 Oktober 2026. Usulan perilaku jika DB gagal: hentikan penyimpanan, tampilkan error, jangan memberi feedback sukses; tidak menambah sinkronisasi offline. | Topologi disetujui; perilaku gagal usulan | Sebelum Tahap 1 |
| D-04 | Versi dan alat pendukung | Kandidat Python 3.11, OpenCV, NumPy, ONNX Runtime bila format model sesuai, psycopg, Alembic, pytest/pytest-cov, PyInstaller. Python sistem teramati 3.14.8; jangan menganggap kompatibel dengan semua model. Verifikasi resolusi dependensi pada Tahap 1 dan kunci versi setelah smoke test. | Usulan | Baseline sebelum Tahap 1; lock setelah uji instalasi |
| D-05 | Model AI | Tentukan file detector/recognizer/liveness, provenance, dimensi, preprocessing, provider CPU/GPU, checksum dan lisensi. RetinaFace wajib dipertahankan; jangan otomatis memakai paket detektor lain sebagai penggantinya. Daftar model nyata belum disiapkan. | Menunggu pemilihan teknis | Sebelum instalasi model Tahap 1 |
| D-06 | ORM vs pemasangan ekstensi, PRD h.11 | Query data memakai SQLAlchemy dan parameter; DDL pgvector hanya dalam provisioning/migrasi oleh akun terpisah. Tetap tanpa raw SQL di layanan aplikasi. | Usulan, didukung dokumentasi | Sebelum Tahap 3 |
| D-07 | Cooldown vs checkout, PRD h.8; US-011/012 | Cooldown per member berlaku lintas kamera: selisih <60 detik ditolak; tepat 60 detik lolos cooldown, tetapi tetap harus lolos state validation. Mode AUTO: scan pertama IN, scan sah berikutnya OUT; mode IN eksplisit menolak IN kedua. Ini rekonsiliasi yang diusulkan, bukan aturan final PDF. | Usulan, konflik tercatat | Sebelum Tahap 10 |
| D-08 | Event break, PRD h.7 | Pilih mode terminal AUTO/IN/OUT/BREAK_OUT/BREAK_IN. Usulan transisi IN -> BREAK_OUT -> BREAK_IN -> OUT; juga IN -> OUT. Setelah OUT, AUTO menolak scan sampai sesi shift berikutnya. Ketentuan early arrival dan sesi tambahan harus diputuskan sebelum implementasi. | Usulan | Sebelum Tahap 10 |
| D-09 | Hak akses Users, PRD h.10; US-025/026 | Ikuti matriks terperinci: hanya Super Admin mengelola Users. Kata admin dalam US-025/026 ditafsirkan Super Admin bila usulan diterima. Alternatif: revisi matriks secara eksplisit. | Usulan, konflik tercatat | Sebelum Tahap 4 |
| D-10 | Operator, Supervisor, Auditor | Operator mendapat Members/Attendance/Reports sesuai matriks PRD. Supervisor dan Auditor dipetakan ke role yang sudah ada; tidak membuat role baru otomatis. Usulan dashboard untuk Super Admin/Admin/Operator; audit viewer untuk Super Admin/Admin; persona dan izin detail perlu disepakati. Viewer hanya Reports. | Usulan | Sebelum Tahap 4 |
| D-11 | Penugasan dan tanggal shift | Tambah relasi penugasan member-shift dengan tanggal berlaku. Sesi shift malam 20:00-04:00 memiliki tanggal kerja saat mulai; simpan waktu absolut dan tampilkan zona organisasi. Default zona usulan Asia/Jakarta, dapat dikonfigurasi. | Usulan, tambahan skema untuk memenuhi fitur | Sebelum Tahap 3/5 |
| D-12 | Late, early leave, auto checkout | Tepat start + grace masih Present, setelahnya Late. Early leave jika OUT sebelum jam selesai; tidak menghapus status keterlambatan. Auto checkout default off karena opsional; bila aktif, event ditandai otomatis dan tidak menggantikan OUT manual. Definisi lembur belum ada; jangan menambah payroll. | Usulan | Sebelum Tahap 5/10 |
| D-13 | Absent dan On Leave | Pengguna menyetujui pada 20 Oktober 2026: Hadir = orang unik sudah IN, Terlambat bagian dari Hadir; anggota aktif terjadwal tanpa IN dihitung Belum masuk sebelum akhir shift, Absent mulai tepat akhir shift, Izin dari catatan izin. Kalender nonkerja mengecualikan jadwal. | Disetujui pengguna | Tahap 11 |
| D-14 | Member/group dan re-register | member_code dan username unik; soft delete member; group yang direferensikan tidak dihapus paksa. Minimal 5 sampel, mencakup seluruh sudut. Simpan satu embedding per sampel; re-register mengganti set aktif hanya setelah set baru lengkap. Penghapusan data biometrik mengikuti kebijakan retensi terpisah. | Usulan; soft delete sesuai US-007 | Sebelum Tahap 3/5/8 |
| D-15 | Laporan dan pagination | Pengguna menyetujui 20 Oktober 2026: satu baris per anggota/shift/tanggal kerja, jam masuk/keluar/istirahat, status dan pulang awal; ekspor seluruh hasil filter. XLSX ringkasan+detail event dan PDF ringkasan memakai snapshot hasil yang dimuat, metadata periode/zona/filter/waktu. | Disetujui pengguna; implementasi mengikuti format ini | Tahap 12 |
| D-16 | Session dan akun | Usulan idle timeout 15 menit, lockout 5 login gagal selama 15 menit, remember me memakai token acak yang disimpan aman dan dapat dicabut, bukan password. Reset menghasilkan password baru yang ditampilkan sekali; penggantian password opsional sesuai revisi pengguna 21 Oktober 2026. Bootstrap interaktif tanpa password bawaan. Nilai ini bukan dari PDF. | Usulan | Sebelum Tahap 4 |
| D-17 | Penyimpanan sensitif dan retensi | Jangan menaruh kredensial/foto/embedding di Git/log. Pilih penyimpanan rahasia OS untuk token/kredensial; akun DB minimal. Durasi retensi dan prosedur penghapusan harus diputuskan pemilik produk sebelum data nyata dipakai; usulan sampel uji sementara dihapus setelah evaluasi disepakati. | Diputuskan pada Tahap 8 atas mandat pengguna; lihat biometric-retention.md | Retensi biometrik diterapkan Tahap 8; backup Tahap 13 |
| D-18 | Backup/restore | Pengguna menyetujui 20 Oktober 2026: retensi 7 hari, enkripsi/password tersendiri, seluruh biometrik dilewati saat restore dan anggota registrasi ulang. Bundel data logis bertipe (bukan dump SQL), foto kelolaan, settings nonrahasia, versi/checksum; sumber RTSP/rahasia diprovisikan ulang. Restore SuperAdmin memakai owner helper, pengaman dan transaksi/lock; sesi dihapus. Audit SA/Admin. Detail/batas: testing/stage-13.md. | Retensi/reenroll disetujui pengguna; implementasi teknis Tahap 13 | 13 |
| D-19 | Similarity dan anti-spoof | Default PDF dipertahankan: similarity .60, timeout 3s, face size Auto, anti-spoof on/.85, duplicate 60s, check-in berdasarkan shift. Usulan cosine similarity = 1 - cosine_distance; skor liveness mengikuti arti output model (bukan menganggap kelas spoof sebagai live). Rentang konfigurasi divalidasi. | Default tetap; interpretasi usulan | Sebelum Tahap 7/9 |
| D-20 | Pengukuran dan DoD | Protokol usulan pada testing/acceptance-strategy.md. Semua AC harus PASS, coverage >=80%, integration lulus, audit/akses aktif, dokumentasi/SLA/UAT lengkap. Usulan arti Critical/Open: tidak ada Critical terbuka dan tidak ada defect AC terbuka; bug minor di luar AC dicatat dan ditinjau. | Usulan; frasa DoD ambigu | Sebelum pengujian fitur dan Tahap 15 |
| D-21 | Target berbeda di PRD | Ringkasan h.1 menyebut speed <2s dan accuracy >98%, MVP h.15 menyebut <=2s dan >=98%. Usulan pakai batas yang lebih ketat untuk penerimaan, sambil melaporkan keduanya; tidak menurunkan target secara diam-diam. | Usulan, konflik batas tercatat | Sebelum Tahap 15 |
| D-22 | Multi-lokasi dan lembur | Keduanya disebut sebagai tujuan/kebutuhan, tetapi tanpa alur/schema rinci; cloud sync dan payroll adalah V2. Usulan V1 terminal berlabel lokasi pada jaringan DB yang disepakati; detail isolasi lokasi dan rekap durasi tambahan perlu disepakati, tanpa menambah cloud/payroll. | Usulan, cakupan belum rinci | Sebelum Tahap 3 |
| D-23 | Multi-face dan kegagalan model | Usulan registrasi hanya satu wajah; absensi hanya memproses satu target yang dipilih deterministik per kamera, target lain menunggu. Bila model hilang atau liveness gagal saat aktif, absensi ditolak, tanpa bypass diam-diam. | Usulan | Sebelum Tahap 6/7 |

## Matriks izin yang terbaca pada tabel PRD halaman 10

| Feature | Super Admin | Admin | Operator | Viewer |
|---|---|---|---|---|
| Members | Ya | Ya | Ya | Tidak |
| Attendance | Ya | Ya | Ya | Tidak |
| Reports | Ya | Ya | Ya | Ya |
| Settings | Ya | Ya | Tidak | Tidak |
| Users | Ya | Tidak | Tidak | Tidak |

Izin group/shift/devices/audit/backup belum seluruhnya ada di tabel; usulan admin management untuk group/shift/devices, Super Admin untuk backup/restore. Setiap izin aksi perlu diturunkan pada Tahap 4, sebelum menu terkait diaktifkan.

## Dokumentasi teknis yang diverifikasi melalui MCP Context7

Pada 18 Oktober 2026, resolve `pgvector` memilih `/pgvector/pgvector-python` (repo pengelola resmi). Query memverifikasi dukungan SQLAlchemy `VECTOR(dim)` dan `cosine_distance`, serta kebutuhan provisioning `CREATE EXTENSION vector` sebelum kolom vektor digunakan. Dimensi StarGate tetap 512. Ini mendukung D-06/D-19, tidak membuktikan extension sudah terpasang atau benchmark telah lulus.

Sumber: [pgvector-python README](https://github.com/pgvector/pgvector-python/blob/master/README.md), [SQLAlchemy API](https://github.com/pgvector/pgvector-python/blob/master/_autodocs/api-reference/pgvector.sqlalchemy.md).

## Catatan persetujuan

D-02 (OS) dan D-03 (topologi lokal satu komputer) disetujui melalui jawaban langsung pengguna pada 18 Oktober 2026. Pengguna kemudian menyetujui review Tahap 0 dan memberi instruksi lanjut pada tanggal yang sama. Label Usulan pada tabel mempertahankan asal keputusan; usulan yang sudah terdefinisi kini diterima sebagai baseline, sedangkan nilai/detail yang belum ditentukan tetap pending sampai tahap terkait. Perangkat yang dinyatakan tersedia: webcam bawaan dan USB; RTSP belum dinyatakan tersedia.

## Realisasi teknis Tahap 1

- Python 3.11.17, PostgreSQL 17.11, pgvector server 0.8.7 dipasang melalui Homebrew. Dependency resolution dan smoke test menentukan lock Python akhir.
- Cluster proyek di `.local/postgres`, localhost:55432, local peer/host SCRAM. Akun aplikasi dan migrator dipisah; tidak memakai service default Homebrew.
- RetinaFace: Caffe `Widerface-RetinaFace.caffemodel` + `deploy.prototxt` dari upstream MiniVision, OpenCV DNN CPU.
- ArcFace: `w600k_r50.onnx` dari rilis InsightFace v0.7 buffalo_l; SCRFD tidak diekstrak/dimuat. Alignment pendukung `2d106det.onnx` dari paket yang sama. Model zoo dipanggil langsung dengan provider CPU.
- Liveness: MiniFASNetV2 `2.7_80x80_MiniFASNetV2.pth`, definisi upstream dipin commit `b6d5f04ad78778917853b25c778acef6d5626d15`; conv6_kernel 5x5 untuk input 80x80.
- Provenance dan hash di `models/manifest.json`; bobot lokal diabaikan Git. Hash dicatat dari download HTTPS awal, bukan tanda tangan publisher. Pretrained InsightFace hanya untuk evaluasi penelitian nonkomersial sampai izin distribusi model diselesaikan sebelum rilis. Ini tidak mengubah stack.
- Context7: `/pgvector/pgvector` memverifikasi Homebrew mendukung PG17/18; `/deepinsight/insightface` memverifikasi ONNX Runtime CPU dan bahwa buffalo/antelopev2 menggunakan SCRFD. Pencarian MiniFASNet di Context7 tidak menemukan repo yang tepat; fallback menggunakan sumber resmi MiniVision.

Sumber tambahan: [MiniVision](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing), [InsightFace model zoo](https://github.com/deepinsight/insightface/tree/master/model_zoo), [pgvector installation](https://github.com/pgvector/pgvector#installation).

## Realisasi teknis Tahap 3

- Delapan tabel PRD dipertahankan; audit_logs, shift_assignments, member_leaves, calendar_days dan locations melengkapi D-11/D-13/D-22. Tipe, kolom, constraint dan batas dijelaskan di database.md.
- Satu location LOCAL disiapkan untuk deployment awal lokal. Tidak mengaktifkan cloud/remote API, payroll atau perhitungan lembur.
- D-06: query bisnis menggunakan SQLAlchemy ORM/Core dengan parameter, DDL eksplisit hanya di migrasi/provisioning.
- D-14: code/username unik case-insensitive, soft delete member; app role tidak diberi DELETE member/user, FK historis RESTRICT.
- D-18: schema menjaga embedding, audit, izin dan kalender di DB; bundle backup aset tetap Tahap 13.
- D-17: audit menerima whitelist dan tidak memuat payload biometrik/password; RTSP repository belum menerima credential URL. Tidak ada pengumpulan wajah nyata; retensi operasional tetap diputuskan sebelum Tahap 7.
- Tahap 2 disetujui setelah review pengguna terhadap simulasi error. Tahap 3 memiliki bukti pada testing/stage-03.md; pengguna menyetujui review dan lanjut ke Tahap 4 pada 18 Oktober 2026.
- Context7 digunakan untuk SQLAlchemy session transactions, Alembic shared connection/migration dan pgvector VECTOR/cosine_distance; sumber tercantum pada database.md.

## Realisasi teknis Tahap 4

- D-09/D-10 memakai baseline yang telah diterima: Users hanya Super Admin; Viewer hanya Reports. Group/shift/device untuk Super Admin/Admin; diagnostik untuk Super Admin/Admin/Operator. Semua aksi layanan memvalidasi token, akun aktif dan peran terbaru dari database.
- D-16: bcrypt cost 12, password 12–72 byte UTF-8. Lima kegagalan login mengunci 15 menit; batas waktu tepat 15 menit sudah dapat mencoba kembali. Timeout idle 15 menit hanya diperpanjang input pengguna, bukan timer/background task. Nilai kebijakan dibaca dari settings.
- Detail implementasi remember: token acak 256 bit, SHA-256 di DB; token mentah hanya di macOS Keychain atau Windows Credential Manager. Masa refresh 30 hari; sesi interaktif terpisah memiliki idle timeout dan batas absolut 24 jam. Tutup aplikasi secara normal mencabut sesi interaktif, refresh grant bertahan. Logout/timeout/password change/reset/deactivate/role change mencabut token sehingga remember tidak melewati penguncian sesi.
- Reset menampilkan password hasil reset sekali; sejak revisi pengguna 21 Oktober 2026, penggantian password tidak diwajibkan. Bootstrap GUI/CLI tidak mempunyai password bawaan dan hanya tersedia sebelum ada Super Admin aktif. User delete diwujudkan dengan nonaktif untuk menjaga audit; akun aplikasi tetap tidak memiliki hak hard DELETE.
- Satu advisory transaction lock yang sama melindungi bootstrap dan perubahan akun/sesi, termasuk perlindungan Super Admin terakhir. Username unik case-insensitive. Akun sendiri tidak dapat dinonaktifkan atau diturunkan dari Super Admin; perubahan akun mencabut sesi lama.
- keyring 25.7.0 ditambahkan sebagai alat pendukung. Backend selain native macOS/Windows ditolak; jika penyimpanan aman tidak tersedia, login password tetap dapat dipakai dan remember tidak disimpan ke berkas biasa.
- Detail 30 hari/24 jam adalah pilihan implementasi Tahap 4 untuk memperjelas baseline D-16, bukan angka eksplisit dari PDF. Review Tahap 4 mencakup detail ini.
- MCP Context7 memverifikasi keyring native get/set/delete dan SQLAlchemy transaction/FOR UPDATE, termasuk kebutuhan session terpisah per worker.

Sumber: [keyring macOS](https://github.com/jaraco/keyring/blob/main/keyring/backends/macOS/__init__.py), [keyring Windows](https://github.com/jaraco/keyring/blob/main/keyring/backends/Windows.py), [SQLAlchemy transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), [Session per thread](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#is-the-session-thread-safe-is-asyncsession-safe-to-share-in-concurrent-tasks).

## Realisasi teknis Tahap 5

- D-09/D-10: grup/shift/penugasan hanya Super Admin/Admin; Members (lihat/edit/pindah grup/nonaktif/riwayat) untuk Super Admin/Admin/Operator. Operator dapat melihat nama grup pada formulir anggota tanpa memperoleh hak CRUD group atau assignment shift.
- D-11/D-12: jam shift memakai ketelitian menit; akhir sebelum mulai berarti hari berikutnya, jam sama ditolak. Grace harus lebih kecil dari durasi shift. Early leave tetap dihitung dari OUT sebelum akhir shift pada Tahap 10, bukan toggle baru atau klaim pencatatan sudah aktif.
- Tanggal penugasan inklusif pada tanggal kerja; maksimal satu penugasan berlaku per anggota pada tanggal yang sama. Setelah berakhir 18 Oktober, penugasan berikut boleh mulai 19 Oktober. Akhir kosong berarti tanpa batas; akhiri dahulu sebelum mengganti. Jam/grace shift yang sudah direferensikan penugasan/attendance tidak diubah; buat shift baru agar riwayat tetap akurat.
- D-14: anggota tetap soft delete; grup/shift yang direferensikan tidak dihapus, termasuk referensi anggota nonaktif atau riwayat. Pindah grup tidak mengganti snapshot group pada attendance lama. Revision counters menolak stale edit agar perubahan terminal/pengguna lain tidak tertimpa.
- Sesuai gerbang plan, form registrasi baru disiapkan tetapi penyimpanan/penyelesaian registrasi tetap diblokir sampai capture/embedding Tahap 8. Tidak menambah draft/anggota aktif hanya berdasarkan foto profil. Tidak membuat anggota contoh pada development.
- Demo administrasi bersifat opt-in melalui script: schema unik pada stargate_test, foto bidang warna sintetis, 25 anggota dan riwayat buatan. Tidak ada wajah/AI/kamera/Keychain nyata; normal close menghapus schema dan aset demo. Empat role tersedia, akun/password demo acak di memori tanpa ditampilkan. Crash/force kill dapat meninggalkan schema uji, sehingga cleanup otomatis hanya dijamin pada exit normal/exception Python yang ditangani.
- Foto profil pengganti dipilih pengguna, diperiksa PNG/JPEG <=10 MiB dan <=16MP, disalin sebagai PNG privat <=1024px di .local/member_photos; file baru dibuang jika transaksi gagal. Foto lama tidak dihapus otomatis sebelum kebijakan retensi final. Retensi/izin sampel wajah tetap diputuskan sebelum pengumpulan data nyata Tahap 7.
- Context7 memverifikasi SQLAlchemy transaction/row locking dan QImageReader canRead/read/scaledSize/allocation limit. Implementasi memakai session terpisah per worker dan guard auth dalam transaksi yang sama dengan mutasi; tidak menambah dependensi.

Sumber: [SQLAlchemy transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), [SQLAlchemy FOR UPDATE](https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.Select.with_for_update), [PyQt6 QImageReader](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtgui/qimagereader.html).

## Realisasi teknis Tahap 6

Pengguna menyetujui Tahap 5 setelah perbaikan ADM-B003 dan mengizinkan Tahap 6. Pengguna menyatakan sumber RTSP belum tersedia. RTSP positif nyata tetap tertunda; pengguna kemudian mengonfirmasi cabut USB aman setelah CAM-B003, menyetujui review dan mengizinkan Tahap 7. Mock tidak menggantikan gerbang hardware.

- URL RTSP penuh disimpan memakai native OS vault yang sudah menjadi dependensi proyek; database hanya menyimpan safe host/port dan reference. Tidak menambah library enkripsi atau menyimpan key berdampingan dengan database.
- Capture di proses spawn terpisah agar read native macet dapat dihentikan tanpa membekukan GUI. Default maksimal dua stream, dapat dikonfigurasi 1–4; open timeout 5 detik, read timeout 3 detik, dua reconnect khusus RTSP. Webcam lokal berhenti setelah gagal dan memerlukan verifikasi nomor/mulai manual karena index dapat berubah.
- Resolusi pilihan 640×480/1280×720/1920×1080 dan FPS 1–60. Resolusi aktual ditampilkan karena perangkat dapat menegosiasikan nilai berbeda. Slot preview dibatasi 960×540; belum menentukan resolusi input engine AI.
- Webcam bawaan/USB dapat memerlukan pemilihan ulang nomor setelah perubahan koneksi. Jenis perangkat merupakan klasifikasi pengguna, bukan klaim pemetaan nama hardware ke index OpenCV yang tetap.

## Realisasi dan keputusan uji Tahap 7

Pengguna mengizinkan lanjut setelah review Tahap 6 dan secara eksplisit menyetujui pengujian wajah hanya di memori: tidak menyimpan foto atau embedding nyata ke DB/berkas. Ini kebijakan untuk alat uji sementara, bukan retensi operasional/enrollment Tahap 8. Uji foto cetak dan replay dilakukan pengguna sendiri. Instruksi lanjut mengizinkan implementasi Tahap 7 sambil mempertahankan RTSP positif Tahap 6 sebagai NOT RUN.

D-05/D-19: model dan hash Tahap 1 dipertahankan; CPU, satu detektor RetinaFace. Model 106 landmark hanya untuk alignment ArcFace 112×112, bukan detektor kedua. Model version mengikat checksum ArcFace, landmark dan versi pipeline; query tidak mencampur versi model. Similarity = 1 − cosine distance dengan L2-normalisasi, rentang −1..1 dan threshold default 0,60 inklusif.

MiniFASNetV2 2.7/80×80 memakai crop berkonteks dari BGR asli, float CHW **0–255** sesuai kode functional.to_tensor pada commit yang dipin; docstring 0–1 upstream tidak sesuai implementasi aktual. Kelas 1 berarti live; softmax kelas 1 harus >=0,85 dan argmax harus kelas 1. Tidak membagi dua skor dari satu model (upstream contoh menggabungkan dua model). Jika liveness aktif dan gagal, tidak mengeluarkan embedding yang diterima. Model hilang/rusak gagal tertutup sebelum parser/torch loader berjalan; tidak download model otomatis.

D-23: registration/lab menolak beberapa wajah; API recognition memilih deterministik area terbesar, confidence lalu koordinat. Semua wajah tetap dihitung. Pemeriksaan awal kualitas memakai sisi bbox >=64px, margin frame 2px, gray mean 30–225 dan Laplacian variance >=35. Nilai ini heuristik awal yang belum dikalibrasi pada holdout, bukan angka PRD atau jaminan akurasi. max face size Auto tidak memaksakan crop wajah terbesar ke resolusi tetap sebelum quality gate.

Native inference dijalankan satu proses spawn, model dimuat sekali, satu input shared-memory maksimal 960×540, satu permintaan aktif tanpa backlog. Batas recognition 3 detik diawasi parent dan checkpoint antarkomponen; proses macet dihentikan lalu memerlukan mulai manual. Loading awal dibatasi 30 detik dan dilaporkan terpisah, tidak disamarkan sebagai latency inferensi.

## Realisasi dan keputusan Tahap 8

Pengguna menyetujui review Tahap 7 dan mengizinkan Tahap 8. Persetujuan tidak menghasilkan angka uji liveness per kondisi yang tidak dilaporkan. Pengguna mengizinkan penyimpanan data nyata, memilih mengganti/menghapus embedding lama setelah set baru lengkap, dan meminta rekomendasi retensi dari beberapa sumber nyata. Dasar dan keputusan produk: [biometric-retention.md](biometric-retention.md), memuat UU PDP Indonesia, ICO dan GDPR serta batas penerapannya.

Foto profil dan lima embedding disimpan selama anggota aktif dan masih memerlukan absensi. Nonaktif anggota menghapus biometrik aplikasi, mengganti foto dengan placeholder dan mempertahankan attendance/audit. Ini memperbarui kebijakan penahanan biometrik sementara Tahap 5; tidak mengubah kebutuhan menjaga riwayat. Foto dihapus setelah commit dengan pemeriksaan reference dan retry orphan. Copy asli di luar direktori aplikasi tidak dihapus. Backup/WAL/media belum dinyatakan terhapus secara forensik; backup/restore harus mengikuti kebijakan pada Tahap 13.

Capture memakai proses terisolasi dan lima pose berurutan. Rasio landmark adalah heuristik awal, bukan estimasi 3D terkalibrasi. Liveness registrasi dipaksa aktif/.85; guard identitas sama mengikuti similarity konfigurasi (default .60). Handoff HMAC terikat sesi/member/revision/nonce, TTL 15 menit sebagai parameter freshness. Hanya set lengkap dapat disimpan; gagal SQL mempertahankan set lama dan membersihkan file baru. Tidak menyimpan lima foto mentah atau video.

Tombol uji wajah tersimpan membuat probe baru hanya di memori dan query gallery PostgreSQL aktif versi model sama setelah restart. Tidak menambah embedding atau attendance. Penerimaan lima sudut/pose dan kecocokan wajah nyata tetap uji mandiri pengguna; tests otomatis hanya sintetis/fixture publik sesuai label bukti.

## Realisasi dan keputusan Tahap 9

Pengguna menyatakan review Tahap 8 sudah OK dan mengizinkan lanjut. Rincian skor/jumlah trial nyata tidak dikirim dan tidak dibuatkan hasil kuantitatif. RTSP positif tetap tertunda.

D-24: Database menjadi sumber konfigurasi operasional delapan parameter recognition/anti-spoof/attendance. Konfigurasi koneksi/rahasia tetap .env/vault. Snapshot pengaturan valid dibuat di transaksi yang sama dengan otorisasi dan pembentukan flow capture, terikat pada packet bertanda tangan; query identifikasi memakai similarity snapshot. Perubahan berlaku pada pemeriksaan baru, tanpa memutasi model/timeout/keputusan proses berjalan. Registrasi tetap mewajibkan liveness aktif/.85 sesuai Tahap 8; verification memakai kebijakan anti-spoof tersimpan. Kehilangan/kerusakan nilai pengaturan gagal tertutup.

D-25: Super Admin/Admin boleh mengubah melalui SettingsService; Operator/Viewer ditolak. Update batch, audit nilai lama/baru dan pemeriksaan snapshot lama dalam satu transaksi, dengan row lock berurutan setelah lock auth yang sudah ada. Konflik tidak menimpa perubahan admin lain; pengguna diminta muat ulang eksplisit. Save tanpa perubahan tidak menambah audit setting.changed. Auto/Shift adalah mode tunggal yang disebut PRD, tanpa tambahan mode yang belum ditentukan. Rentang numerik mengikuti validator repository yang sudah dipakai sejak Tahap 3.

Aturan absensi tersimpan sekarang, penerapan transaksi cooldown/shift/auto checkout dan US-028 attendance end-to-end tetap Tahap 10. Lab demo AI mandiri tidak membaca database; uji konfigurasi melalui main.py/Anggota/Uji wajah tersimpan. Context7 SQLAlchemy dipakai untuk memverifikasi transaksi dan FOR UPDATE, tanpa pembaruan dependency.

## Realisasi dan keputusan Tahap 10

Pengguna menyetujui review Tahap 9 dan mengizinkan lanjut pada 19 Oktober 2026. Pengguna secara eksplisit memilih: **tolak check-in sebelum jam mulai shift; izinkan mulai tepat jam shift**. Rincian percobaan nyata Tahap 9 tidak dilaporkan dan tidak dibuatkan metrik tambahan.

D-07/D-08/D-12 diterapkan dari baseline yang sudah diterima: jeda <60 ditolak, tepat 60 lolos jeda; AUTO awal IN, berikutnya OUT, setelah BREAK_OUT menjadi BREAK_IN. Mode IN eksplisit tidak menghasilkan IN ganda. Setelah OUT tidak menerima event pada sesi yang sama. Tepat start+grace masih Present; early leave terpisah dan tidak menghapus Late. OUT dan penyelesaian istirahat boleh setelah akhir shift, memulai istirahat baru tidak boleh. Sesi terbuka lama diselesaikan sebelum sesi berikutnya dibuka.

D-26: setelah scan sukses, kamera yang sama menahan anggota tersebut sampai detektor tidak menemukan wajah setidaknya satu detik. Orang lain dapat diproses. Ini mencegah OUT tidak sengaja bila orang tetap berdiri setelah cooldown; tidak mengganti cooldown lintas kamera atau liveness. Probe bertanda tangan memakai sequence dan batas waktu recognition sejak pemeriksaan dimulai; diperiksa ulang sebelum/sesudah penulisan agar pekerjaan database yang terlalu lambat tidak meloloskan probe kedaluwarsa. Tidak menyimpan probe/foto/video dari scan.

D-27: versi kebijakan mencakup delapan nilai settings dan updated_at. Semua jalur attendance revalidasi policy/perangkat/lokasi/sesi pada transaksi auth yang sama; pengaturan yang berubah saat inference menolak hasil lama dan memerlukan mulai ulang. Lokasi memakai zona IANA untuk tanggal shift; timestamp disimpan UTC. Penugasan berlaku harian dalam rentang tanggal, kecuali kalender nonkerja atau izin yang tercatat. Editor kalender/izin dan dashboard bukan cakupan Tahap 10.

D-28: checkout otomatis default off; berjalan setelah login dan setiap 10 detik selama aplikasi terbuka dan sesi Attendance sah, maksimal 100 sesi due per transaksi. Catch-up saat login berikutnya, tanpa daemon sistem baru. OUT dicatat pada akhir shift, diberi is_automatic, tidak menimpa OUT manual, tidak mengarang BREAK_IN untuk istirahat yang belum selesai, dan dapat memfinalisasi sesi anggota yang kemudian nonaktif. Aktor audit adalah pengguna yang menjalankan scheduler. Tidak menafsirkan event otomatis sebagai bukti fisik keberadaan sampai akhir shift.

Notifikasi/suara sukses dikirim setelah transaksi committed; kegagalan audit/DB tidak membuat sukses palsu. Menghentikan kamera mencegah scan baru, transaksi yang sudah dimulai ditunggu penyelesaiannya. Member history membedakan sumber Scan/Otomatis. Suara WAV dibuat lokal, QSoundEffect memakai PyQt6 yang sudah terpasang. Tidak ada migrasi/dependency baru; target RTSP nyata, Windows, SLA dan statistik tetap memerlukan pengujian terpisah.

## Keputusan persiapan Windows Tahap14

Pengguna pada 20 Oktober 2026 menyebut Windows melalui Parallels dan tujuan lomba/penelitian/internal dahulu. VM Windows11 ditemukan stopped; start gagal karena kekurangan disk minimal1589MB. Pengguna memilih menyiapkan dahulu dan menguji Windows kemudian. Arsitektur guest, executable, installer, driver/ACL/offline/upgrade/uninstall belum disertifikasi. Build Windows harus memakai host Windows dan interpreter x64; pada WindowsARM, x64 berjalan melalui emulasi dan kompatibilitas harus dibuktikan. Bobot riset opt-in, bukan izin distribusi komersial; PyQt tetap memerlukan pemenuhan GPL/komersial sebelum pembagian binary eksternal. Resource immutable dan data/config/log privat dipisahkan; tidak mengubah stack inti. Rincian: windows-install.md dan testing/stage-14.md.

## Revisi D-16 — penggantian password opsional, 21 Oktober 2026

Pengguna meminta penghapusan kewajiban mengganti password untuk semua akun, termasuk Super Admin pertama, akun buatan pengelola dan hasil reset. Login langsung membuka halaman sesuai peran; menu Ganti password tetap tersedia dan dapat dibatalkan. Reset tetap menghasilkan password acak yang ditampilkan sekali dan mencabut sesi lama. Hashing, batas panjang password, penguncian login gagal, masa sesi dan pemeriksaan izin tetap berlaku.

Migrasi `0005_optional_password` mengubah default penanda lama menjadi false dan menghapus penanda wajib pada akun yang sudah ada, tanpa mengubah password atau menghapus akun/riwayat. Kolom lama tetap disimpan untuk kompatibilitas struktur dan berkas cadangan, tetapi tidak lagi menghalangi login, remember-session, atau akses fitur.

## D-29: lanjut bersyarat menggunakan Parallels, 28 Oktober 2026

Pengguna meminta mencoba build terbaru pada Parallels lalu melanjutkan tahap berikutnya karena deadline dan customer tidak berada bersama pengguna. Pengguna mengonfirmasi dashboard terlihat setelah login pada ruang uji baru. Kamera FaceTime HD Camera indeks0 berhasil pada1280x720, ditutup/dibuka ulang; pengguna memilih melanjutkan dengan kamera yang tersedia dahulu ketika kamera kedua tidak tersedia.

Tahap15 boleh dimulai berdasarkan hasil installer/runtime Parallels dan konfirmasi dashboard tersebut. Pengujian AMD fisik dan kamera kedua ditunda; keduanya tetap belum diuji pada putaran ini. USB dicabut secara fisik, RTSP positif, suara, pembaca laporan, restart Windows dan alur wajah nyata menyeluruh tetap mempunyai catatan pengujian terbuka. Keputusan melanjutkan tidak mengubah kasus yang belum diuji menjadi PASS, tidak menjamin kompatibilitas AMD, dan tidak mengubah target akurasi/liveness/SLA.

Ruang uji interaktif memakai `%LOCALAPPDATA%\StarGate-Parallels-0141`, database kelolaan baru dan seeder SMP fiktif. Konfigurasi lama `%LOCALAPPDATA%\StarGate\.env` dipertahankan. Model dan stack produksi tetap mengikuti ketentuan awal; pengukuran vektor sintetis hanya menilai kinerja pencarian.
