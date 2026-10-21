# Hasil Tahap 4 — login, session, role dan pengguna

Tanggal: 18 Oktober 2026, macOS arm64 / Python 3.11.17. Status: **Lulus; pengguna menyelesaikan review dan mengizinkan Tahap 5 pada 18 Oktober 2026 setelah perbaikan AUTH-B004**.

## Implementasi

- [x] Login/logout, bcrypt cost 12, perubahan password, forced change akun awal/baru/reset.
- [x] Idle timeout 15 menit; 5 login gagal mengunci 15 menit. Kegagalan dan audit tetap dikomit ketika login ditolak.
- [x] Token sesi/remember acak 256 bit; SHA-256 di PostgreSQL, token mentah di native OS credential store, tidak di berkas biasa.
- [x] Ingat saya 30 hari, terpisah dari sesi interaktif idle 15 menit / absolut 24 jam. Tutup normal mencabut sesi interaktif; remember bertahan.
- [x] Token dicabut saat logout, timeout, password change/reset, perubahan akun/peran atau nonaktif. Token remember tidak bisa digunakan sebagai sesi interaktif dan sebaliknya.
- [x] Otorisasi layanan serta navigasi berdasarkan akun/peran terkini. Viewer hanya Reports; Users hanya Super Admin.
- [x] Form pengguna: list/create/edit/nonaktif/reset. Username unik tanpa membedakan kapital; password sementara tampil sekali dan wajib diganti.
- [x] Bootstrap GUI/CLI tanpa akun bawaan; lindungi Super Admin terakhir dan cegah nonaktif/demote akun sendiri. Mutasi auth diserialkan secara transaksional.
- [x] Migrasi tambahan 0002_auth; revision 0001 tetap; 14 tabel aplikasi. Database tidak otomatis dimigrasikan oleh GUI.
- [x] I/O, bcrypt dan keyring pada worker; penutupan menunggu transaksi/worker selesai. Expected errors tidak membocorkan detail internal.
- [x] Panduan dan keputusan diperbarui; dependency keyring 25.7.0 dikunci, pip check lulus.
- [x] Pengguna menyelesaikan review dan mengizinkan Tahap 5, 18 Oktober 2026.

## Hasil dan bukti

| ID | Skenario | Hasil | Bukti |
|---|---|---|---|
| AUTH-01 | Login valid/invalid/unknown/inactive; username SQL-like; mandatory change | PASS | test_auth.py, test_session_ui.py |
| AUTH-02 | Lima kegagalan, paralel tanpa lost update, lock dan tepat batas unlock | PASS | PostgreSQL nyata + clock terkendali |
| AUTH-03 | Idle sebelum/tepat batas; input sesudah batas tidak menghidupkan sesi; background tidak menyegarkan | PASS | Service + UI test |
| AUTH-04 | Hash bcrypt, token hash, DTO repr aman, audit tanpa password/token | PASS | DB assertions; test_credentials.py |
| AUTH-05 | Sesi/remember berbeda; restart, expiry 30 hari, logout/forget/timeout revocation | PASS | Service/UI integration |
| AUTH-06 | Keychain macOS lintas proses save → proses baru resume → logout → clear | PASS | [JUnit Keychain](evidence/stage-04-keychain.xml), token sintetis di scope unik |
| AUTH-07 | Backend ditolak/locked; tidak ada plaintext fallback; login password masih bisa | PASS | Credential store + UI tests; backend gagal terkontrol |
| AUTH-08 | Seluruh matriks empat role dan akses langsung ke CRUD tanpa izin | PASS | test_full_permission_matrix_enforced_at_service + native UI |
| AUTH-09 | User create/edit/nonaktif, duplikat case-insensitive, reset dan forced change; sesi lama ditolak | PASS | Service + UI; audit create/update/deactivate/reset |
| AUTH-10 | Bootstrap hanya sekali; akun sendiri/SA terakhir terlindungi; dua bootstrap bersamaan | PASS | Stage 3 concurrency + Stage 4 regression/UI |
| AUTH-11 | DB gagal memblokir sesi; close saat login/diagnostic berjalan; event loop tetap merespons | PASS | UI + worker regression |
| AUTH-12 | Migrasi schema kosong/downgrade/upgrade, metadata sesuai, dev/test revision dan kolom lengkap | PASS | [Deployment](evidence/stage-04-deployment.json), regresi migrasi |
| AUTH-13 | GUI macOS native, termasuk bootstrap/reset dan empat role | PASS: 10 tes | [JUnit native](evidence/stage-04-ui-native.xml) |
| AUTH-14 | Regresi keseluruhan + coverage >=80% | PASS: 100/100, 0 skip, coverage 91,45% (1850/2023 statement) | [JUnit](evidence/stage-04-tests.xml), [Coverage](evidence/stage-04-coverage-summary.json) |

