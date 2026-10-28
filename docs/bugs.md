# Catatan bug dan isu StarGate

Tanggal: 18 Oktober 2026. Smoke test lingkungan Tahap 1 sudah dijalankan; hasil tahap terbaru dicatat di bawah; kelulusan terbatas pada cakupan yang sudah diuji.

## Defect implementasi

Defect implementasi dan perbaikannya dicatat per tahap. Template:

| ID | Tahap / test | Severity | Reproduksi / expected / actual | Penyebab | Perbaikan | Uji ulang | Status |
|---|---|---|---|---|---|---|---|

Status defect: OPEN -> REPRODUCED -> FIXED -> RETEST -> CLOSED; gagal retest kembali OPEN. Catat environment/versi kode dan bukti tersanitasi.

## Isu spesifikasi yang sudah ditemukan

| ID | Masalah | Keputusan terkait | Status |
|---|---|---|---|
| SPEC-001 | Duplicate check-in ditolak tetapi scan selanjutnya menjadi OUT; batas cooldown belum tegas | D-07/D-08 | OPEN: usulan tersedia |
| SPEC-002 | Matriks Users hanya Super Admin, US menyebut admin | D-09 | OPEN: usulan tersedia |
| SPEC-003 | Persona Supervisor/Auditor tidak ada di empat role resmi | D-10 | OPEN: usulan tersedia |
| SPEC-004 | Penugasan shift, izin/kalender dan audit belum ada di daftar tabel | D-11/D-13/D-18 | OPEN: usulan tersedia |
| SPEC-005 | Format ekspor kosong | D-15 | OPEN: usulan tersedia |
| SPEC-006 | Nilai timeout/lockout/remember me, retensi, backup aset belum dirinci | D-16/D-17/D-18 | OPEN: usulan tersedia |
| SPEC-007 | Target speed/accuracy di ringkasan berbeda pada batas kesetaraan dengan MVP | D-20/D-21 | OPEN: usulan tersedia |
| SPEC-008 | Multi-lokasi dan lembur disebut tanpa alur lengkap; cloud/payroll V2 | D-22 | OPEN: butuh batas V1 |
| SPEC-009 | DoD Critical/Open dan metode SLA belum jelas | D-20 | OPEN: usulan tersedia |

Isu spesifikasi bukan defect runtime dan tidak dihitung seolah pengujian produk gagal. Isu wajib diselesaikan sebelum fitur terkait; gerbang tahap tetap mempertimbangkan keputusan yang diperlukan.

## Isu lingkungan Tahap 1

| ID | Gejala | Penyebab / perbaikan | Uji ulang | Status |
|---|---|---|---|---|
| SETUP-001 | initdb gagal shared memory | Batas sandbox; ulang dengan izin proses yang sesuai | init/start dan lifecycle PASS | CLOSED |
| SETUP-002 | Kamera tidak diizinkan | Pengguna mengaktifkan izin macOS | Dua kamera PASS | CLOSED |
| SETUP-003 | Kamera indeks 1 tidak tersedia | USB belum terdeteksi; pengguna menyambungkan perangkat | Inventory dua perangkat dan frame 1920x1080 PASS | CLOSED |
| SETUP-004 | Versi Qt runtime dilaporkan sebagai compile version | Gunakan qVersion(), bukan QT_VERSION_STR untuk runtime | Import check diulang PASS, bukti diperbarui | CLOSED |

Review Tahap 0 menerima usulan terdefinisi sebagai baseline. SPEC-* masih mencatat asal gap dan rincian yang harus diturunkan sebelum fitur terkait; status OPEN tidak berarti ada defect runtime yang disembunyikan.

## Fondasi Tahap 2

| ID | Temuan | Perbaikan dan bukti | Status |
|---|---|---|---|
| FND-B001 | Clock header terpotong pada screenshot awal | Tambah minimum width; screenshot native final terbaca | CLOSED |
| FND-B002 | Pola credential prefiks/dictionary belum tercakup regex umum saat review | Perluas redaksi dan regression test; tests PASS | CLOSED |

26 tests dan smoke native/offscreen lulus untuk fondasi. Tidak ada critical defect fondasi yang diketahui dari cakupan uji ini; fitur bisnis belum diuji. Error dari tombol Simulasikan kesalahan adalah input uji yang disengaja, bukan bug terbuka.

## Database Tahap 3

