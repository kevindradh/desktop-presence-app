# Setup StarGate untuk pengujian Windows 11 AMD

Panduan 21 Oktober 2026. Gunakan paket Windows **x64** untuk komputer AMD dengan Windows 11 64-bit. Pengujian sebelumnya dilakukan pada paket x64 di Windows 11 ARM64 Parallels; komputer AMD fisik customer belum diuji.

**Status paket:** installer yang tersedia saat panduan ini dibuat masih versi sebelum revisi terbaru. Bangun ulang dan uji paket dari sumber terbaru sebelum dikirim. Panduan ini mengacu pada CLI dan alur akun versi terbaru, bukan installer lama. Build aplikasi mengikuti [panduan pembuat paket](windows-install.md).

## 1. Berkas yang diberikan kepada customer

Siapkan satu folder `Downloads\StarGate-setup` berisi:

- Installer `StarGate-Research-Windows-x64.exe` hasil build terbaru.
- `provision.sql` dari `packaging/windows/provision.sql`.
- `.env.example` dari `packaging/windows/.env.example`.
- Panduan ini.

Jangan menyalin `.env` nyata, database, foto, embedding atau akun pribadi pengembang. Paket saat ini disiapkan untuk lomba/penelitian/pengujian internal sesuai cakupan proyek. Catat versi/commit dan checksum installer yang benar-benar dikirim; checksum installer lama tidak berlaku untuk hasil build baru.

Python, pip dan lingkungan pengembangan aplikasi tidak perlu dipasang pada komputer customer untuk menjalankan paket executable. Database PostgreSQL dan extension pgvector masih perlu disiapkan terpisah. Bagian 2–5 dapat dikerjakan oleh Anda atau teknisi saat pemasangan awal.

## 2. Pasang PostgreSQL 17 x64

