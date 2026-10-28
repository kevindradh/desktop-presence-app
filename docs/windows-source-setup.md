# StarGate dari source di Windows 11 AMD x64

Paket source siap setup menyertakan kode aplikasi, wheel library Windows CPython3.11 x64, model AI, serta runtime PostgreSQL17/pgvector0.8.7. StarGate dijalankan dengan Python melalui `main.py`. Python dan Microsoft Visual C++ Runtime dipasang terpisah. Tidak perlu memasang Git, compiler C++, PostgreSQL sistem atau membangun pgvector untuk paket ini.

## Persiapan satu kali

1. Pasang [Python install manager dari Python.org](https://www.python.org/downloads/). Buka Terminal Windows baru dan jalankan:

   ```powershell
   pymanager install 3.11
   py -3.11 -c "import sys,sysconfig; print(sys.version); print(sysconfig.get_platform())"
   ```

   Hasil arsitektur harus `win-amd64`. Paket memerlukan Python3.11 x64; jangan memakai distribusi embeddable, Python32-bit, atau interpreter ARM64. Jika sudah memiliki Python3.11 x64, gunakan instalasi tersebut. Lingkungan pengembangan diuji memakai3.11.17; wheel memakai ABI CPython3.11.

2. Pasang [Microsoft Visual C++ Redistributable x64 resmi](https://aka.ms/vc14/vc_redist.x64.exe) bila belum tersedia. Ikuti dialog Microsoft dan restart jika diminta. Lihat [panduan Microsoft](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).
3. Ekstrak seluruh ZIP source siap setup ke folder tetap, misalnya `C:\StarGate`. Pastikan `main.py`, `SETUP-WINDOWS.cmd`, `RUN-WINDOWS.cmd`, `wheelhouse` dan `postgresql` berada langsung di folder tersebut. Jangan menjalankan dari dalam ZIP. Jangan menyalin `.venv`/`.env` milik Mac atau komputer lain.

## Setup

Klik dua kali **SETUP-WINDOWS.cmd** pada akun Windows pemakai. Tidak perlu Run as administrator. Tunggu hingga muncul `SETUP SELESAI`.

Setup memeriksa hash berkas pendukung, membuat `.venv-win`, memasang wheel lokal dengan pemeriksaan hash tanpa mengunduh library, membuat database/konfigurasi privat, menjalankan migrasi/data dasar, serta memeriksa model AI pada frame kosong. Tidak membuat akun pengguna atau memasukkan wajah nyata. Bila gagal, proses berhenti; baca pesan terakhir sebelum mengulang.

Konfigurasi, database dan log berada di `%LOCALAPPDATA%\StarGate-Source`, terpisah dari folder source dan data installer StarGate. Password database dibuat acak oleh setup. Jangan membuat `.env` manual atau menyalin contoh `.env` ke folder data ini sebelum setup pertama. Setup ulang tidak menggunakan `fresh` atau menghapus database.

## Menjalankan

Klik dua kali **RUN-WINDOWS.cmd**. Skrip menjalankan:

```powershell
.\.venv-win\Scripts\python.exe main.py --data-dir "$env:LOCALAPPDATA\StarGate-Source"
```

Buat Super Admin pertama pada halaman awal. Setelah itu siapkan grup, shift, anggota dan perangkat. Aktifkan akses kamera desktop pada Windows Settings → Privacy & security → Camera. Sampel wajah belum tersedia; registrasikan sendiri melalui aplikasi.

Untuk data SMP fiktif, opsional sebelum memasukkan data operasional:

```powershell
.\.venv-win\Scripts\python.exe scripts/manage_database.py seed-school --data-dir "$env:LOCALAPPDATA\StarGate-Source"
```

Akun simulasi dicetak jika baru dibuat; gunakan hanya untuk pengujian. Jangan menjalankan perintah `fresh` pada data yang ingin dipertahankan.

## Pemakaian dan pemeriksaan

Tutup aplikasi dengan normal. Setelah komputer direstart, RUN-WINDOWS.cmd kembali menjalankan aplikasi; startup menyalakan database kelolaan yang sudah disiapkan. Untuk pemeliharaan, tutup StarGate dahulu, kemudian:

```powershell
.\.venv-win\Scripts\python.exe scripts/setup_local_windows.py stop-local-db --data-dir "$env:LOCALAPPDATA\StarGate-Source"
```

Jangan memindahkan folder source setelah `.venv-win` dibuat karena environment Python mengandung path lokal. Untuk pindah folder, ekstrak paket di tempat baru dan jalankan setup di sana; folder data terpisah tetap dipertahankan. Ketika source diedit, tutup dan jalankan ulang aplikasi. Tidak perlu build `.exe` untuk perubahan Python.

Jika muncul error, catat perintah/pesan terakhir. `No matching distribution` atau error arsitektur perlu diperiksa; jangan mengganti versi library acak. Untuk error DLL, periksa Visual C++ Runtime x64. Jangan mengirim `.env`, password, foto atau embedding lewat chat.

Paket ditujukan untuk lomba/penelitian/uji internal sesuai izin model proyek. [Notice pihak ketiga](packaging/THIRD_PARTY_NOTICES.md) tetap berlaku. Uji di Parallels x64 membantu pemeriksaan teknis; pengujian laptop AMD fisik tetap harus dilakukan di perangkat tersebut.

Referensi instalasi Python/venv diperiksa melalui Context7 pada dokumentasi resmi CPython: [Using Python on Windows](https://docs.python.org/3/using/windows.html). Microsoft mensyaratkan arsitektur runtime sesuai aplikasi dan runtime setidaknya sama baru dengan build tools pada [dokumentasi redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).
