# Build StarGate menjadi installer Windows

Alur utama: **clone → siapkan environment/model/runtime → build → jalankan installer**. Tidak perlu membuat paket source offline atau menyalin venv dari Mac.

## Persiapan mesin build, satu kali

Pasang Python3.11 x64, Git, Visual Studio Build Tools dengan komponen **Desktop development with C++**, PostgreSQL17 x64, dan Inno Setup6. Compiler dibutuhkan jika library Python harus dibangun dari source dan untuk pgvector. Alat-alat ini berada di mesin build; laptop pengguna cukup menerima installer StarGate.

Clone repositori milik Anda lalu masuk ke foldernya. URL di bawah adalah placeholder untuk URL repositori Anda:

```powershell
git clone <URL_REPOSITORI_ANDA> StarGate
cd StarGate
```

### Runtime database untuk dibawa installer

Pasang pgvector0.8.7 pada PostgreSQL17. Dari **x64 Native Tools Command Prompt** dengan hak pemasangan PostgreSQL:

```bat
git clone --branch v0.8.7 --depth 1 https://github.com/pgvector/pgvector.git C:\StarGate-pgvector
set "PGROOT=C:\Program Files\PostgreSQL\17"
cd /d C:\StarGate-pgvector
nmake /F Makefile.win
nmake /F Makefile.win install
```

Kembali ke PowerShell di folder proyek, buat venv dan pasang library sesuai README. Siapkan berkas lisensi PostgreSQL resmi ke `.local/postgresql-COPYRIGHT` dan gunakan LICENSE dari checkout pgvector:

```powershell
New-Item -ItemType Directory -Force .local | Out-Null
Invoke-WebRequest 'https://raw.githubusercontent.com/postgres/postgres/REL_17_STABLE/COPYRIGHT' -OutFile '.local\postgresql-COPYRIGHT'
.\.venv-win\Scripts\python.exe scripts/prepare_postgres_runtime.py --source 'C:\Program Files\PostgreSQL\17' --output 'C:\StarGate-runtime\postgresql' --postgres-license '.local\postgresql-COPYRIGHT' --pgvector-license 'C:\StarGate-pgvector\LICENSE'
```

Packer mengambil bin/lib/share/doc beserta lisensi dan membuat manifest; direktori database pengguna tidak ikut. Folder output runtime harus baru. Setelah siap, runtime yang sama bisa dipakai untuk build berikutnya. Jika lokasinya berbeda, sesuaikan `-PostgresRuntime`.

Referensi: [PostgreSQL Windows](https://www.postgresql.org/download/windows/) dan [pgvector Windows](https://github.com/pgvector/pgvector#installation).

## Build berikutnya

Setelah environment, model dan runtime tersedia, cukup satu perintah dari folder proyek:

```powershell
.\packaging\windows\build.ps1 -IncludeResearchModels -PostgresRuntime 'C:\StarGate-runtime\postgresql'
```

Script memeriksa dependensi, menjalankan PyInstaller dengan ikon StarGate, memeriksa paket/model, lalu menjalankan Inno Setup. ISCC dicari melalui PATH dan lokasi instalasi Inno per pengguna/sistem. Gunakan kebijakan skrip PowerShell yang diizinkan di komputer Anda.

Aplikasi berada di `dist\StarGate`; installer berada di `dist\installer\StarGate-Research-Windows-x64.exe`. Berikan installer tersebut ke laptop tujuan. Setelah dipasang, buka dari Start Menu dan pin ke taskbar. Python, Git dan compiler tidak diperlukan di laptop pengguna.

## Membersihkan hasil build

Tutup aplikasi/alat yang sedang memakai hasil build, kemudian hapus folder `build` dan keluaran `dist` yang tidak diperlukan. Keduanya bisa dibuat ulang. Pertahankan satu installer terbaru bila masih dibutuhkan. Model dan environment pengembangan tetap diperlukan untuk build; database, foto, konfigurasi dan cadangan bukan cache build.

Dokumen lama dan hasil pengujian tersimpan sebagai riwayat. Penyiapan paket source offline bukan alur utama lagi.