| ID | Temuan | Perbaikan dan uji ulang | Status |
|---|---|---|---|
| DB-B001 | Autogenerate memasukkan drop metadata Alembic | Dihapus sebelum apply; exclude metadata table dan test round-trip/metadiff lulus | CLOSED |
| DB-B002 | Introspeksi unqualified membaca fallback public setelah tabel uji di-drop | Schema eksplisit pada health check dan test; regresi missing table/column; run akhir 75/75 PASS | CLOSED |

Run antara sempat 74 PASS/1 FAIL karena DB-B002. Tidak ada public table yang dihapus; schema sementara dibersihkan. Run akhir 75 PASS dan coverage 91,36%; persistent data sesudah restart terverifikasi. Fitur UI bisnis belum diuji.

## Autentikasi Tahap 4

| ID | Temuan | Perbaikan dan uji ulang | Status |
|---|---|---|---|
| AUTH-B001 | Native macOS: dialog reset menggunakan exec di callback hasil worker dapat timeout/macet pada nested event loop | Reset dan bootstrap memakai open + finished callbacks; field dibersihkan setelah dialog ditutup. Kasus gagal dan seluruh 10 native UI tests lulus | CLOSED |
| AUTH-B002 | Keychain locked dapat menghalangi login biasa karena pembacaan remember lama | Expected credential error tidak menghalangi autentikasi password; token remember gagal disimpan dicabut, tanpa fallback plaintext. Regression test backend unavailable lulus | CLOSED |
| AUTH-B003 | Form native macOS mempertahankan lebar input kecil dan checkbox kurang jelas | Field growth policy dan gaya input/table eksplisit; native screenshot diperiksa dan tes GUI diulang | CLOSED |

Regresi Tahap 4: 100 PASS, termasuk database nyata dan Keychain lintas proses; 10 tes GUI native PASS. Tidak ada Critical defect terbuka yang diketahui pada cakupan ini. Modul yang belum dibangun serta Windows/SLA bukan dianggap lulus.

## Temuan uji mandiri Tahap 4 — AUTH-B004

Pengguna melaporkan halaman ganti password berkedip dan input kehilangan fokus setiap kedip setelah login pertama. Penyebab terkonfirmasi: timer validasi sesi tiap satu detik memakai jalur busy yang sama dengan operasi simpan, sehingga seluruh password_panel dinonaktifkan lalu diaktifkan kembali.

Reproduksi otomatis sebelum perbaikan gagal pada pemeriksaan input tetap aktif saat validasi sesi berjalan. Perbaikan memberi penanda blocks_ui=False khusus pemeriksaan sesi rutin; login/simpan/reset tetap memakai penguncian interaksi, dan validasi/timeout tetap dijalankan di worker. Tidak mematikan timer atau memperpanjang idle timeout sebagai jalan pintas.

Regresi memeriksa fokus dan ketikan sebelum/selama/setelah pemeriksaan pada tiga field, baik forced change pertama kali maupun ganti password biasa. Dua tes offscreen dan dua tes macOS native lulus. Regresi lengkap 102 PASS, 0 skip, coverage 91.47%. Bukti: testing/evidence/stage-04-focus-summary.json. Status: CLOSED; menunggu uji ulang pengguna.

## Administrasi Tahap 5

| ID | Temuan | Perbaikan dan uji ulang | Status |
|---|---|---|---|
| ADM-B001 | Closure pagination mengubah offset lalu membacanya sebelum local terisi | page_offset terpisah; pagination, offset stale dan empty tests lulus | CLOSED |
| ADM-B002 | Native filter grup terpotong dan tombol pertama keluar dari baris | Minimum width dan explicit None check layout; screenshot diperiksa, 7 native tests lulus | CLOSED |
| AUTH-B005 | Simpan Pengguna dapat terlewat bila bertepatan dengan polling sesi; regresi awal 142 PASS/1 FAIL | Satu aksi foreground diantrekan setelah poll; dibuang jika sesi tidak valid. Dua regresi dedicated, 14 auth UI dan 21 combined native PASS | CLOSED |

Run akhir Tahap 5: 147 PASS, 0 failure/error/skip, coverage 93,23%; 21 GUI/auth native PASS. Tidak ada Critical defect terbuka yang diketahui pada cakupan ini. Capture/AI/attendance nyata dan Windows belum dinyatakan lulus. Detail: testing/stage-05.md.

## Uji mandiri Tahap 5 — ADM-B003

Pengguna melaporkan Akhiri penugasan baru aktif setelah berpindah menu dan kembali. Dropdown shift serta penugasan belum menghubungkan currentIndexChanged ke pembaruan controls, sehingga enabled state baru dihitung ketika detail dimuat ulang.

