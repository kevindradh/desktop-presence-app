# Reset database untuk testing

Perintah `fresh` adalah padanan alur `migrate:fresh` untuk StarGate: tabel aplikasi dibuat ulang dari migrasi terbaru, lalu pengaturan bawaan dan lokasi utama diisi kembali. Akun, anggota, jadwal, kehadiran, sesi dan embedding di database tujuan akan dihapus. Perintah tidak membuat akun atau anggota contoh.

## Pemakaian

Tutup aplikasi terlebih dahulu. Dari folder proyek pada macOS:

```sh
.venv/bin/python scripts/manage_database.py fresh
```

Perintah menampilkan database tujuan dan meminta Anda mengetik nama database. Untuk konfigurasi proyek saat ini, namanya `stargate_dev`.

Jika ingin langsung memberikan konfirmasi lewat perintah:

```sh
.venv/bin/python scripts/manage_database.py fresh --confirm-database stargate_dev
```

Untuk database uji yang dikonfigurasi terpisah melalui `STARGATE_DB_TEST_NAME`:

```sh
.venv/bin/python scripts/manage_database.py fresh --database test --confirm-database stargate_test
```

Nama setelah `--confirm-database` harus sama persis dengan nama database pada konfigurasi tujuan. `--data-dir` dan `--config` tetap didukung jika memakai konfigurasi lain. Perintah hanya menerima host loopback lokal dan menolak database sistem PostgreSQL.

Setelah selesai, jalankan aplikasi kembali:

```sh
.venv/bin/python main.py
```

Halaman **Buat Super Admin** akan muncul otomatis. Anda dapat membuat akun baru untuk mulai menguji dari awal.

## Lingkup dan pemeriksaan

- Reset dijalankan memakai role migrasi terpisah; bukan akun runtime aplikasi.
- Database, role dan extension pgvector tetap tersedia. Tabel aplikasi dibongkar melalui downgrade migrasi lalu dibuat lagi melalui upgrade.
- Tabel di luar StarGate atau tabel aplikasi tanpa riwayat migrasi menyebabkan proses ditolak. Tidak memakai `DROP SCHEMA CASCADE`.
- Reset, migrasi dan seed berada dalam satu transaksi. Pengujian kegagalan seed membuktikan data lama serta schema kembali melalui rollback.
- Pengaturan yang pernah diubah ikut kembali ke nilai bawaan. Tidak ada akun Super Admin yang dibuat otomatis.
- File `.env`, foto lokal dan cadangan di luar database tidak dihapus oleh perintah ini.
- Perintah tidak dijalankan otomatis saat membuka aplikasi. Installer Windows yang sudah dibuat sebelumnya belum memuat perintah baru ini.

## Verifikasi

21 Oktober2026: **41 tes lulus** pada modul fresh dan database; kemudian **11 tes fresh diulang dan lulus** setelah penambahan pemeriksaan struktur hasil. Angka11 adalah pengulangan bagian dari41, bukan tambahan kasus berbeda. Pengujian hanya memakai schema sementara terpisah di `stargate_test`; database kerja tidak direset untuk menyiapkan perintah ini.

Bukti: [run fresh dan database](testing/evidence/database-fresh-command.xml), [run akhir fresh](testing/evidence/database-fresh-command-final.xml). Skenario mencakup konfirmasi salah/tidak ada, target nonlokal/database sistem, konfirmasi interaktif, penolakan CLI sebelum membuka koneksi, reset berulang, schema kosong, seed bawaan tanpa akun, penolakan tabel asing, dan rollback saat seed gagal.
