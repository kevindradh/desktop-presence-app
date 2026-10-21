# Installer Windows dengan setup otomatis

Status 21 Oktober 2026: **kode telah disiapkan; installer baru belum dibangun dan belum diuji di Windows**. Parallels menolak menyalakan VM karena perlu tambahan ruang sedikitnya 2.146 MB. Pengguna memilih menyiapkan kode dahulu dan menguji Windows nanti. Installer lama pada `dist/windows` belum memuat fitur ini.

## Alur customer setelah paket baru lolos pengujian

1. Jalankan installer x64 pada akun Windows pemakai.
2. Installer menyalin aplikasi, model yang diizinkan, PostgreSQL 17 x64, dan pgvector 0.8.7.
3. Untuk pemasangan baru, setup membuat database lokal, password acak, konfigurasi privat, tabel dan data dasar.
4. Installer memeriksa paket/native runtime dan model bila disertakan. Jika setup/pemeriksaan gagal, peluncuran otomatis tidak dijalankan dan installer menampilkan pesan gagal.
5. Buka StarGate dan buat Super Admin sendiri. Akun/password aplikasi tidak dibuat otomatis.

Customer tidak perlu clone GitHub, memasang Python, Git, compiler atau PostgreSQL sistem. Tidak ada unduhan saat setup lokal berlangsung. Kebutuhan native harus dibawa oleh pembuat paket dan dibuktikan pada Windows bersih melalui pemeriksaan/UAT, bukan diasumsikan dari kode ini.

## Database milik aplikasi

- Runtime hanya-baca: direktori `_internal/postgresql` di dalam paket aplikasi.
- Data privat: `%LOCALAPPDATA%\StarGate\.local\managed-postgres`.
- Konfigurasi: `%LOCALAPPDATA%\StarGate\.env`.
- Listener: `127.0.0.1`, memilih port kosong dalam 55435–55444 saat setup pertama; port tetap dipakai setelah itu.
- Tiga password acak berbeda: owner cluster, migrator dan aplikasi. Password tidak dikirim sebagai argumen command line. Berkas credential/config dilindungi dengan pembatasan file privat yang sudah digunakan proyek.
- Auth PostgreSQL memakai SCRAM. Role aplikasi/migrator bukan superuser. Owner cluster dipakai hanya untuk provisioning, termasuk extension vector.
- Startup aplikasi memeriksa penanda database kelolaan, memvalidasi konfigurasi/runtime, dan menyalakan cluster melalui worker agar GUI tidak diblokir. Database sistem atau instance eksternal tidak dinyalakan/diubah otomatis.
- Database tetap hidup setelah jendela ditutup. Setelah restart Windows, membuka StarGate menyalakannya lagi. Tidak membuat service Windows atau tugas startup sistem.
- Uninstall menjalankan penghentian cluster kelolaan sebelum menghapus binary; data dan konfigurasi tetap dipertahankan.

Jika `.env` sudah ada tanpa penanda database kelolaan, setup tidak menimpa konfigurasi, membuat cluster, atau menjalankan migrasi pada database tersebut. Instalasi lama tetap mengikuti prosedur upgrade eksplisit. Menjalankan ulang setup pada cluster kelolaan tidak menggunakan `fresh`, DROP atau penghapusan folder data. Proses memakai lock untuk mencegah dua setup berjalan bersamaan. State yang tidak konsisten menyebabkan setup berhenti; tidak dihapus atau ditebak secara otomatis.

## Persiapan satu kali pada mesin pembuat paket