Perbaikan menghubungkan kedua dropdown ke controls. Memilih shift valid langsung mengaktifkan Tetapkan shift; memilih penugasan valid langsung mengaktifkan Akhiri penugasan, sedangkan placeholder membuatnya tidak aktif. Guard pending, anggota aktif dan izin role tetap berlaku.

Pengujian sebelumnya memanggil metode aksi langsung, sehingga tombol disabled terlewat. Kasus regresi kini memeriksa enabled state dan memakai klik tombol untuk create/end/assign berikutnya tanpa navigasi. Reproduksi sebelum fix FAIL; sesudah fix 19 tes UI/layanan administrasi PASS dan satu skenario macOS native PASS. Bukti pada testing/evidence/stage-05-assignment-buttons-regression.xml dan stage-05-assignment-buttons-native.xml. Status: CLOSED; menunggu pengguna menguji ulang.

## Perangkat/kamera Tahap 6

| ID | Temuan | Perbaikan dan uji ulang | Status |
|---|---|---|---|
| CAM-B001 | ORM default mengubah camera_index NULL RTSP menjadi 0 dan menaikkan revision pada no-op update | evaluates_none dan regression DB no-op lulus | CLOSED |
| CAM-B002 | Input RTSP lama dapat terbawa saat mengubah jenis ke lokal | Bersihkan input dan reset masking pada perubahan jenis; tes UI klik tombol lulus | CLOSED |
| CAM-O001 | Pembukaan pertama hardware index 0 gagal setelah dua frame | Buka ulang dan multi-camera berhasil; run ulang 60 frame/kamera PASS. Penyebab awal belum terisolasi; perlu pemantauan uji mandiri/soak | OBSERVATION |

191 tes regresi PASS, coverage 92,37%; 27 GUI native PASS. RTSP positif nyata dan cabut/pasang fisik NOT RUN, bukan bug yang dinyatakan tertutup. Detail: testing/stage-06.md. Tahap 7 belum dimulai.

## Uji mandiri Tahap 6 — CAM-B003

Pengguna mencabut USB (index 0); retry membuka webcam laptop. Penyebab: CameraManager membuka index lokal yang sama, sementara index sudah menunjuk perangkat fisik lain. Ini bukan fallback yang benar. Perbaikan membatasi reconnect otomatis untuk RTSP; INTERNAL/USB berhenti saat gagal, frame dibersihkan, proses dilepas, lalu UI meminta verifikasi nomor dan mulai manual. Identitas hardware lokal yang stabil belum didukung; mitigasi ini tidak mengklaim otomatis mengenali USB yang sama setelah sambung ulang.

Regresi mensimulasikan index yang akan mengembalikan sumber lain jika dibuka kembali: INTERNAL/USB tidak boleh retry; mulai manual tetap bekerja. Jalur RTSP retry/recovery dan UI/session lifecycle juga diuji. Bukti: testing/evidence/stage-06-local-disconnect.xml dan stage-06-local-disconnect-native.xml. Status: perbaikan terverifikasi otomatis; menunggu uji cabut/pasang fisik ulang pengguna. Baseline 191/92,37% di atas berasal dari sebelum perbaikan ini.

CAM-B003: pengguna mengonfirmasi masalah terselesaikan setelah restart aplikasi, lalu menyetujui review Tahap 6. Status CLOSED berdasarkan regresi otomatis dan uji ulang pengguna; ini bukan dukungan identitas hardware lokal stabil.

## Engine AI Tahap 7

| ID | Temuan | Penanganan dan uji | Status |
|---|---|---|---|
| AI-B001 | Docstring MiniVision ToTensor mengatakan 0–1, tetapi kode functional pada commit bobot mengembalikan 0–255 | Ikuti implementasi yang dipin; test BGR dan range tensor eksplisit. Tidak menyesuaikan threshold dari skor peserta | CLOSED, sebelum penerimaan |
| AI-B002 | Review watchdog menemukan hasil di pipe dapat diterima setelah deadline bila diproses sebelum pengecekan waktu | Cek deadline sebelum menerima hasil; regression fake clock memastikan hasil terlambat dibuang dan proses direap | CLOSED |
| AI-O001 | InsightFace norm_crop memakai SimilarityTransform.estimate yang deprecated pada scikit-image terpasang | Runtime dan integrasi masih lulus; warning tetap terlihat, versi lock tidak diubah; evaluasi sebelum upgrade dependency | OBSERVATION |
| AI-O002 | Kamera nyata delapan sampel mendeteksi satu wajah tetapi bbox terpotong tepi | Quality gate menolak partial_face sebelum liveness/embedding. Perlu posisi kamera/wajah yang layak untuk uji mandiri; bukan PASS genuine/spoof | PENDING REAL TRIAL |

