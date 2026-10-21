# Hasil Tahap 5 — grup, shift dan administrasi anggota

Tanggal: 18 Oktober 2026. Status: **lulus dan disetujui pengguna**. Pengguna menyetujui hasil setelah perbaikan ADM-B003 dan mengizinkan Tahap 6. Tahap 4, termasuk perbaikan fokus AUTH-B004, sudah disetujui pengguna.

## Implementasi

- [x] CRUD grup, nama unik case-insensitive, jumlah anggota dan penolakan hapus jika direferensikan.
- [x] CRUD shift, ketelitian menit, validasi grace terhadap durasi, shift lintas hari; jadwal yang direferensikan dilindungi.
- [x] Daftar anggota 10/25/50 per halaman, pencarian literal nama/ID, filter grup/status, detail dan edit field wajib/opsional.
- [x] Foto profil pengganti divalidasi, disalin privat dan tidak hilang jika berkas sumber dipindah; berkas baru dibuang bila transaksi gagal.
- [x] Form registrasi baru disiapkan. Save/capture tetap tidak aktif sampai capture/embedding tersedia; service juga menolak penyelesaian registrasi.
- [x] Konfirmasi nonaktif, soft delete, audit mutasi, riwayat event tersimpan serta snapshot grup historis dipertahankan.
- [x] Penugasan shift bertanggal inklusif, akhir opsional, pencegahan overlap dan penutupan rentang tanpa mengeluarkan attendance yang ada.
- [x] Hak layanan dan UI: grup/shift/assignment Super Admin/Admin; Members Super Admin/Admin/Operator; Viewer ditolak.
- [x] Migrasi 0003_admin menambahkan revision untuk menolak stale edit. Dev/test dimigrasikan tanpa mengganti akun/password/sesi atau jumlah data yang sudah ada.
- [x] Mode demo opt-in terisolasi: 25 anggota, dua grup/shift, foto bidang warna, satu event sintetis; empat role. Tidak menambah member development atau memakai wajah nyata.
- [x] Regresi 147 PASS tanpa skipped, 21 tes GUI/auth native PASS, coverage 93,23%; bukti dicatat.
- [x] Pengguna menyelesaikan review dan mengizinkan Tahap 6.

## Lingkungan dan bukti

macOS arm64, Python 3.11.17, PyQt6 6.11.0 / Qt 6.11.2, PostgreSQL 17.11 + pgvector 0.8.7, SQLAlchemy 2.0.55. Tidak ada dependensi baru; lock tidak berubah. Query data tetap ORM terparameterisasi. Revision lama 0001/0002 tidak diedit; 14 tabel aplikasi total.

| ID | Cakupan | Hasil saat ini | Bukti |
|---|---|---|---|
| ADM-01 | Group create/read/update/delete, duplikat kapital, FK/historical protection, stale edit, actor audit | PASS | test_administration.py |
| ADM-02 | Shift pagi/malam, jam sama, minute precision, grace negatif/boolean/durasi, CRUD dan referensi | PASS | Service + validation + UI |
| ADM-03 | Pagination awal/tengah/akhir, offset stale, empty/literal SQL/wildcard, filter group/active | PASS | Service + UI |
| ADM-04 | Member ID/nama/group wajib, email/phone/position, Unicode, duplikat rollback, perpindahan group historis | PASS | Service + validation + UI |
| ADM-05 | PNG/JPEG, size/resolution bounds, private copy, missing/corrupt input, rollback tanpa orphan baru | PASS | Photo validation/integration |
| ADM-06 | Soft delete cancel/confirm; member/embedding/event tetap; pencarian embedding mengecualikan nonaktif | PASS | Service + UI; vector sintetis saja |
| ADM-07 | Assignment inclusive/nonoverlap/open end, next-day replacement, concurrent submissions, historical end guard | PASS | Service + UI |
| ADM-08 | Semua role, akses langsung mutasi, revoked token, izin Operator edit vs assignment | PASS | Service matrix + UI |
| ADM-09 | New registration tidak bisa diselesaikan dari UI maupun service | PASS | Gate Tahap 8 diuji |
| ADM-10 | Demo seed/empat role, cleanup normal/exception, proses CLI membuka/menutup; public unchanged | PASS | test_administration_demo.py |
| ADM-11 | Migrasi kosong/downgrade/upgrade/model comparison; preservation dev/test | PASS | [Deployment](evidence/stage-05-deployment.json), regression schema |
| ADM-12 | UI native macOS | PASS: 21 tes GUI administrasi + auth macOS | [Native gabungan](evidence/stage-05-ui-and-auth-native.xml) |
| ADM-13 | Regresi keseluruhan + coverage >=80% | PASS: 147/147, 0 skip; coverage 93,23% (2728/2926 statement) | [JUnit](evidence/stage-05-tests.xml), [Summary](evidence/stage-05-summary.json) |

Bukti visual: [Grup](evidence/stage-05-groups.png), [Shift](evidence/stage-05-shifts.png), [Anggota](evidence/stage-05-members.png), [Detail](evidence/stage-05-member-detail.png). Semua screenshot memakai data sintetis. Angka/label pengujian riwayat tidak berasal dari scan wajah nyata.