Gunakan Windows x64 beserta lingkungan build proyek yang sudah sesuai. Siapkan instalasi PostgreSQL 17 x64 yang berisi pgvector 0.8.7 yang dibangun untuk instalasi tersebut. Gunakan sumber resmi dan simpan lisensi beserta dependensi native/vendor yang didistribusikan. Referensi upstream yang diperiksa melalui Context7: [initdb dan auth](https://www.postgresql.org/docs/17/creating-cluster.html), [pg_ctl](https://www.postgresql.org/docs/17/app-pg-ctl.html), dan [pgvector Windows](https://github.com/pgvector/pgvector#installation).

Contoh PowerShell pada mesin build, dengan lokasi lisensi disesuaikan ke berkas resmi yang tersedia:

```powershell
.\.venv-win\Scripts\python.exe scripts/prepare_postgres_runtime.py --source 'C:\Program Files\PostgreSQL\17' --output 'C:\StarGate-runtime\postgresql' --postgres-license 'C:\StarGate-sources\postgresql-COPYRIGHT' --pgvector-license 'C:\StarGate-sources\pgvector\LICENSE'
.\packaging\windows\build.ps1 -IncludeResearchModels -PostgresRuntime 'C:\StarGate-runtime\postgresql'
```

Lokasi `C:\StarGate-sources\...` adalah contoh lokasi berkas sumber/lisensi, bukan berkas yang disediakan otomatis. Folder output runtime harus baru dan di luar folder sumber PostgreSQL. Runtime packer memeriksa header PE x64 PostgreSQL dan vector DLL, seri PostgreSQL melalui executable saat CLI dijalankan, control pgvector, serta keberadaan lisensi. Packer hanya menyalin bin/lib/share/doc dan berkas lisensi, lalu membuat manifest SHA256. Folder data/konfigurasi PostgreSQL tidak ikut disalin. Manifest runtime diverifikasi sebelum setup/start; berkas kurang, berubah, tambahan, atau tautan ditolak.

Kebutuhan DLL C/C++/OpenSSL/ICU dan lisensi vendor tetap harus tersedia di hasil paket. Proses PostgreSQL mendapat PATH terbatas yang mencakup bin runtime, `_internal` aplikasi dan direktori sistem; variabel PG bawaan shell tidak diwariskan ke alat PostgreSQL. Jalur ini belum merupakan bukti seluruh dependensi berjalan di Windows bersih.

Opsi `-PostgresRuntime` bersifat eksplisit. Build tanpa opsi tersebut masih menghasilkan paket yang memerlukan setup database manual, sehingga jangan menyerahkan paket itu sebagai installer otomatis.

## Perintah pendamping

Pada aplikasi terpasang, PowerShell:

```powershell
$StarGateAdmin = Join-Path $env:LOCALAPPDATA 'Programs\StarGate\StarGateAdmin.exe'
& $StarGateAdmin setup-check
& $StarGateAdmin setup-local
& $StarGateAdmin package-check --verify-models
```

`setup-check` hanya memeriksa kelengkapan/hash runtime. `setup-local` menjalankan atau melanjutkan provisioning/migrasi/data dasar untuk instance kelolaan. `package-check` menguji Qt/import native/proses model sesuai opsi; ini tidak menguji akurasi wajah. `stop-local-db` tersedia untuk pemeliharaan saat aplikasi ditutup. Jangan menyamakan `setup-check` dengan UAT Windows yang sudah lulus.

## Pengujian sebelum customer menerima paket

- [ ] Build Windows dari source terbaru dengan runtime dan model yang sesuai cakupan penggunaan.
- [ ] Jalankan installer sebagai pengguna standar di akun Windows bersih tanpa Python, PostgreSQL sistem, compiler atau PATH pengembangan.
- [ ] Buktikan tidak ada unduhan dan setup selesai tanpa langkah database manual; pemeriksaan native/model lulus.
- [ ] Periksa database baru/tabel/extension/ACL, listener loopback, role minimal dan password privat.
- [ ] Buat Super Admin, login dan uji kamera/registrasi/absensi nyata pada komputer AMD customer.
- [ ] Tutup/buka dan restart Windows; aplikasi dapat menyalakan database kelolaannya kembali.
- [ ] Ulangi installer dan setup; akun/data/sentinel tetap, tidak ada inisialisasi ulang.
- [ ] Uji port terpakai, ruang disk kurang, native DLL hilang, runtime berubah, serta penghentian setup di tengah proses. Tidak boleh ada sukses palsu atau penghapusan data.
- [ ] Uji repair/upgrade saat cluster masih hidup, uninstall/reinstall dan penghentian cluster. Pastikan executable yang sedang digunakan tidak menyebabkan kegagalan penggantian runtime. Upgrade PostgreSQL lintas versi mayor belum didukung otomatis.
- [ ] Uji konfigurasi eksternal yang sudah ada: tidak ditimpa atau dimigrasi otomatis.

Pengujian komponen di Mac memakai executable/worker bootstrap simulasi untuk memeriksa orkestrasi dan pengaman. Uji tambahan menjalankan **PostgreSQL 17 native macOS pada cluster sementara yang terpisah** untuk membuktikan provisioning SQL, extension vector 0.8.7, migrasi, data dasar, pembuatan Super Admin, setup ulang tanpa kehilangan akun, dan stop/start dengan akun tetap ada. Uji tersebut memetakan alat native macOS sebagai adaptor pengujian; tidak menjalankan executable Windows, memvalidasi DLL Windows, atau membuktikan installer Windows berhasil.

Bukti: `testing/evidence/automatic-setup-core.xml`, `testing/evidence/automatic-setup-session.xml`, dan `testing/evidence/automatic-setup-native-posix.xml`. Sampai checklist Windows lulus, fitur ini merupakan kode persiapan, bukan installer siap kirim.

Hasil persiapan: 33 tes komponen/packaging/bootstrap/SQL native dan 20 regresi startup/login lulus (53 total); satu tes model nyata dilewati karena di luar cakupan setup ini. Bukti native POSIX terarah juga lulus dan merupakan bagian dari cakupan yang sama, bukan tambahan jumlah kasus unik. Diff diperiksa tanpa galat whitespace. Kode installer dan pencarian DLL/ACL Windows masih memerlukan compiler/UAT Windows; tidak ditandai lulus dari pengujian Mac.

Pemeriksaan copy installer: dua status menyebut langkah yang sedang berjalan (menyiapkan database/memeriksa aplikasi), dan kegagalan meminta pendampingan tanpa menampilkan rahasia atau exception mentah. Tidak menambah aset, dekorasi, atau mengubah tampilan halaman aplikasi. Pemeriksaan sumber/copy selesai; gerbang distribusi installer tetap terbuka sesuai pilihan pengguna menunda Windows.