Model/DB/unit/UI diverifikasi terpisah dari akurasi manusia. Wajah asli layak, unknown subject, foto cetak dan replay lewat kamera belum diterima; gerbang Tahap 7 masih tertunda. Bukti dan prosedur: testing/stage-07.md. Tidak menyimpan foto atau embedding nyata dan tidak memulai Tahap 8.

Regresi akhir Tahap 7: 233 PASS/0 skip, coverage app+database+ai 91,14%; 7 tes native PASS. Satu FutureWarning upstream tetap tercatat. Bukti: testing/evidence/stage-07-summary.json. Gerbang nyata awal belum lulus, Tahap 8 belum dimulai.

## Registrasi Tahap 8

| ID | Temuan | Penanganan dan verifikasi | Status |
|---|---|---|---|
| ENR-B001 | Setup awal tes menggunakan AuthService.db yang tidak ada | Fixture memakai database; uji layanan ulang lulus | CLOSED, fixture |
| ENR-B002 | Helper smoke sementara spawn tanpa guard __main__ | Guard ditambahkan pada helper; entry point produksi sudah memakai guard, smoke model nyata no-face lulus | CLOSED, helper |
| ENR-B003 | Review visual menunjukkan status menunggu kamera setelah lima sudut lengkap | Tahan preview PNG depan di memori untuk review sebelum save; kamera sudah berhenti, tes native lulus | CLOSED |
| ENR-B004 | Edit metadata pada anggota nonaktif sebelumnya dapat menerima foto baru, bertentangan dengan kebijakan retensi baru | UI dan service menolak photo_source untuk anggota nonaktif; edit metadata tetap bisa, regresi khusus lulus | CLOSED |

Uji sintetis membuktikan rollback sampel ketiga, preservation set lama saat registrasi ulang gagal, pembaruan lengkap saat sukses, pembersihan foto pending/retry dan pencarian gallery dari proses/jendela baru. Pose heuristik dan kecocokan wajah nyata lima sudut setelah restart tetap uji mandiri, bukan dinyatakan PASS dari tes sintetis. Tahap 9 belum dimulai.

Run final Tahap 8: 260 PASS/0 skip, coverage app+database+ai 90,17%; 28 tes GUI/auth/administrasi native PASS. Satu FutureWarning upstream, tanpa error/failure. Bukti: testing/evidence/stage-08-summary.json. Uji nyata tetap diperlukan sebelum gerbang Tahap 8 lulus penuh.

## Pengaturan Tahap 9

| ID | Temuan | Penanganan dan verifikasi | Status |
|---|---|---|---|
| SET-B001 | Fixture UI awal menukar argumen angle/vector saat membuat embedding sintetis | Perbaiki urutan sesuai API repository; tidak mengubah validasi produksi | CLOSED, fixture |
| SET-B002 | Regresi penuh tersangkut saat thread Qt selesai; sample menunjukkan GUI membuat koneksi QTimer.singleShot sambil destructor worker menunggu GIL pada disconnectNotify | Poll join memakai QTimer persisten yang terkoneksi sejak init, bukan membuat koneksi baru saat cleanup. Ditambah uji reuse 100 pekerjaan; suite penuh/native diulang | CLOSED; 284 regresi/37 native PASS |
| SET-B003 | Uji fokus native dapat meminta fokus sebelum aktivasi jendela macOS selesai | Helper tes raise/activate lalu qWaitForWindowActive; seluruh assertion fokus/typing tetap dijalankan; 7 kasus terisolasi PASS | CLOSED, fixture |

Tahap 8 sudah direview/disetujui pengguna dan Tahap 9 diizinkan. Tidak ada angka uji nyata tambahan dari persetujuan itu. Hasil akhir Tahap 9 dicatat dalam testing/stage-09.md; absensi operasional tetap Tahap 10.

Verifikasi akhir Tahap 9: 284 regresi PASS/90,37% coverage, 37 tes native PASS, 7 uji fokus terisolasi PASS. Suite native akhir dijalankan sendiri setelah memperbaiki prasyarat aktivasi; assertion fokus/typing tetap dijalankan. Bukti: testing/evidence/stage-09-summary.json.

## Absensi Tahap 10

