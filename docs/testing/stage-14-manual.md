# Uji mandiri Tahap 14 — aplikasi terpasang di Windows

Status21 Oktober2026: installer sudah dibuat dan aplikasi sudah terbuka di akun Windows `kevind`. Database Windows baru terpisah dari data kerja macOS. Jangan menjalankan pengujian ini pada aplikasi macOS bila tujuan Anda memeriksa installer Windows.

## Mulai

1. Buka VM Windows11 di Parallels. StarGate sudah dipasang per-user; dapat dibuka dari Start → StarGate.
2. Jika VM baru direstart dan koneksi database gagal, buka `%LOCALAPPDATA%\StarGate-stage14\Start-StarGate.cmd`. Peluncur ini menyalakan PostgreSQL uji lokal lalu membuka aplikasi. PostgreSQL uji belum berupa service otomatis.
3. Pada versi sumber terbaru, jika belum ada Super Admin aktif, form **Buat Super Admin** muncul otomatis sebelum halaman login. Isi akun dan kata sandi sendiri, lalu login dan selesaikan ganti kata sandi wajib. Installer Windows yang dibuat sebelumnya masih memakai tombol **Buat Super Admin pertama** sampai dibangun ulang. Jangan kirim kata sandi/isi `.env` ke chat.
4. Pastikan kamera USB diarahkan ke **Windows** melalui Devices → USB & Bluetooth di Parallels. Indeks kamera mengikuti deteksi Windows; jangan menganggap indeks0 selalu kamera laptop.

## Checklist singkat

Isikan hasil di bawah. Biarkan item kosong jika belum dicoba.

| Skenario | Hasil yang diharapkan | Hasil Anda |
|---|---|---|
| Buat akun awal, login, ganti kata sandi | Tidak berkedip; fokus input bertahan; masuk dashboard | Belum diuji |
| Navigasi semua menu; tutup dan buka aplikasi | Tidak macet/crash; data tetap ada | Belum diuji |
| Ingat saya, tutup/buka; lalu logout | Sesi dipulihkan; setelah logout harus login lagi | Belum diuji |
| Tambah grup, shift, anggota dan penugasan | Dapat disimpan dan masih ada setelah buka ulang | Belum diuji |
| Preview kamera laptop dan USB secara terpisah | Gambar bergerak, kamera dilepas ketika preview dihentikan | Belum diuji |
| Dua kamera bersamaan | Keduanya bergerak; anggota yang sama tidak tercatat ganda | Belum diuji |
| Cabut USB saat aktif | Gambar dihentikan/pesan gagal; tidak beralih ke kamera laptop | Belum diuji |
| Sambungkan USB kembali; pilih dan mulai ulang | Kamera yang dipilih kembali dapat dipakai | Belum diuji |
| Registrasi lima sudut dan verifikasi wajah | Sampel lengkap; setelah restart anggota masih dikenali | Belum diuji |
| Absensi IN/OUT | Riwayat dan dashboard sesuai; tidak ada sukses palsu | Belum diuji |
| Suara berhasil | Bunyi terdengar melalui output Windows/Parallels | Belum diuji |
| Ekspor XLSX dan PDF | Terbuka pada Excel/reader Windows; jumlah/filter/teks benar | Belum diuji |
| Operasi tanpa internet | Dengan PostgreSQL tetap hidup, login/scan/laporan/backup berfungsi | Belum diuji |

Untuk skenario absensi, gunakan anggota uji dan shift yang sedang berlangsung, dengan penugasan aktif pada tanggal kerja saat ini. Check-in sebelum jam mulai memang ditolak. Ikuti jeda/deteksi wajah meninggalkan kamera sebelum menguji OUT. Lihat [panduan Tahap10](stage-10.md) untuk kasus jam dan status yang lebih lengkap.

Foto dan embedding registrasi Windows akan disimpan pada instance Windows sesuai kebijakan retensi yang sudah disetujui. Gunakan wajah sendiri atau peserta yang mengizinkan. Jangan mengirim foto/embedding melalui chat.

## Ekspor dan pemulihan

Anda dapat membuka contoh hasil paket Windows `docs/testing/evidence/stage-14-windows-export.xlsx` dan `.pdf` dari shared folder untuk memeriksa reader. Keduanya berisi71 baris sintetis; PDF18halaman. Ini bukan data absensi Anda.

Backup/restore nyata pada instance sintetis terpisah sudah diuji otomatis, termasuk penghapusan semua biometrik dan pemulihan riwayat. **Jangan menekan restore pada database Windows yang sedang Anda isi untuk sekadar mengulang tes**: restore mengganti data instance dan menghapus biometrik/sesi. Uji lebih lanjut memakai instance terpisah; [aturan pemulihan](stage-13.md) tetap berlaku.

Uninstall/reinstall dan repair versi sama sudah diuji pada akun standar sementara; konfigurasi, cadangan,71 anggota dan satu riwayat tetap ada. Anda tidak perlu menghapus instalasi yang sedang dipakai untuk review. Belum ada rilis Windows lama untuk memvalidasi upgrade/rollback lintas versi.

## Catat hasil

Kirim ringkasan: nama skenario, langkah, hasil yang muncul, dan waktu kejadian. Jika ada pesan kesalahan, sertakan kode referensinya. Jangan sertakan kata sandi, `.env`, token, URL RTSP berkredensial atau data wajah. Review ini menjadi gerbang sebelum Tahap15; hasil otomatis bukan persetujuan review pengguna.

RTSP kamera nyata belum tersedia dan tetap belum diuji. Windows fisik x64 juga belum diuji; bukti saat ini berasal dari Windows11 ARM64 Parallels yang menjalankan paket x64.
