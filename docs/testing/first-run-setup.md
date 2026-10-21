# Revisi alur awal — pembuatan Super Admin

21 Oktober 2026. Pengguna meminta tombol pembuatan akun awal dihapus dari login dan diganti penyiapan otomatis.

## Perilaku

1. Saat dibuka, aplikasi memeriksa keberadaan Super Admin aktif di database melalui worker, tanpa memblokir tampilan.
2. Jika belum ada, halaman **Buat Super Admin** tampil sebelum login. Pengguna mengisi username, nama lengkap, password awal dan pengulangannya.
3. Kesalahan isian tampil pada form yang sama. Setelah akun berhasil disimpan, aplikasi menampilkan **Masuk** dan mengisi username akun baru. Login serta ganti password awal tetap mengikuti aturan sebelumnya.
4. Jika Super Admin sudah tersedia, aplikasi langsung menuju login atau memulihkan sesi tersimpan. Tombol pembuatan Super Admin tidak ada pada login.
5. Jika pemeriksaan database gagal, aplikasi tetap pada halaman persiapan dengan pesan kesalahan dan tombol **Coba lagi**. Kegagalan koneksi bukan dianggap database tanpa akun.
6. Jika jendela lain lebih dahulu membuat Super Admin, transaksi bootstrap tetap menolak duplikasi. Jendela yang tertinggal beralih ke login dengan pemberitahuan bahwa akun pengelola sudah tersedia.

Pemeriksaan mengikuti aturan bootstrap yang sudah ada: Super Admin **aktif**. Pembuatan akun tetap memakai kunci transaksi database yang sama. Tidak mengubah schema, akun atau data operasional, batas sesi, maupun aturan wajib ganti password awal.

## Verifikasi

Perintah:

```sh
.venv/bin/python -m pytest tests/test_session_ui.py tests/test_auth.py tests/test_bootstrap.py --run-db -q --tb=short
```

Hasil: **33 PASS**, 61,15 detik. Database pengujian memakai schema sementara terpisah pada `stargate_test`, bukan database kerja. Skenario baru mencakup penyiapan otomatis sebelum login, pengulangan/validasi password, restart setelah akun dibuat, login yang tidak bisa melewati penyiapan, kegagalan database dengan/tanpa akun lalu retry, serta akun yang dibuat terlebih dahulu dari jendela lain. Regresi sesi, izin role, remember-session dan startup/shutdown yang sudah ada juga lulus.

Pratinjau form diperiksa melalui Qt offscreen menggunakan status akun buatan, tanpa mengakses database atau kamera. Ini bukan uji installer Windows baru. Installer Windows sebelumnya belum dibangun ulang dan masih memakai alur lama.

Untuk mencoba pada database yang sudah memiliki Super Admin, hasil yang diharapkan adalah halaman login langsung. Jangan menghapus akun/database kerja hanya untuk memunculkan halaman penyiapan. Tahap15 dan gerbang review Windows tetap tidak berubah.