| ID | Temuan | Penanganan dan verifikasi | Status |
|---|---|---|---|
| ATT-B001 | PostgreSQL lokal tidak aktif pada run awal; traceback dependency terlalu rinci | Jalankan cluster proyek tanpa reset data; pytest memakai traceback singkat tanpa konteks lokal dependency, keluaran gagal awal tidak dipakai sebagai bukti PASS | CLOSED, lingkungan/pelaporan |
| ATT-B002 | Fixture awal memakai label versi embedding berbeda dari probe sintetis | Samakan label synthetic-v1; tidak melonggarkan pemisahan versi model produksi | CLOSED, fixture |
| ATT-B003 | Menangkap error audit bersama validasi state dapat mengubah kegagalan penulisan menjadi feedback biasa | Penulisan/audit berada di luar catch validasi; tes kegagalan audit memastikan event dan audit rollback | CLOSED |
| ATT-B004 | BREAK_IN setelah akhir shift sempat ditolak sehingga sesi istirahat terbuka tidak dapat diselesaikan manual | Izinkan penyelesaian istirahat dan OUT; tetap tolak IN/BREAK_OUT baru setelah akhir shift | CLOSED; regresi akhir 334 PASS |
| ATT-B005 | Probe dapat menjadi kedaluwarsa selama query/penulisan DB | Cek freshness sebelum dan sesudah penulisan; keterlambatan membatalkan transaksi termasuk audit | CLOSED; regresi akhir 334 PASS |

Review Tahap 9 sudah disetujui pengguna. Hasil akhir Tahap 10 serta batas hardware/audio dicatat pada testing/stage-10.md. Jangan menandai SLA/RTSP/Windows atau ketahanan serangan nyata PASS dari fixture sintetis.

ATT-B006: kamera kedua yang terus melihat wajah sempat dapat mencoba OUT saat cooldown habis setelah kamera pertama menyimpan IN. Stream yang mendeteksi duplikat cooldown kini ikut menahan identitas sampai kondisi tanpa wajah; tes layanan serta dua kamera UI dan regresi akhir lulus.

Verifikasi akhir Tahap 10: **334 regresi PASS/89,90% coverage** dan **47 tes native PASS**, tanpa failure/error/skip. Satu FutureWarning upstream. Bukti: testing/evidence/stage-10-summary.json. UAT kamera/speaker/foto/replay tetap tertunda.

ATT-B007 (perbaikan setelah UAT): tombol Muat ulang terlihat berkedip selama scan karena enabled mengikuti setiap transaksi probe. Status tombol kini hanya mengikuti permintaan muat ulang; scan latar belakang tidak menonaktifkannya. Klik saat transaksi berjalan diantrikan satu kali dan dijalankan setelah transaksi selesai, tanpa menumpuk permintaan. Stop/navigasi membatalkan permintaan tertunda. Verifikasi: 11 tes halaman Kehadiran PASS (termasuk regresi perubahan enabled selama beberapa scan dan klik saat scan berlangsung), serta 2 tes native macOS PASS. Bukti: testing/evidence/stage-10-refresh-fix.xml dan stage-10-refresh-fix-native.xml. Suite penuh/coverage sebelumnya tidak dihitung ulang untuk perbaikan ini; Tahap 11 belum dimulai.

## Dashboard Tahap 11

Review Tahap 10 diterima pengguna pada 20 Oktober 2026; tahap berikutnya diizinkan. Persetujuan tidak diubah menjadi jumlah uji serangan/kamera fisik yang belum dilaporkan.

| ID | Temuan | Penanganan | Status |
|---|---|---|---|
| DASH-B001 | Fixture awal mengasumsikan Operator tidak berhak Dashboard dan membuat event tanpa argumen status wajib | Tes mengikuti matriks akses yang sudah ada; status fixture diberikan eksplisit. Tidak mengubah otorisasi atau validasi produksi | CLOSED, fixture |
| DASH-B002 | Fixture terminal lain memakai jam monotonic nyata sedangkan packet memakai jam uji terkontrol; predicate pergantian hari mengakses snapshot yang sedang dikosongkan | Samakan jam pada fixture terminal; tunggu snapshot baru non-None. Guard signature/freshness tetap utuh | CLOSED, fixture |
| DASH-B003 | Assertion awal demo mengharapkan jam UTC dari snapshot yang memang mempertahankan zona WIB | Assertion memeriksa jam 17:00 WIB dan menunggu tombol siap setelah pekerjaan selesai | CLOSED, fixture |

Pembaruan Dashboard berjalan single-flight pada worker sendiri; hasil yang kadaluwarsa karena tanggal/sesi/navigasi tidak diterapkan. Kegagalan data ditandai stale tanpa nol palsu. Bukti akhir dan batas: testing/stage-11.md.

## Laporan Tahap 12

