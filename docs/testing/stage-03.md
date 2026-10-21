# Hasil Tahap 3 - Database, migrasi, repository, audit

Tanggal: 18 Oktober 2026 (Asia/Jakarta). Status: **Lulus; pengguna menyetujui review dan mengarahkan lanjut ke Tahap 4 pada 18 Oktober 2026**.

## Checklist implementasi

- [x] Delapan tabel inti PRD beserta seluruh kolom wajib, tipe dan relasi dibuat.
- [x] Audit, penugasan shift, izin, kalender dan lokasi ditambahkan sesuai baseline keputusan.
- [x] Foreign key RESTRICT, unique case-insensitive, check constraint, timestamp timezone-aware, indeks dan soft delete disiapkan.
- [x] Repository ORM untuk group/member/embedding/shift/device/user/settings/attendance/audit dan batas transaksi dibuat.
- [x] Seed 12 setting + lokasi default idempotent; tidak menimpa konfigurasi yang diubah.
- [x] Bootstrap Super Admin interaktif tanpa password bawaan; bcrypt cost 12, advisory lock dan audit atomik.
- [x] Audit append-only untuk akun aplikasi, tanpa payload sensitif; terpisah dari log diagnostik.
- [x] Migrasi Alembic statis, account aplikasi/migrator terpisah, revision metadata read-only bagi aplikasi.
- [x] Integrasi PostgreSQL/pgvector nyata, regresi, rollback, constraint, downgrade/upgrade terisolasi dan restart diuji.
- [x] Panduan CLI, schema, keputusan dan plan diperbarui.
- [x] Pengguna melakukan review dan menyatakan lanjut ke Tahap 4, 18 Oktober 2026.

## Lingkungan dan perubahan aktual

Python 3.11.17, PostgreSQL 17.11, extension pgvector 0.8.7, SQLAlchemy 2.0.55, Alembic 1.20.0, psycopg 3.3.6 pada macOS arm64. Dependency lock tidak berubah.

Revision `0001_stargate` diterapkan ke stargate_dev dan stargate_test pada schema public. Ada 13 tabel aplikasi ditambah alembic_version. Saat pemeriksaan akhir, masing-masing hanya mempunyai 12 settings, 1 lokasi dan 1 audit seed; member, embedding, attendance, users dan data operasional lain masih kosong. Akun nyata tidak dibuat otomatis.

## Hasil pengujian

| ID | Cakupan dan expected | Hasil aktual | Status | Bukti |
|---|---|---|---|---|
| DB-01 | Migrasi dari schema kosong, metadata/tipe/index/constraint sesuai ORM, round-trip downgrade/upgrade | Semua 13 tabel terbentuk dan metadata comparison kosong; downgrade/upgrade hanya schema sementara | PASS | test_database.py, [JUnit](evidence/stage-03-tests.xml) |
| DB-02 | Scope pemeriksaan schema tepat | Tabel public tidak menyamarkan tabel/kolom uji yang hilang; missing_tables dan missing_columns terdeteksi | PASS setelah perbaikan | Regression test migrasi |
| DB-03 | Seed dapat diulang tanpa overwrite atau audit tambahan | Seed awal 12 settings + 1 lokasi; ulang 0+0; threshold .65 yang diubah pada fixture tetap .65 | PASS | Integration dan [deployment](evidence/stage-03-deployment.json) |
| DB-04 | Transaksi dan audit atomik | Error setelah create membatalkan entity dan audit; pelanggaran FK/unique/check tidak meninggalkan row parsial | PASS | Integration tests |
| DB-05 | Relasi, soft delete dan riwayat | Member nonaktif, history tetap; snapshot group pada attendance tidak berubah ketika group member berpindah; delete group direferensikan ditolak | PASS | Integration tests |
| DB-06 | Vector 512D dan pencarian identitas | Round-trip valid; cosine identik/opposite benar; lima sudut tidak menduplikasi member dalam hasil; model berbeda dan member nonaktif dikecualikan | PASS | Integration tests |
| DB-07 | Invalid data ditolak | Vector 511/zero/NaN/Inf, grace negatif, shift nol, FPS nol, range tanggal terbalik, plaintext password dan role invalid ditolak | PASS | Integration + validation tests |
| DB-08 | Hak database minimum | Audit UPDATE/DELETE ditolak SQLSTATE 42501; member/user hard DELETE dan perubahan revision ditolak | PASS | Integration tests |
| DB-09 | Bootstrap aman dan konkurensi | Password tersimpan bcrypt; dua bootstrap bersamaan hanya menghasilkan satu Super Admin; bootstrap kedua tidak menimpa akun | PASS | Integration tests, schema sementara |
| DB-10 | Audit privasi | Arbitrary payload/password/embedding ditolak; setting old/new hanya whitelist yang tervalidasi; tidak ada password di audit | PASS | Integration tests |
| DB-11 | Parameterisasi dan koneksi gagal | SQL-like search tidak mengeksekusi perintah; wildcard diperlakukan literal; port tidak tersedia memberi pesan aman tanpa password | PASS | Integration tests |
| DB-12 | Persistensi setelah restart PostgreSQL | Digest snapshot, jumlah record, vector dan waktu event sama sebelum/sesudah; postmaster start time berubah; schema sementara dibersihkan | PASS | [Persistence](evidence/stage-03-persistence.json) |
| DB-13 | Deployment lokal dan health check akun aplikasi | dev/test at_head=true, schema_valid=true, 13 tabel/kolom lengkap; public tanpa data contoh bisnis | PASS | [Status](evidence/stage-03-status.json) |
| DB-14 | Regresi keseluruhan | 75 tests, 0 failure/error/skip; 30 real DB integration + 45 test lain | PASS | [JUnit](evidence/stage-03-tests.xml) |
| DB-15 | Coverage >=80% | app + database 91.36% (1079/1181 statements), tanpa exclusion baru | PASS | [Coverage](evidence/stage-03-coverage-summary.json) |
| DB-16 | Review pengguna | Pengguna menyatakan review OK dan dapat dilanjutkan | PASS | Persetujuan chat 18 Oktober 2026 |

