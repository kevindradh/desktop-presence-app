# Revisi — penggantian password opsional

21 Oktober 2026. Pengguna meminta penghapusan seluruh kewajiban ganti password: Super Admin pertama, akun buatan pengelola, dan hasil reset.

## Perilaku

- Login berhasil langsung membuka halaman sesuai peran. Ingat saya dapat dipakai tanpa harus mengganti password lebih dahulu.
- Menu Ganti password tetap tersedia. Pengguna dapat kembali ke ruang kerja tanpa menggantinya.
- Reset pengelola tetap membuat password acak, menampilkannya sekali, dan mencabut sesi lama. Pemberitahuan reset tidak lagi menyebut penggantian wajib.
- Validasi password saat mengganti, hashing bcrypt, izin role, penguncian login gagal, serta waktu kedaluwarsa sesi tetap berlaku.
- Penanda must_change_password lama tetap berada pada struktur untuk kompatibilitas, tetapi tidak lagi membatasi akses atau mengarahkan pengguna ke halaman ganti password.

## Migrasi

Migrasi0005_optional_password mengubah default penanda menjadi false dan membersihkan penanda pada akun yang sudah ada. Migrasi tidak menghapus akun, mengubah password, atau mencabut sesi yang masih berlaku. Downgrade mengembalikan default lama, tanpa memaksa semua akun yang sudah ada mengganti password.

Migrasi pada stargate_dev berhasil; satu akun yang ada beserta password dan sesi tetap dipertahankan, penanda wajib tersisa0. Tidak dilakukan reset database ulang. Untuk instalasi lain, jalankan upgrade melalui alat administrasi proyek sebelum memakai versi sumber ini. Cadangan dari revisi0004 tidak dapat dipulihkan langsung pada revisi0005 karena aturan pemulihan tetap menuntut revisi yang sama; buat cadangan baru setelah upgrade. Installer Windows sebelumnya belum dibangun ulang.

## Verifikasi

```sh
.venv/bin/python -m pytest tests/test_auth.py tests/test_session_ui.py tests/test_database.py tests/test_backups.py --run-db -q --tb=short
```

**88 PASS**, 156,40detik. Bukti: [hasil uji](evidence/optional-password-change.xml). Cakupan mencakup login awal langsung ke ruang kerja, akun baru/hasil reset/penanda legacy, remember-session, penggantian password sukarela, kembali tanpa logout, izin role, hash dan audit, pencabutan sesi setelah reset/penggantian, migrasi data akun lama, schema database, serta backup/restore. Migrasi diuji dari revisi0004 dengan penanda lama true dan dibuktikan mempertahankan password serta sesi.

Setelah penyempurnaan pesan reset, skenario pengguna/create/reset/deactivate diulang: **1 PASS**. Bukti: [uji pesan reset](evidence/optional-password-reset-message.xml).

Tahap15 dan review installer Windows tetap belum diselesaikan oleh revisi ini.
