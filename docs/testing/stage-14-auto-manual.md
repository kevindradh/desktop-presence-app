# Uji mandiri installer otomatis StarGate

Paket penelitian **0.14.1-research**, Windows 11 64-bit Intel/AMD. Hasil Parallels dan batas pengujiannya ada di [laporan 28 Oktober](stage-14-auto-20261028.md). Komputer AMD customer masih perlu diuji.

## Pasang dan buka

1. Gunakan `dist/windows/StarGate-Research-Windows-x64-0.14.1.exe` dari proyek ini. Berkas `StarGate-Research-Windows-x64.exe` tanpa nomor versi adalah installer lama.
2. Tutup StarGate sebelum memasang atau memperbarui. Jalankan installer menggunakan akun Windows yang akan memakai aplikasi sehari-hari.
3. Tunggu penyalinan, penyiapan database, dan pemeriksaan model selesai. Paket menyertakan Python, PostgreSQL, pgvector, serta model; pemasangan baru tidak memerlukan clone GitHub atau instalasi database manual.
4. Buka StarGate melalui Start Menu. Pada pemasangan baru, isi akun Super Admin pertama, lalu masuk dengan akun tersebut. Password yang dibuat sendiri tidak memaksa langkah ganti password.

Installer belum memiliki tanda tangan digital. Identitas berkas dan SHA256 akhir dicatat di [artifact.json](evidence/automatic-windows-20261028/artifact.json). Gunakan paket yang asal dan hash-nya sudah diperiksa.

Database dan konfigurasi berada di `%LOCALAPPDATA%\StarGate`. Jika komputer sudah memiliki konfigurasi StarGate manual, installer mempertahankannya; database lama tidak otomatis diubah menjadi database kelolaan. Untuk menguji pemasangan pertama tanpa mengganggu data lama, gunakan akun Windows terpisah.

## Checklist pengujian

- [ ] Pemasangan selesai tanpa memasang Python/PostgreSQL secara manual; aplikasi dapat dibuka.
- [ ] Buat Super Admin pertama, login, keluar, dan login kembali.
- [ ] Aktifkan **Ingat saya**, tutup aplikasi, lalu buka kembali. Setelah logout, aplikasi kembali meminta login.
- [ ] Tambahkan data anggota, grup, dan shift uji. Tutup/buka aplikasi; data tetap ada.
- [ ] Mulai ulang Windows. Buka StarGate; database dapat berjalan kembali tanpa perintah tambahan.
- [ ] Uji kamera laptop dan USB, registrasi wajah, serta absensi masuk/keluar sesuai jadwal. Catat kamera yang digunakan dan hasilnya. Data wajah nyata mengikuti kebijakan penyimpanan proyek.
- [ ] Cabut USB ketika kamera aktif. Aplikasi tidak berpindah diam-diam ke kamera laptop.
- [ ] Periksa notifikasi absensi dan suara. Orang yang tetap di depan kamera tidak memunculkan notifikasi tanpa henti.
- [ ] Buka ekspor XLSX/PDF memakai aplikasi pembaca di Windows.
- [ ] Matikan internet sementara dan ulangi alur lokal, lalu aktifkan kembali koneksinya.
- [ ] Tutup StarGate, jalankan installer yang sama untuk repair. Akun dan data tetap ada.
- [ ] Uninstall StarGate, lalu pasang kembali pada akun Windows yang sama. Akun dan data tetap ada; aplikasi dapat login kembali.

Uninstall mempertahankan database dan konfigurasi. Checklist ini tidak meminta penghapusan folder data atau `migrate:fresh`.

## Jika gagal

Catat langkah, teks pesan, versi Windows, jenis prosesor, serta kamera yang digunakan. Jangan mengirim `.env`, password, token, database, foto, atau embedding melalui chat.

Untuk mencatat ulang pemasangan, buka PowerShell pada folder installer dan jalankan:

```powershell
.\StarGate-Research-Windows-x64-0.14.1.exe /LOG="$env:TEMP\StarGate-install.log"
```

Untuk memeriksa atau melanjutkan setup database kelolaan pada akun pemakai:

```powershell
$StarGateAdmin = Join-Path $env:LOCALAPPDATA 'Programs\StarGate\StarGateAdmin.exe'
& $StarGateAdmin setup-local
& $StarGateAdmin check
```

Jika perintah tetap gagal, simpan pesan dan log untuk diperiksa sebelum mengulang. Data yang sudah ada tidak perlu dihapus.

Isi hasil setiap checklist dengan **Lulus / Gagal / Belum diuji**. Tahap 15 dilanjutkan setelah review gerbang Tahap 14 selesai.