Bukti visual: [Login](evidence/stage-04-login.png), [Dashboard](evidence/stage-04-dashboard.png), [Users](evidence/stage-04-users.png), [Viewer](evidence/stage-04-viewer.png). Screenshot dibuat tanpa password atau token. Seluruh akun pengujian dibuat dalam schema unik database test dan dibersihkan; tidak membuat akun pengguna nyata otomatis.

Pengujian waktu menggunakan clock terkendali untuk tepat batas 15 menit/30 hari; tidak mengklaim observasi selama 30 hari. Uji Keychain memakai dua proses Python terpisah dan database PostgreSQL nyata; uji UI remember juga menutup lalu membuat jendela baru. Windows Credential Manager belum diuji pada Windows nyata (Tahap 14).

## Debug dan uji ulang

- Native macOS pertama: 8 PASS / 1 FAIL; dialog reset yang dibuka melalui exec di callback hasil worker memicu timeout/nested event loop. Reproduksi terisolasi sempat macet dan dihentikan. Reset dan bootstrap kini memakai open + callback finished, field rahasia dibersihkan setelah dialog ditutup. Uji kasus gagal lulus, lalu seluruh 10 tes native lulus. Tidak ada data public yang dipakai untuk reproduksi. Satu schema sintetis yang tertinggal akibat proses dihentikan telah divalidasi fixture-nya dan dibersihkan secara spesifik; [bukti pembersihan](evidence/stage-04-cleanup.json).
- Review menemukan keyring yang terkunci dapat menghalangi login password biasa. Normal login sekarang melepaskan marker lama dan tetap mengautentikasi password; jika remember gagal disimpan, grant baru dicabut dan sesi biasa tetap tersedia. Regresi backend unavailable lulus.
- Pemeriksaan semua sesi berjalan di worker, sehingga periode idle dan penutupan aplikasi tidak melakukan query/bcrypt pada thread GUI. Error transaksi tidak dianggap sukses.

## Uji mandiri sebelum Tahap 5

Jalankan dari folder proyek:

```sh
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/manage_database.py check
.venv/bin/python main.py
```

- [ ] Check menampilkan revision 0002_auth, at_head/schema_valid true, application_table_count 14.
- [ ] Pilih **Buat Super Admin pertama** jika belum pernah membuat akun. Isi username/nama/password awal, lalu masuk. Jika akun sudah ada, gunakan akun tersebut; bootstrap kedua harus ditolak.
- [ ] Setelah masuk pertama kali, ganti password awal dengan password berbeda (12–72 byte UTF-8). Dashboard terbuka setelah perubahan berhasil.
- [ ] Klik **Pengguna** → **Form akun baru**, isi nama/username/password awal dan pilih Viewer; simpan. Ulangi untuk Admin/Operator jika ingin memeriksa matriks lengkap.
- [ ] Keluar lalu masuk sebagai Viewer; ganti password awal. Hanya **Laporan** yang terlihat. Halaman laporan masih pratinjau, belum menghasilkan data/ekspor.
- [ ] Masuk kembali sebagai Super Admin. Ubah nama/peran akun uji dan muat ulang; perubahan tersimpan. Coba username duplikat; harus ditolak.
- [ ] Pilih akun uji, **Reset password**. Salin secara pribadi sebelum dialog ditutup; password tampil sekali. Password lama ditolak, sementara bisa masuk dan wajib diganti. Jangan mengirim password lewat chat.
- [ ] Hilangkan centang **Akun aktif** untuk akun uji, lalu simpan. Akun tersebut tidak bisa masuk; aktifkan kembali bila dibutuhkan. Akun sendiri tidak boleh dinonaktifkan/demote.
- [ ] Centang **Ingat saya**, masuk, tutup aplikasi normal lalu buka kembali: masuk kembali lewat token. Jika macOS meminta akses Keychain, izinkan agar fitur ini dapat diuji.
- [ ] Klik **Keluar akun**, buka ulang: layar login tampil. Jika Keychain tidak tersedia, pesan menjelaskan bahwa sesi biasa tetap dapat digunakan.
- [ ] Opsional: gunakan akun uji untuk salah password lima kali. Akun terkunci; tunggu 15 menit sebelum mencoba lagi. Jangan memakai satu-satunya Super Admin untuk percobaan ini.
- [ ] Opsional: biarkan aplikasi tanpa input 15 menit (timer/progress tidak dihitung): konten terlindungi ditutup dan login diminta lagi.
- [ ] Pindah halaman saat diagnostik berjalan, coba sukses/error/batal; UI tetap merespons. Tutup saat proses berjalan, buka kembali.
- [ ] Sampaikan hasil review dan izin lanjut, atau langkah reproduksi jika ada kendala.