## Debug

1. Pengujian awal pagination menemukan closure mengubah offset sehingga variabel terbaca sebagai local sebelum diisi. Pakai page_offset lokal terpisah; boundary/empty tests lulus.
2. Review native menemukan filter group terpotong dan tombol pertama salah baris karena layout kosong dianggap false. Pemilihan layout kini memeriksa None secara eksplisit; lebar filter dibatasi agar label terbaca; tujuh native UI tests diulang lulus.
3. Regresi gabungan awal: 142 PASS / 1 FAIL. Klik Simpan Pengguna dapat terlewat jika polling sesi sedang berjalan. Jobs kini mengantrekan satu aksi interaktif setelah polling dan menahan pengiriman ganda; antrean dibuang jika sesi gagal/berakhir. Dua regression cases khusus (poll sukses/gagal) ditambahkan. Seluruh 14 tes auth UI lulus pada uji ulang sebelum run akhir.
4. Foto lama tetap disimpan sampai retensi ditetapkan; ini keputusan perlindungan data, bukan klaim garbage collection sudah tersedia. Salinan baru yang gagal commit dibersihkan dan pengujian memastikan row/audit tetap konsisten.

## Uji mandiri: data kerja

Tutup aplikasi versi lama, lalu jalankan dari folder proyek:

```sh
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/manage_database.py check
.venv/bin/python main.py
```

- [ ] Check: current/expected revision terbaru (0004_devices setelah Tahap 6); at_head/schema_valid true; 14 tabel, missing kosong.
- [ ] Masuk memakai akun yang sudah dibuat. Tidak perlu bootstrap/reset database/password.
- [ ] **Grup**: buat grup uji, edit nama/deskripsi, muat ulang dan pilih kembali untuk memverifikasi persistensi. Coba nama kosong dan duplikat kapital. Hapus grup kosong dengan konfirmasi; klik Tidak untuk menguji pembatalan.
- [ ] **Shift**: buat shift uji 08:00–17:00, grace 10; edit sebelum direferensikan. Buat 20:00–04:00 dan lihat label lintas hari. Jam sama atau grace >=durasi membuat Simpan tidak aktif.
- [ ] Tutup/buka aplikasi: grup dan shift kerja tetap tersimpan.
- [ ] Buka **Anggota**. Jika belum ada anggota, daftar kosong adalah hasil yang benar. Form registrasi baru tersedia, tetapi penyimpanan/capture belum aktif sampai Tahap 8.

Akun Operator tidak memperoleh menu grup/shift; Viewer hanya Reports. Administrasi yang dilakukan pada aplikasi normal merupakan data development nyata dan tidak dibersihkan otomatis.

## Uji mandiri lengkap: demo terpisah

Gunakan demo untuk menguji anggota, relasi, riwayat dan pagination sebelum registrasi wajah tersedia:

```sh
.venv/bin/python scripts/demo_administration.py
```

Jendela bertanda **MODE UJI SINTETIS**. Akun Super Admin uji dimasukkan otomatis hanya pada schema demo. Tidak ada password demo yang perlu dimasukkan. Tutup jendela untuk menghapus data demo; buka kembali untuk memulai dari awal. Jangan memakai force kill untuk pengujian cleanup normal.

- [ ] Buka **Anggota**: 25 anggota, 10 per halaman. Coba Berikutnya/Sebelumnya, ukuran 25/50, cari nama/ID, hasil kosong, filter grup/status dan Muat ulang.
- [ ] Pilih anggota. Gulir halaman ke bawah untuk formulir, penugasan shift dan riwayat. Ubah nama, email, telepon/jabatan dan grup, lalu simpan. Pilih lagi untuk memastikan perubahan.
- [ ] Kosongkan ID/nama atau pilih placeholder grup: Simpan tidak aktif. Coba ID anggota lain atau email invalid: service menolak tanpa perubahan parsial.
- [ ] Ganti foto menggunakan berkas [foto uji sintetis](../../resources/samples/profile-test.png), lalu simpan. Ini bidang warna, bukan wajah. Coba berkas rusak/tidak ada: ditolak dengan pesan aman.
- [ ] Anggota pertama mempunyai satu event IN sintetis. Pindahkan grup: group pada event lama tetap Kelas 10A.
- [ ] Klik **Nonaktifkan anggota**, pilih Tidak: tetap aktif. Ulangi dan pilih Ya: anggota hilang dari filter Aktif, muncul di Nonaktif; riwayat tetap ada.
- [ ] Coba hapus grup yang direferensikan, termasuk anggota nonaktif: ditolak. Buat grup baru kosong, lalu hapus: berhasil.
- [ ] Pilih Anggota Uji 02 (tanpa penugasan). Pilih shift dan tanggal mulai, kosongkan akhir melalui **Tanpa tanggal akhir**, lalu **Tetapkan shift**. Penugasan muncul.
- [ ] Coba assignment lain pada rentang yang sama: ditolak. Pilih penugasan lama dan akhiri pada tanggal tertentu; assignment berikut boleh mulai hari sesudahnya.
- [ ] Coba ubah jam/grace atau hapus shift yang sudah direferensikan: ditolak. Untuk jadwal pengganti, buat shift baru dan penugasan baru.
- [ ] Klik **Form registrasi baru**, isi field wajib dan pilih foto sintetis. Registrasi tetap tidak bisa disimpan/capture: ini gerbang yang disengaja sampai Tahap 8.
- [ ] Ketik sambil menunggu beberapa detik pada pencarian/form; pemeriksaan sesi tidak boleh membuat input berkedip atau kehilangan fokus. Coba navigasi dan close saat proses berjalan.
- [ ] Tutup demo, buka kembali: perubahan demo hilang dan 25 anggota awal kembali. Data pada aplikasi normal tetap sama.

