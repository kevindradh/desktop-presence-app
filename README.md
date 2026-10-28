# StarGate

Aplikasi desktop absensi wajah dengan PyQt6, PostgreSQL/pgvector, RetinaFace, ArcFace dan MiniFASNet.

## Build aplikasi Windows

Build dilakukan di Windows11 x64. Siapkan Python3.11 x64, Inno Setup6, serta runtime PostgreSQL17/pgvector. Persiapan runtime cukup sekali; langkahnya ada di [panduan build Windows](docs/windows-build.md).

Setelah clone, buka PowerShell di folder proyek:

```powershell
# Environment pengembangan Windows.
py -3.11 -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install "torch>=2.6,<3" --index-url https://download.pytorch.org/whl/cpu
.\.venv-win\Scripts\python.exe -m pip install -r requirements.in

# Ambil model dengan pemeriksaan checksum.
.\.venv-win\Scripts\python.exe scripts/download_models.py

# Buat aplikasi lalu installer, termasuk model dan database lokal.
.\packaging\windows\build.ps1 -IncludeResearchModels -PostgresRuntime 'C:\StarGate-runtime\postgresql'
```

Hasil:

- `dist/StarGate/StarGate.exe`: aplikasi beserta dependensinya; pertahankan seluruh folder jika memakai versi portable ini.
- `dist/installer/StarGate-Research-Windows-x64.exe`: installer yang diberikan ke pengguna.

Jalankan installer di laptop tujuan. Buka **StarGate** dari Start Menu, buat Super Admin pertama, lalu pin aplikasinya ke taskbar. Pengguna installer tidak perlu memasang Python atau menjalankan kode source.

Database lokal disiapkan saat pemasangan dan dinyalakan saat aplikasi dibuka. Model dimuat saat fitur registrasi/absensi dimulai. Data disimpan di `%LOCALAPPDATA%\StarGate`, terpisah dari file aplikasi.

## Pengembangan macOS

Gunakan environment dan konfigurasi lokal yang sudah disiapkan:

```bash
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python main.py
```

## Storage

`build/` dan `dist/` adalah keluaran yang dapat dibuat ulang dan diabaikan Git. Simpan satu installer yang diperlukan; tidak perlu membuat ZIP source, wheelhouse, dan salinan paket berulang. `.venv`/`.venv-win` serta bobot di `resources/models` diperlukan pada mesin pengembangan dan tidak masuk Git. Jangan menghapus `.local/postgres`, foto anggota, `.env`, atau cadangan untuk membersihkan build.

## Dokumentasi

- [Build dan prasyarat Windows](docs/windows-build.md)
- [Penggunaan aplikasi](docs/operations.md)
- [Tahapan proyek](PLAN.md) dan [pengujian yang masih terbuka](docs/testing/remaining-acceptance.md)
- [Riwayat pengembangan](docs/development-history.md)
- [Lisensi dependency/model](packaging/THIRD_PARTY_NOTICES.md)

Bobot pretrained yang digunakan mengikuti cakupan lomba, penelitian dan pengujian internal yang telah dipilih. Periksa notice sebelum distribusi komersial.