Review Tahap 11 diterima pengguna; format laporan per anggota/shift/tanggal dan ekspor semua hasil disetujui terpisah pada 20 Oktober 2026.

| ID | Temuan | Penanganan | Status |
|---|---|---|---|
| REP-B001 | Cancel dapat datang sesudah file dipublikasikan tetapi sebelum checkpoint terakhir worker | TaskContext.commit mempertahankan hasil publikasi sukses, sementara cancel sebelum publikasi tetap mencegah file akhir. Tes race setelah hard link lulus | CLOSED |
| REP-B002 | Pengaturan date_format dari writer tidak cukup untuk konsistensi display tanggal OpenPyXL | Format tanggal/waktu diterapkan eksplisit pada sel bertipe, dibuka ulang dan diperiksa | CLOSED |
| REP-B003 | Pemeriksaan halaman tengah/akhir menemukan continuation nama panjang tanpa identitas pada awal halaman | Baris normal dipertahankan utuh; split di dalam baris hanya untuk sel melebihi tinggi area halaman. Regresi ekspor memeriksa ID muncul sebelum continuation teks, 13 tes ulang PASS | CLOSED |
| REP-B004 | Filter satu kolom menyisakan sedikit ruang untuk tabel pada jendela awal | Filter diringkas dua kolom dan notifikasi memakai nama file dengan tooltip lokasi penuh; diuji ulang native | CLOSED; 65 native PASS |

Tidak ada perubahan data operasional/migrasi. Detail verifikasi run lengkap dan perapian visual setelahnya: testing/stage-12.md.

## Audit dan pemulihan Tahap 13

| ID | Temuan | Penanganan | Status |
|---|---|---|---|
| REC-B001 | Fixture mengharapkan pengaman dibuat walaupun akun runtime ditolak pada lock tabel sebelum perubahan | Assertion membedakan penolakan izin awal dari kegagalan sesudah pengaman; data tetap utuh | CLOSED, fixture |
| REC-B002 | Kegagalan koneksi ketika acknowledgement commit tidak membuktikan rollback | Pesan membedakan status commit ambigu dan meminta pemeriksaan data sebelum ulang | CLOSED |
| REC-B003 | File foto/direktori pengaman berpotensi berupa symlink ke luar direktori kelolaan | Validasi resolved parent dan penolakan symlink sebelum baca/tulis/cleanup; arsip tidak diekstrak ke filesystem | CLOSED |

Backup valid tidak sama dengan pemulihan biometrik: pengguna secara eksplisit memilih reenroll setelah restore. Bukti dan batas pada testing/stage-13.md.

REC-B004: native run awal menemukan klik demo Dashboard terlewat ketika Jobs menjalankan pemeriksaan sesi latar belakang. Klik kini memakai antrean single-flight Jobs, dan pemulihan remember-session startup dilewati jika sesi sudah diterima (demo). Tes memblokir poll dengan Event lalu membuktikan klik diantrikan/dijalankan satu kali. Satu kegagalan lain adalah prasyarat jendela Cocoa tidak aktif pada uji password; bukan assertion fokus input setelah aktivasi. Ketiga kasus native ulang PASS; run lengkap/native final dicatat pada bukti. Native awal 67 PASS/2 FAIL disimpan sebagai stage-13-native-initial.xml, tidak dilaporkan sebagai run lulus.

## Persiapan Windows Tahap14

DIST-B001: audit load sebelumnya memakai Jobs background single-flight sehingga klik saat session poll dapat dikembalikan False dan tampak tidak memuat apa pun. Permintaan eksplisit kini memakai antrean Jobs foreground; fixture mengunci poll lalu membuktikan tepat satu permintaan tertunda dan tabel termuat setelah poll selesai. Native awal68PASS/1FAIL disimpan, lalu diuji ulang setelah perbaikan.

Windows11 Parallels belum dapat start karena disk. Pengguna memilih menunda uji Windows; ini pembatas lingkungan, bukan hasil lulus installer. Tidak menghapus data untuk mengatasi kapasitas.

DIST-B002: Python3.11 Windows tidak menyediakan os.fchmod. Writer backup kini memeriksa ketersediaan API; mkstemp tetap mereservasi file, Pada kelanjutan Windows, ACL privat diterapkan eksplisit sebelum isi ditulis; tidak lagi mengandalkan izin folder tujuan. Tes codec mensimulasikan fchmod tidak tersedia tanpa mengubah platform global. Jalur POSIX tetap memakai fchmod0600.