Unduh installer Windows melalui [halaman resmi PostgreSQL](https://www.postgresql.org/download/windows/). Pilih seri **17 x64** agar sesuai dengan lingkungan pengujian proyek. Gunakan pembaruan seri 17 yang tersedia melalui sumber resmi.

Saat instalasi:

1. Pasang PostgreSQL Server dan Command Line Tools. pgAdmin boleh ikut dipasang untuk memudahkan pemeriksaan.
2. Gunakan lokasi standar `C:\Program Files\PostgreSQL\17` agar perintah di bawah sesuai.
3. Buat password administrator `postgres` dan simpan sendiri.
4. Gunakan port **5432** bila masih tersedia. Jika memilih port lain, samakan pada perintah dan `.env` nanti.
5. Pastikan service PostgreSQL berjalan melalui aplikasi **Services** Windows. Untuk penggunaan satu komputer, gunakan koneksi lokal; tidak perlu membuka akses database dari internet.

Jika komputer sudah memakai PostgreSQL atau memiliki database StarGate, periksa konfigurasinya dahulu. Langkah provisioning di bawah ditujukan untuk instance StarGate baru.

## 3. Pasang pgvector 0.8.7 untuk PostgreSQL 17

pgvector menyimpan dan mencari data ciri wajah. Menjalankan `CREATE EXTENSION vector` saja belum cukup jika berkas extension belum terpasang pada PostgreSQL.

Ikuti [petunjuk Windows resmi pgvector](https://github.com/pgvector/pgvector#installation). Petunjuk terbaru juga diperiksa melalui Context7. Untuk proyek ini, target `PGROOT` disesuaikan ke PostgreSQL 17 yang telah diuji.

1. Pasang Visual Studio Build Tools dengan dukungan **Desktop development with C++**, termasuk MSVC x64 dan Windows SDK.
2. Unduh [sumber pgvector v0.8.7](https://github.com/pgvector/pgvector/archive/refs/tags/v0.8.7.zip), lalu ekstrak sehingga folder sumber berada di `Downloads\StarGate-setup\pgvector-0.8.7` dan berisi `Makefile.win`.
3. Buka **x64 Native Tools Command Prompt** dari Visual Studio dengan **Run as administrator**. Perintah berikut dijalankan di terminal tersebut, bukan PowerShell biasa:

```bat
set "PGROOT=C:\Program Files\PostgreSQL\17"
cd /d "%USERPROFILE%\Downloads\StarGate-setup\pgvector-0.8.7"
nmake /F Makefile.win
nmake /F Makefile.win install
```

Jika instalasi PostgreSQL berada di folder lain, sesuaikan `PGROOT`. Extension harus dibangun untuk arsitektur x64 dan instalasi PostgreSQL yang digunakan. Setelah berhasil, aplikasi StarGate tidak membutuhkan compiler ini untuk berjalan.

## 4. Buat database StarGate

Buka **PowerShell** pada akun Windows yang akan menggunakan aplikasi:

```powershell
$StarGateSetup = Join-Path $env:USERPROFILE 'Downloads\StarGate-setup'
& 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -h 127.0.0.1 -p 5432 -U postgres -d postgres -f "$StarGateSetup\provision.sql"
```

Masukkan password administrator PostgreSQL saat diminta. Script kemudian meminta dua password baru, masing-masing dengan konfirmasi:

- `stargate_migrator`: akun database untuk migrasi dan pemeliharaan.
- `stargate_app`: akun database untuk aplikasi sehari-hari.

Gunakan password berbeda dan simpan keduanya untuk konfigurasi langkah berikutnya. Ini bukan akun login pengguna StarGate.

Script membuat `stargate_local`, mengaktifkan extension vector, dan mengatur hak akses. Script berhenti jika role/database dengan nama tersebut sudah ada. Jika gagal, baca error dan periksa state terlebih dahulu; jangan menghapus database untuk sekadar mengulang pemasangan.

## 5. Pasang aplikasi dan buat konfigurasi

Jalankan installer terbaru menggunakan akun Windows yang akan memakai aplikasi. Installer memasang executable per pengguna pada:

```text
%LOCALAPPDATA%\Programs\StarGate
```

Jangan membuka aplikasi dulu sebelum database dan konfigurasi siap. Pada PowerShell akun yang sama:

```powershell
$StarGateSetup = Join-Path $env:USERPROFILE 'Downloads\StarGate-setup'
$StarGateData = Join-Path $env:LOCALAPPDATA 'StarGate'
$StarGateAccount = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
New-Item -ItemType Directory -Force $StarGateData | Out-Null
icacls $StarGateData /inheritance:r /grant:r "$($StarGateAccount):(OI)(CI)F" 'SYSTEM:(OI)(CI)F'
Copy-Item "$StarGateSetup\.env.example" "$StarGateData\.env"
notepad "$StarGateData\.env"
```

Perintah penyalinan contoh ditujukan untuk pemasangan baru. Jangan menimpa `.env` yang sudah dipakai pada instalasi lain. Isi file dengan konfigurasi berikut; ganti dua nilai `ISI_...` dengan password yang dibuat pada langkah 4:

```dotenv
STARGATE_DB_HOST=127.0.0.1
STARGATE_DB_PORT=5432
STARGATE_DB_NAME=stargate_local
STARGATE_DB_USER=stargate_app
STARGATE_DB_PASSWORD=ISI_PASSWORD_DATABASE_APLIKASI
STARGATE_DB_MIGRATION_USER=stargate_migrator
STARGATE_DB_MIGRATION_PASSWORD=ISI_PASSWORD_DATABASE_MIGRATOR
STARGATE_TIMEZONE=Asia/Jakarta
STARGATE_LOG_LEVEL=INFO
```

Simpan sebagai `.env`, bukan `.env.txt`. Jangan mengisi `STARGATE_MODEL_DIR` jika menggunakan model bawaan installer. Isi password langsung di komputer customer, bukan melalui chat. Bila password memuat karakter yang membutuhkan pengutipan pada format dotenv, gunakan pengutipan yang sesuai saat mengedit file.

## 6. Siapkan tabel dan periksa paket

Masih pada PowerShell akun pemakai:

```powershell
$StarGateApp = Join-Path $env:LOCALAPPDATA 'Programs\StarGate'
& "$StarGateApp\StarGateAdmin.exe" upgrade
& "$StarGateApp\StarGateAdmin.exe" seed
& "$StarGateApp\StarGateAdmin.exe" check
& "$StarGateApp\StarGateAdmin.exe" package-check --verify-models
```

Jalankan berurutan dan berhenti jika ada perintah gagal. `upgrade` membuat/memperbarui tabel, `seed` mengisi data dasar, `check` memeriksa database, dan `package-check --verify-models` memeriksa paket/model pada mesin customer. Perintah ini bukan pembuktian akurasi pengenalan wajah.

Untuk pengujian dari keadaan kosong, lanjutkan ke langkah 7 dan buat data sendiri. Jangan menjalankan `fresh` pada database yang ingin dipertahankan.

Opsional, jika ingin data simulasi sekolah yang sudah disediakan, jalankan **sebelum mengisi data operasional**:

```powershell
& "$StarGateApp\StarGateAdmin.exe" seed-school
```

Seeder menghasilkan data fiktif dan akun uji. Kredensial pengujian dicetak pada terminal; gunakan akun tersebut hanya untuk pengujian. Sampel wajah tidak disertakan, sehingga registrasi wajah tetap perlu dilakukan. Perintah `seed-school` memerlukan paket versi terbaru dan tidak tersedia pada installer lama Tahap 14.

## 7. Login dan izin kamera

1. Buka **Start → StarGate**.
2. Pada database tanpa Super Admin aktif, buat akun Super Admin pada form awal yang muncul. Jika memakai seeder sekolah, login dengan akun uji yang dicetak terminal.
3. Buka Windows **Settings → Privacy & security → Camera**. Aktifkan akses kamera dan **Let desktop apps access your camera**. Tutup aplikasi lain yang sedang menggunakan kamera saat menguji.
4. Di **Perangkat**, tambahkan kamera bawaan/USB dan jalankan **Pratinjau**. Cocokkan nomor kamera dengan gambar sebenarnya; indeks nol belum tentu kamera laptop.
5. Siapkan grup, shift yang sedang berlangsung, anggota, dan penugasan shift. Registrasikan lima sudut wajah dengan kamera yang benar.
6. Buka **Kehadiran**, pilih perangkat dan mode, lalu **Mulai**. Periksa notifikasi, suara, daftar kehadiran, dan hasil di dashboard/laporan.

Pilihan kamera dialog registrasi masih memakai indeks. Perubahan dropdown nama kamera telah dibatalkan atas permintaan pengguna; deteksi kamera internal belum dianggap selesai diperbaiki. Laporkan jika kamera laptop customer tidak dapat dibuka.

## 8. Uji singkat customer

- [ ] Tutup/buka StarGate dan periksa data tetap ada.
- [ ] Restart Windows, lalu periksa service PostgreSQL dan StarGate dapat berjalan.
- [ ] Uji kamera laptop dan USB secara terpisah.
- [ ] Cabut USB saat berjalan: tidak boleh berpindah sendiri ke kamera laptop.
- [ ] Registrasi wajah, scan masuk/keluar, dan periksa riwayatnya.
- [ ] Tetap menatap kamera: event dan notifikasi tidak boleh berulang tanpa aturan scan berikutnya terpenuhi.
- [ ] Ekspor Excel/PDF dan buka berkasnya.
- [ ] Putuskan internet, biarkan PostgreSQL lokal hidup, lalu ulangi fungsi utama.

Catat langkah, hasil, dan nomor referensi jika muncul error. Log berada di `%LOCALAPPDATA%\StarGate\logs`; periksa isinya sebelum dibagikan. Jangan mengirim password, `.env`, URL kamera berkredensial, atau data wajah.

Setelah setup awal, pemakaian sehari-hari cukup **Start → StarGate** dengan service PostgreSQL berjalan. Pemeriksaan di komputer AMD customer merupakan uji kompatibilitas tersendiri; keberhasilan di Parallels tidak menggantikannya.