Bootstrap dan task native memiliki batas pengukuran coverage dari Tahap 2 (subprocess/Qt native thread tidak seluruhnya terukur oleh parent). Tidak ada test database yang digantikan SQLite atau mock untuk klaim di atas.

## Debug yang ditemukan dan diselesaikan

1. Review autogenerate menemukan metadata alembic_version ikut dianggap tabel yang perlu dihapus. Perintah itu dibuang sebelum migrasi diterapkan; env autogenerate mengecualikan metadata Alembic. Migrasi final menggunakan DDL statis dan round-trip diuji pada schema sementara.
2. Setelah public berisi tabel, test akhir sempat 74 PASS / 1 FAIL: introspeksi tanpa schema eksplisit dapat melihat fallback public sesudah tabel uji di-drop. Perbaiki schema_status dan test agar selalu menyebut schema tepat; tambahkan regresi tabel/kolom hilang dengan public masih tersedia. Run akhir 75/75 PASS; tidak ada tabel public yang dihapus oleh test.
3. Peringatan Alembic path_separator dihilangkan dengan konfigurasi path_separator=os; tidak ada dependency upgrade.

## Uji mandiri

Dari folder proyek:

```sh
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/manage_database.py check
.venv/bin/python scripts/manage_database.py check --database test
```

- [ ] Kedua check exit 0, at_head true dan schema_valid true.
- [ ] application_table_count 13; missing_tables [] dan missing_columns {}.
- [ ] Opsional: jalankan `.venv/bin/python -m pytest --run-db`; seluruh 75 tes harus lulus, tanpa skipped DB tests.
- [ ] Opsional: uji restart dengan `.venv/bin/python scripts/smoke_database_persistence.py --restart-local` ketika tidak ada aktivitas DB lain; kedua check harus PASS.
- [ ] Tinjau [struktur database](../database.md) dan batas tahap berikut.
- [ ] Nyatakan hasil review atau kirim error yang sudah disanitasi; jangan kirim `.env` atau password.

Bootstrap akun awal tersedia melalui `.venv/bin/python scripts/manage_database.py bootstrap-admin` di terminal interaktif, tetapi opsional untuk review. Perintah ini membuat akun nyata pada development; tidak perlu dilakukan hanya untuk melihat schema siap.

## Batas tahap

- Tampilan GUI tetap pratinjau; login, role/otorisasi aksi UI, CRUD screen dan seluruh alur user story belum selesai.
- Repository adalah fondasi persistensi, bukan bukti AC registrasi wajah/absensi/liveness telah lulus.
- Audit login/user changes lain baru disambungkan ketika fitur dibangun pada Tahap 4 dan seterusnya. US-029 lengkap belum ditandai PASS.
- Sumber izin/kalender dan penugasan tersedia sebagai tabel; overlap jadwal, grace/late/early leave, cooldown, check-in/out state, Absent dan On Leave calculation masih tahap terkait.
- Tidak ada wajah nyata/RTSP credential di dev/test. Retensi dan storage secret perangkat tetap diselesaikan sebelum penggunaan data nyata/perangkat terkait.
- Audit dilindungi dari akun aplikasi, bukan dari administrator database. Backup/restore produk tetap Tahap 13.
- Pengujian downgrade/drop dilakukan hanya pada schema unik stage3_test_*; tidak ada perintah reset/downgrade massal dalam CLI pengguna.
- SLA 10.000 member, accuracy/liveness dan Windows belum diukur pada tahap ini.

Langkah berikut: Tahap 4 Authentication, Authorization dan User Management, setelah review tahap ini diterima.

Catatan versi: jumlah 13 tabel dan revision 0001 di atas adalah hasil Tahap 3 saat diuji; Tahap 4 menambahkan migrasi 0002_auth dan tabel auth_sessions.