DIST-B003: pemeriksaan Windows menemukan bahwa chmod/mode0600 bukan pembatas DACL Windows. restrict_path kini menetapkan DACL protected yang hanya memberi FullControl kepada pemakai proses dan SYSTEM pada foto/profil, marker, log dan cadangan (termasuk pengaman restore), sebelum data ditulis. Tes Windows menginspeksi ACL melalui PowerShell secara terpisah dan membuktikan grant Everyone eksplisit dihapus. Tes POSIX tetap memeriksa0600/0700. Symlink diuji terpisah karena akun Windows standar tanpa privilege tidak dapat membuatnya; kebijakan Windows tidak diubah untuk tes.

DIST-B004: kit awal tidak menyertakan pytest.ini. Pada mesin build dengan sumber CPython di prerequisites, pytest tanpa target ikut mengoleksi tes CPython dan gagal sebelum regresi proyek. Kit kini menyertakan pytest.ini dengan testpaths=tests, kontrak kit memeriksanya, dan perintah regresi Windows juga menyebut tests secara eksplisit. Bukti collection awal dipertahankan dan tidak dihitung sebagai hasil aplikasi.

DIST-B005: pada Windows kamera kedua dalam satu Mulai absensi dapat selesai startup setelah cooldown; latch kamera pertama tidak melindungi flow kedua yang belum pernah melihat peserta. Satu pemanggilan begin kini memiliki capture_group bertanda tangan; wajah yang masih tertahan pada kamera lain dalam kelompok yang sama menahan pencatatan berikutnya. Kelompok/terminal baru tetap mengikuti aturan cooldown yang sudah ada. Tes mengirim hasil kamera kedua pertama kali setelah61detik, lalu mensyaratkan absence pada kedua kamera sebelum OUT.

DIST-B006: tombol Pulihkan dapat mengabaikan klik ketika background session poll sedang aktif karena restore langsung return. Sekarang persiapan maintenance dimulai dan menunggu pekerjaan sebelumnya selesai; klik ganda saat persiapan ditolak. Tes UI menahan poll menggunakan Event dan membuktikan klik diterima serta pemulihan/login ulang selesai.

Windows awal:189PASS/3FAIL/1SKIP sebelum batas tiga kegagalan. Satu kegagalan demo berupa timeout saat build dan regresi berjalan bersamaan; pengulangan terpisah lulus. Empat tes terarah Windows setelah perbaikan lulus. Probe executable awal lulus Qt/native/spawn tetapi worker model gagal memulai; paket belum dinyatakan lulus. Diagnostik model hanya merekam tahap, jenis exception dan lokasi stack, tanpa pesan exception atau data wajah.

DIST-B007: executable awal gagal saat mengimpor onnx_cpp2py_export. Pemeriksaan PE membuktikan ONNX1.23.2 membutuhkan msvcp140 dengan nama hash di direktori saudara onnx.libs, sedangkan paket hanya memiliki salinan identik di pandas.libs. Finalizer build kini memakai collect_delvewheel_libs_directory resmi PyInstaller dan mempertahankan folder onnx.libs sebelum menghitung manifest. DLL berasal dari wheel yang sama, bukan unduhan DLL terpisah. Probe executable setelah staging lulus semua pemeriksaan termasuk worker AI/frame kosong. Tes finalizer memeriksa folder, checksum, pengulangan manifest dan penolakan .env privat.

DIST-B008: tes PDF Windows awal gagal karena pdfinfo/pdftotext belum tersedia pada mesin uji, lalu decoding default ANSI tidak cocok dengan keluaran UTF-8. Poppler di PATH proses tes dan encoding UTF-8 eksplisit menyelesaikannya:13tes ekspor Windows PASS,13macOS PASS. Poppler tidak masuk installer runtime.

DIST-B009 (28 Oktober 2026): proses setup kedua membaca byte lock Windows sebelum mencoba mengambil lock, sehingga dapat menghasilkan PermissionError mentah. Pemeriksaan ukuran berkas kini memakai fstat. Penguncian lintas proses dan tes setup terarah lulus pada Windows; pengulangan akhir 29 PASS/3 SKIP. CLOSED dalam cakupan tes tersebut.

DIST-B010 (28 Oktober 2026): repair installer otomatis ketika PostgreSQL kelolaan masih hidup gagal mengganti msvcp140.dll yang sedang digunakan. Installer kini menghentikan cluster bertanda miliknya melalui PrepareToInstall sebelum menyalin berkas; kegagalan penghentian membatalkan persiapan pemasangan. Database eksternal tanpa marker tidak dihentikan. Retest kondisi database hidup lulus, diikuti uninstall/reinstall dengan 80 anggota/5 akun/2.467 catatan tetap utuh. CLOSED dalam cakupan VM; hasil akhir pada docs/testing/stage-14-auto-20261028.md.