Mode role lain:

```sh
.venv/bin/python scripts/demo_administration.py --role admin
.venv/bin/python scripts/demo_administration.py --role operator
.venv/bin/python scripts/demo_administration.py --role viewer
```

Admin dapat mengelola grup/shift/anggota/assignment; Operator dapat melihat/edit/nonaktifkan anggota dan membaca riwayat tetapi tidak mengelola grup/shift/assignment. Viewer tidak memiliki menu ketiganya.

## Batas tahap dan gerbang

- Tidak ada capture kamera, embedding/liveness nyata, atau penyelesaian registrasi baru. Foto profil saja tidak mengaktifkan registrasi.
- Riwayat tersimpan sudah dapat dibaca (50 event terbaru dengan total jelas); pencatatan event/late/early leave dan suara scan tetap Tahap 10. Riwayat uji bukan bukti integrasi kamera.
- Audit mutasi disimpan atomik, tetapi layar inspeksi audit lengkap tetap Tahap 13. SLA, Windows dan dataset wajah nyata belum dinyatakan lulus.
- Pengujian menggunakan schema unik stage3_test_* di database test. Migrasi dev/test menambah kolom revision dan tidak membuat/menghapus akun/member operasional.
- Revision adalah guard layanan untuk aksi administratif yang tersedia; layanan mutasi baru harus mempertahankan mekanisme ini. Tidak mengklaim setiap penulis SQL eksternal otomatis mengikuti guard aplikasi.
- Foto pengganti disimpan privat di .local/member_photos, maksimal 1024px. Foto sebelumnya dipertahankan sampai kebijakan retensi/pembersihan ditetapkan. Tidak ada pengambilan wajah nyata otomatis.
- Mode demo menghapus schema/aset saat normal close atau exception Python yang ditangani. Force kill/crash mesin dapat meninggalkan schema uji; jangan menghapus schema public untuk membersihkannya.

Tahap 6 (perangkat dan pipeline kamera) menunggu review/uji mandiri Tahap 5 serta persetujuan pengguna.

Run akhir: STARGATE_TEST_NATIVE_KEYCHAIN=1 .venv/bin/python -m pytest --run-db --cov=app --cov=database --cov-fail-under=80: **147 PASS** dalam 99,63 detik, tanpa failure/error/skip. Native gabungan **21 PASS** dalam 49,29 detik. Tanpa flag native Keychain, satu test OS memang dilewati; tanpa --run-db, test DB juga dilewati. Coverage seluruh app + database 93,23%, tanpa exclusion baru. Subprocess entry point tidak seluruhnya terukur oleh parent, sehingga bootstrap 0% tetap dilaporkan jujur; startup dibuktikan test subprocess.

## Perbaikan uji mandiri — tombol penugasan ADM-B003

Dropdown pemilihan shift dan penugasan kini memperbarui tombol segera tanpa pindah menu. Setelah memilih anggota, pilih shift pada dropdown Shift untuk mengaktifkan Tetapkan shift. Pilih opsi valid pada Penugasan yang diakhiri untuk mengaktifkan Akhiri penugasan. Placeholder tetap membuat tombol tidak aktif.

Reproduksi otomatis sebelum fix FAIL. Sesudah fix: **19 tes UI/layanan administrasi PASS** dan **1 skenario native macOS PASS**, termasuk klik tombol Tetapkan shift → pilih penugasan → kembali ke placeholder → pilih lagi → Akhiri penugasan → penugasan berikutnya, tanpa berpindah menu. Bukti: [regresi](evidence/stage-05-assignment-buttons-regression.xml), [native](evidence/stage-05-assignment-buttons-native.xml). Run 147 tes/coverage sebelumnya di atas adalah baseline sebelum perbaikan ini; verifikasi terbaru memakai cakupan terdampak tersebut.

Uji ulang: tutup aplikasi/demo lama, lalu jalankan ulang mode yang digunakan. Pilih anggota dan penugasan yang hendak diakhiri; tombol harus langsung aktif. Tidak perlu migrasi, reset akun atau mengganti data kerja. Data demo kembali ke awal ketika demo ditutup normal.