Akun yang Anda buat untuk uji mandiri merupakan data development nyata dan dipertahankan. Tidak ada pembersihan akun development otomatis. Menonaktifkan akun menjaga riwayat dan dapat dibalik oleh Super Admin.

## Batas tahap

Modul anggota/grup/shift/perangkat, kamera, AI, absensi, laporan, settings UI dan backup belum operasional. Pengujian role pada modul tersebut memeriksa guard akses dan navigasi; aksi bisnisnya diuji lagi saat modul dibangun. US-029 masih parsial sampai seluruh fitur audit dan tampilan inspeksi selesai. SLA, retensi data operasional dan Windows tetap tahap terkait.

Saat DB tidak tersedia, UI menutup sesi lokal pada pemeriksaan berikut dan menolak operasi. Jika server tidak dapat menerima pencabutan saat logout/close, sesi yang belum tercabut tetap tunduk expiry di server; marker/token lokal dihapus saat logout. Tidak ada mode offline atau data bisnis yang disimpan dengan feedback sukses palsu.

Langkah berikut: review/uji mandiri Tahap 4, kemudian Tahap 5 setelah persetujuan pengguna.

Run akhir: STARGATE_TEST_NATIVE_KEYCHAIN=1 .venv/bin/python -m pytest --run-db --cov=app --cov=database --cov-fail-under=80: 100 PASS dalam 53,33 detik, 0 failure/error/skip, coverage 91,45%. Tanpa flag native Keychain, 1 tes OS tersebut memang dilewati; tanpa --run-db, tes DB juga dilewati. Coverage mencakup seluruh app + database, tanpa exclusion baru. Entry point diuji dalam subprocess dan tidak seluruhnya terukur oleh parent; ini membuat coverage bootstrap dilaporkan 0%, bukan berarti startup tidak diuji.

## Perbaikan setelah uji mandiri — fokus input password

Pengguna menemukan kedipan dan hilangnya fokus saat forced change. Pemeriksaan sesi satu detik sempat ikut menonaktifkan seluruh formulir. AUTH-B004 memperbaiki mode busy: pemeriksaan rutin tidak lagi mengubah enabled state widget, sementara operasi simpan/login tetap mencegah pengiriman ganda. Pengamanan sesi dan timeout tetap aktif.

Reproduksi sebelum fix: FAIL pada assertion input tetap enabled. Sesudah fix: dua skenario offscreen PASS, meliputi tiga input pada login pertama serta ganti password biasa. Bukti: [regresi fokus](evidence/stage-04-focus-regression.xml). Dua skenario macOS native juga PASS: [bukti native](evidence/stage-04-focus-native.xml). Regresi lengkap **102 PASS, 0 failure/error/skip**, coverage **91.47%**: [JUnit](evidence/stage-04-focus-tests.xml), [ringkasan](evidence/stage-04-focus-summary.json).

Untuk uji ulang, tutup proses aplikasi yang masih berjalan lalu jalankan `.venv/bin/python main.py`. Masuk menggunakan akun yang sudah Anda buat; tidak perlu bootstrap atau reset database. Pada halaman ganti password, ketik dan tunggu beberapa detik pada setiap input. Fokus dan isi ketikan harus bertahan, lalu simpan password baru. Jangan mengirim isi password ke chat.

Persetujuan penutupan: pengguna menyatakan “sudah saya review dan sudah OK, bisa dilanjutkan” setelah uji mandiri dan perbaikan fokus input. Tahap 5 diizinkan; tidak menganggap seluruh fitur V1 sudah selesai.