Percobaan awal installer otomatis juga mengembalikan kegagalan setup tanpa output child yang dapat dibaca. Pencatatan ExecAndLogOutput dan exit code diperjelas; pemasangan dari data kosong berikutnya berhasil. Penyebab pasti percobaan pertama tidak diklaim sudah terisolasi. Log percobaan awal tetap disimpan pada akun uji.

## Temuan performa Tahap15

PERF-B001, OPEN, High: benchmark produksi exact search pada10.000anggota x5embedding512D di Windows11 ARM64 Parallels/executable x64 menghasilkan p50=305,32ms, p95=364,83ms, maksimum957,27ms untuk1.000probe setelah5pemanasan. Target PRD-SEARCH100ms belum terpenuhi pada VM. Semua ID sintetis sesuai expected dan schema sementara dibuang. Profil berikutnya menemukan biaya pengelompokan dan TOAST. Kandidat0.14.2 menerapkan top-one exact serta storage PLAIN/target4096 dan migrasi penulisan ulang. Run produksi1.000probe menghasilkan p50=39,90ms,p95=50,92ms,p99=76,27ms,max=228,82ms;3query>100ms dan query pertama132,26ms. Semua ID sintetis sesuai dan schema sementara dihapus. p95 membaik, tetapi defect tetap OPEN untuk batas100ms pada seluruh query/query pertama. Periksa cache/I/O serta penjadwalan VM dan uji perangkat target; hasil AMD fisik belum disimpulkan. Bukti akhir: testing/evidence/stage-15-final-windows/search-scale.json. Bukti: testing/evidence/parallels-interactive-20261028/search-scale.json. Tahap15 belum ditutup.

Pembaruan21 Oktober2026: installer/akun standar/model/DB/credential lintas proses, ekspor/restore sintetis, probe offline dan repair/uninstall/reinstall lulus. Regresi penuh terakhir455PASS/2timeout/1SKIP; kedua kasus timeout lulus terpisah3/3 tanpa mengubah batas produksi. Symlink yang SKIP pada token standar lulus1/1 saat dijalankan terpisah dengan hak SYSTEM yang sudah tersedia. Kamera frozen awal4FAIL/3PASS saat USB tidak terdeteksi; recheck setelah pengguna menghubungkan kembali USB7/7PASS. Kegagalan pembukaan pertama laptop belum terisolasi sepenuhnya, tetap observasi/soak. Tidak menyatakan satu run regresi penuh hijau atau review manual pengguna sudah diterima.

DIST-B011 (28 Oktober2026), CLOSED pada lingkungan build Windows: build ulang gagal ketika PyInstaller menghapus `dist/StarGate/_internal/postgresql/licenses/PostgreSQL.txt` yang memiliki atribut READONLY. Persiapan keluaran build sekarang menolak tautan/reparse point dan menghapus atribut hanya-baca pada berkas dalam folder hasil build miliknya sebelum PyInstaller menggantinya. Berkas lisensi tetap disertakan. Pengulangan build berhasil; fixture Windows asli membuktikan berkas hanya-baca dapat ditulis setelah persiapan. Data/config pengguna tidak disentuh. Bukti `testing/evidence/stage-15-final-windows/build-recovery.json`; log kegagalan awal dan hasil ulang disimpan terpisah. Pengulangan memakai cache yang tersedia tanpa --clean; PyInstaller tetap memeriksa/membangun ulang tahap yang diperlukan, kemudian runtime/manifest disusun kembali.


CAM-B004 (28 Oktober2026), OPEN, Medium: preview kamera0 dari runtime0.14.2 di Parallels pertama kali gagal tanpa frame; proses dan memori berhasil dilepas. Inventaris Windows tetap menunjukkan FaceTime HD Camera OK. Probe OpenCV source dapat membaca640x480 dan1280x720; pengulangan helper frozen setelah penambahan trace metadata lulus preview/reopen30frame1280x720 serta indeks tak tersedia. Tidak ada perubahan kode capture produksi di antara kedua percobaan. Penyebab awal belum terisolasi, sehingga tidak menandai kestabilan kamera selesai. Bukti pertama `testing/evidence/stage-15-final-windows/cameras-first-attempt.json`; hasil ulang `testing/evidence/stage-15-final-windows/cameras.json`. Lanjutkan uji buka/tutup, putus-sambung dan soak pada perangkat target; frame/foto tidak disimpan.
