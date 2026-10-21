# Windows / Parallels — build dan instalasi paket penelitian

20 Oktober 2026. Pemilik menetapkan penggunaan lomba/penelitian/pengujian internal dahulu. Setelah penundaan awal karena ruang disk, pengguna menyatakan komputer siap; VM berjalan dan build/UAT Windows dilanjutkan. Pembaruan21 Oktober2026: executable dan installer x64 sudah dibangun dan dipasang pada Windows11 ARM64 Parallels. Probe model, akun standar, backup/restore sintetis, offline probe dan uninstall/reinstall lulus. Review/uji perangkat akhir tetap terbuka; rincian ada di [hasil Tahap14](testing/stage-14.md).

## Arsitektur dan prasyarat

Host pengembangan macOS arm64. Inspeksi ulang setelah pengguna menyatakan siap pada20 Oktober2026 mengonfirmasi guest Windows11 Pro10.0.26200 ARM64, RAM sekitar12GB. Build/UAT dilanjutkan. Pada Windows ARM gunakan **Python 3.11 Windows x64**, sehingga seluruh wheel, PostgreSQL, pgvector dan paket aplikasi mengikuti x64. Windows 11 ARM mendukung emulasi x64 menurut [Microsoft](https://learn.microsoft.com/en-us/windows/arm/apps-on-arm-x86-emulation). Ini tidak menjamin kinerja/kompatibilitas PyTorch, ONNX Runtime, driver kamera atau CPU instruction set; semuanya perlu diuji di VM. Target fisik Windows x64 juga tetap perlu uji sebelum distribusi kepadanya.

Siapkan ruang disk yang cukup untuk VM, wheel AI, lingkungan build dan output. Angka 15–20 GB adalah anggaran kerja awal, bukan minimum resmi atau jaminan ukuran build. Cadangkan VM bila perlu. Jangan menghapus database/data kerja untuk memberi ruang.

Kebutuhan di Windows: Python 3.11 x64, Visual Studio C++ Build Tools untuk paket yang memerlukan kompilasi (termasuk InsightFace bila wheel tidak tersedia), PostgreSQL 17 x64, pgvector 0.8.7 yang dibangun terhadap instalasi PostgreSQL yang sama, dan Inno Setup **6.3+** untuk compiler installer. Jangan menyalin .venv atau lockfile macOS sebagai lingkungan Windows. Tidak ada pemasangan otomatis melalui internet saat aplikasi berjalan.

## 1. Transfer sumber yang bersih

Pada macOS:

```bash
.venv/bin/python scripts/prepare_windows_kit.py --include-research-models
```

Hasil `dist/StarGate-Windows-build-kit.zip` adalah **kit sumber**, bukan aplikasi Windows. Kit memakai allowlist dan checksum per file; tidak memuat .env nyata, database, foto anggota, embedding, backup, log atau .venv. Bobot model masuk hanya melalui flag penelitian eksplisit dan diverifikasi terhadap manifest. Jangan meneruskan kit/model ke pihak lain tanpa menyelesaikan ketentuan lisensinya. Hapus/rename kit lama bila ingin membuat nama yang sama lagi; tidak ditimpa.

Salin ZIP ke Windows melalui shared folder lalu ekstrak ke folder lokal NTFS, misalnya `C:\StarGate-build`. Bangun pada disk Windows lokal; jangan membangun langsung di path jaringan Parallels/OneDrive untuk menghindari masalah path, lock dan native DLL.

## 2. Siapkan Python x64 dan dependensi

Build aktual memakai CPython3.11.17 dari sumber resmi (installer3.11.9 bukan pembaruan keamanan terbaru). Unduh `Python-3.11.17.tgz` dari Python.org, verifikasi SHA256 `53cdee63ac4bf12387b7b33a53d3b1f8f4941cad73807a7b4fe91bb001ef004a`, lalu bangun dengan Visual Studio2022 Build Tools17.14 menggunakan `PCbuild\build.bat -p x64 -c Release --no-tkinter`. Python hasil build melaporkan `win-amd64`; gunakan path lengkap `PCbuild\amd64\python.exe` untuk membuat venv. Tiga warning metadata Git pada tarball muncul, tetapi kompilasi selesai dengan0error. Petunjuk upstream: [PCbuild](https://github.com/python/cpython/blob/v3.11.17/PCbuild/readme.txt), [rilis3.11.17](https://www.python.org/downloads/release/python-31117/). Sumber dan alat build diperlukan hanya pada mesin pembuat paket.

PowerShell di folder sumber:

```powershell
py -3.11-64 -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install --upgrade pip
.\.venv-win\Scripts\python.exe -m pip install "torch>=2.6,<3" --index-url https://download.pytorch.org/whl/cpu
.\.venv-win\Scripts\python.exe -m pip install -r requirements.in
.\.venv-win\Scripts\python.exe -m pip check
.\.venv-win\Scripts\python.exe -m pip freeze | Out-File -Encoding utf8 requirements-windows-x64.candidate.txt
.\.venv-win\Scripts\python.exe scripts/build_package.py --target windows --include-research-models --check-only
```

Jika launcher `py` tidak tersedia, gunakan path lengkap Python x64 yang dipasang. Kandidat lock Windows baru menjadi lock tervalidasi setelah build/UAT lulus; simpan versi dan hash wheel untuk reproduksi/offline. Perintah pip di atas memerlukan internet hanya saat menyiapkan lingkungan. Untuk instalasi tanpa internet, pada mesin Windows x64 build yang berhasil siapkan wheelhouse beserta hash dan instal dengan `pip --no-index --find-links <wheelhouse>`; paket yang tidak memiliki wheel harus dibangun di Windows terlebih dahulu. Wheelhouse uji Windows berisi75 wheel (388.004.710 byte); simulasi instalasi `--no-index --require-hashes --ignore-installed` lulus. Hash tersimpan pada `requirements-windows-x64.candidate.lock.txt`; wheelhouse tetap berada di VM build, bukan dalam installer/kit sumber. Status kandidat dipertahankan hingga review Windows selesai.

## 3. PostgreSQL lokal dan pgvector

Gunakan installer PostgreSQL x64 dari [halaman resmi](https://www.postgresql.org/download/windows/), simpan password administrator sendiri, gunakan port sesuai konfigurasi (contoh 5432), dan batasi listener/firewall untuk komputer lokal. Database berjalan sebagai service terpisah, bukan proses yang ikut dibundel dengan GUI.

Untuk pgvector, ikuti [instruksi upstream Windows](https://github.com/pgvector/pgvector#installation-notes---windows) dari x64 Native Tools Command Prompt dengan hak yang diperlukan. Checkout tag v0.8.7, set `PGROOT` ke instalasi PostgreSQL 17 yang benar, lalu `nmake /F Makefile.win` dan `nmake /F Makefile.win install`. Jangan mengambil DLL dari sumber tidak dikenal atau mencampur DLL PostgreSQL/arsitektur lain. Build/instalasi extension0.8.7 sudah lulus pada guest Parallels terhadap EDB PostgreSQL17.11-5 x64.

Pada database/role **baru**, jalankan:

```powershell
psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -f packaging\windows\provision.sql
```

Script berhenti jika role/database sudah ada. Password migrator dan app diminta oleh psql tanpa echo; keduanya harus berbeda dan disimpan privat. Script ini tidak memperbarui atau menghapus database lama. Jika gagal sebagian, administrator harus memeriksa state, bukan menjalankan DROP database/role secara sembarang. Jangan menjalankannya pada instance organisasi yang sudah dipakai.

## 4. Konfigurasi dan migrasi

Data aplikasi selalu terpisah dari folder executable:

- Binary/installer per-user: `%LOCALAPPDATA%\Programs\StarGate`.
- Konfigurasi: `%LOCALAPPDATA%\StarGate\.env`.
- Log: `%LOCALAPPDATA%\StarGate\logs`.
- Profil, marker remember dan pengaman: `%LOCALAPPDATA%\StarGate\.local`.
- Database PostgreSQL di data directory service PostgreSQL; tidak ikut uninstall aplikasi.
- Resource/model bawaan dibaca dari folder bundle yang immutable; model eksternal dapat dipilih dengan STARGATE_MODEL_DIR.

Buat folder data privat dan salin `packaging/windows/.env.example` menjadi `.env` di sana. Edit sendiri dalam editor lokal: host127.0.0.1, port5432, DB_NAME stargate_local, DB_USER stargate_app, password kedua role sesuai provisioning, DB_MIGRATION_USER stargate_migrator. **Jangan memakai placeholder, password contoh atau mengirim isi file ke chat.** Jangan membuat database test menunjuk database yang sama. STARGATE_MODEL_DIR boleh dihapus dari file agar model bawaan bundle dipakai; jika masih mengarah `resources/models`, path itu relatif ke data pengguna dan bobot harus disediakan di sana.

Batasi ACL folder data untuk akun Windows pemakai dan SYSTEM; jangan berikan akses ke Users/Everyone. Contoh PowerShell, periksa identitas akun sebelum menerapkan:

```powershell
$StarGateData = Join-Path $env:LOCALAPPDATA 'StarGate'
New-Item -ItemType Directory -Force $StarGateData | Out-Null
icacls $StarGateData /inheritance:r /grant:r "$($env:USERDOMAIN)\$($env:USERNAME):(OI)(CI)F" 'SYSTEM:(OI)(CI)F'
```

Uji ACL native Windows sudah lulus untuk file privat, direktori, dan penghapusan grant Everyone pada fixture uji. Kredensial owner hanya dipakai perintah migrasi/restore setelah otorisasi; tidak ada password bawaan di paket. Untuk distribusi operasional, arsitektur akses owner lokal dan tata kelola kredensial harus ditinjau sebelum rilis.

Sebelum build, CLI sumber:

```powershell
.\.venv-win\Scripts\python.exe scripts/manage_database.py upgrade --data-dir "$env:LOCALAPPDATA\StarGate"
.\.venv-win\Scripts\python.exe scripts/manage_database.py seed --data-dir "$env:LOCALAPPDATA\StarGate"
.\.venv-win\Scripts\python.exe scripts/manage_database.py bootstrap-admin --data-dir "$env:LOCALAPPDATA\StarGate"
.\.venv-win\Scripts\python.exe scripts/manage_database.py check --data-dir "$env:LOCALAPPDATA\StarGate"
```

Setelah terpasang, padanannya `StarGateAdmin.exe upgrade`, `seed`, `bootstrap-admin`, `check`; default data-dir diambil otomatis dari LOCALAPPDATA. Bootstrap hanya pada instance yang belum memiliki Super Admin aktif, meminta password interaktif dan wajib ganti awal. Migrasi tidak berjalan otomatis saat GUI dibuka.

## 5. Build, probe dan installer

```powershell
.\packaging\windows\build.ps1 -IncludeResearchModels
```

Jalankan dari sesi PowerShell dengan kebijakan skrip yang diizinkan organisasi; jangan mengubah execution policy sistem hanya untuk melewati error. Script menjalankan PyInstaller di Windows, memeriksa dependensi, menjalankan `StarGateAdmin.exe package-check` (ditambah `--verify-models` bila bobot disertakan), lalu memanggil ISCC jika tersedia. Output onedir `dist\StarGate`, installer `dist\installer`. Installer tidak memasang PostgreSQL, tidak mengubah database, tidak memuat data pengguna dan tidak menjalankan migrasi tersembunyi. Antivirus/SmartScreen/code signing belum diverifikasi; jangan menonaktifkan perlindungan untuk menganggap hasil lulus.

Probe bobot AI eksplisit:

```powershell
.\dist\StarGate\StarGateAdmin.exe package-check --verify-models --data-dir "$env:TEMP\StarGate-package-probe"
```

Probe memeriksa plugin gambar Qt, resource, import native, subprocess spawn, folder tulis dan worker model nyata pada frame kosong lokal. Tidak membuka kamera atau mengubah database. Probe sumber di macOS **tidak menggantikan probe executable Windows**.

## 6. Uji lingkungan bersih dan offline

Pada akun/VM bersih tanpa checkout, .venv, Python build atau PATH pengembangan: pasang installer, konfigurasi DB, migrasi/seed/bootstrap, login/ganti password, restart/remember, webcam laptop/USB, model/registrasi/absensi, XLSX/PDF, audit/backup, restore **hanya pada instance uji** dan reenroll. Lalu matikan internet sambil membiarkan PostgreSQL lokal hidup; ulangi fungsi utama. Tidak ada antrean absensi offline ketika DB mati; app harus menolak pencatatan tanpa sukses palsu.

Di Parallels, pastikan USB kamera dihubungkan ke Windows (bukan bersamaan dengan macOS) dan izin Windows Privacy → Camera diaktifkan. Kamera bawaan virtual Parallels, USB passthrough, audio dan driver harus diuji nyata; RTSP nyata tetap belum tersedia. Catat versi Windows, ARM/x64, Python, paket, PostgreSQL/vector, model/checksum, durasi probe dan hasil tiap skenario pada checklist Tahap 14.

## Upgrade, rollback dan uninstall

1. Hentikan terminal/scan, buat dan **uji** backup terenkripsi pada instance terpisah; backup berlaku7hari dan pemulihan wajah memerlukan registrasi ulang sesuai kebijakan pemilik.
2. Catat versi app/schema/model dan simpan paket lama. Jangan upgrade database nyata tanpa bukti pemulihan yang sesuai.
3. Installer berikutnya memakai AppId/lokasi sama, menutup proses app dan mengganti binary saja. Data pengguna/PG tetap di luar app directory. Jalankan migrasi eksplisit memakai console companion setelah membaca perubahan versi.
4. Jika binary baru gagal sebelum perubahan schema, kembalikan binary lama yang cocok dengan schema. Jika schema sudah berubah, jangan sekadar memasang binary lama atau menjalankan downgrade destruktif. Siapkan database pemulihan terpisah dengan app/schema yang cocok dengan backup dan ikuti prosedur restore Tahap13. Format backup menolak schema berbeda; tidak menjanjikan pemulihan lintas versi otomatis.
5. Uninstall hanya menghapus file binary yang dipasang, shortcut dan uninstaller. Tidak ada UninstallDelete untuk data, backup atau PostgreSQL. Pasang ulang dan periksa bahwa instance/data tetap ada. Penghapusan data permanen memerlukan tindakan pemilik terpisah; jangan menguji kehilangan data pada instance kerja.

Installer aktual456.709.976 byte, SHA256 `b12341fd78dd4711450d3673b18c5ce36ba38b0431e4dea2a46dd9437bcd6fd7`; status Authenticode NotSigned. Akun standar/ACL, probe offline dan repair/uninstall/reinstall lulus. Belum ada versi Windows terdahulu untuk membuktikan upgrade/rollback lintas rilis; repair versi sama bukan bukti lintas versi. Review pengguna, alur wajah/perangkat dan reader Windows tetap diperlukan. Tahap15 belum dimulai. Lihat [uji mandiri](testing/stage-14-manual.md).

## Lingkungan uji Windows yang sudah disiapkan

Aplikasi akun `kevind` memakai `%LOCALAPPDATA%\StarGate` dan database baru `stargate_local` pada127.0.0.1:55434. Tidak menyalin data kerja macOS. Database `stargate_clean14` berisi fixture sintetis untuk uji installer dan restore, bukan akun untuk pemakaian Anda. PostgreSQL uji berupa proses lokal terpisah, belum didaftarkan sebagai service otomatis. Jika VM direstart dan koneksi DB gagal, jalankan berkas `Start-StarGate.cmd` di `%LOCALAPPDATA%\StarGate-stage14` untuk menyalakan cluster uji dan aplikasi. Lingkungan distribusi permanen tetap mengikuti provisioning service pada bagian3.

Pengujian PDF sumber Windows memerlukan Poppler (`pdfinfo`, `pdftotext`) di PATH proses pytest saja; alat ini tidak menjadi kebutuhan runtime aplikasi. Run ini memakai Poppler25.07.0-0 dari paket winget yang diverifikasi checksum; decoding tes dieksplisitkan UTF-8. Jangan menganggap tool pengujian tersebut harus ikut installer pengguna.
