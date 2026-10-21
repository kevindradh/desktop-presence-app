# Tahap 14 — Packaging dan pengujian Windows

Pembaruan **21 Oktober 2026**. Pengguna meminta kelanjutan setelah ruang disk tersedia dan menghubungkan USB ke Windows. Build dan pengujian teknis di bawah selesai pada Windows11 Pro10.0.26200 ARM64 Parallels, RAM12GB, menjalankan paket **x64**. Tujuan tetap lomba/penelitian/pengujian internal.

**Status: installer siap untuk uji mandiri; gerbang review pengguna belum lulus. Tahap15 belum dimulai.** Uji wajah/alur lengkap secara manual, suara, reader Windows dan offline alur lengkap belum dianggap lulus dari tes otomatis. Windows fisik x64 dan RTSP nyata belum diuji.

- [Panduan uji mandiri](stage-14-manual.md)
- [Instalasi/build dan pemulihan](../windows-install.md)
- Installer: `dist/windows/StarGate-Research-Windows-x64.exe`, **456.709.976 byte**.
- SHA256: `b12341fd78dd4711450d3673b18c5ce36ba38b0431e4dea2a46dd9437bcd6fd7`.
- Authenticode: **NotSigned**; perlindungan Windows tidak dinonaktifkan. Ini bukan izin distribusi publik/komersial.

## Checklist Windows

- [x] Inventaris OS/arsitektur, CPython3.11.17 win-amd64 dan75 komponen disimpan.
- [x] pip check,75 wheel/hash dan simulasi instalasi tanpa indeks internet lulus.
- [x] PyInstaller GUI+console companion dan Inno6.7.3 berhasil; manifest4615 file serta lisensi wheel/CPython disertakan; file privat ditolak finalizer.
- [x] Probe executable Qt/resource/native/spawn/pinned models/worker/frame kosong PASS dari TEMP, PATH hanya direktori Windows.
- [x] Installer per-user pada akun standar baru `SGStage14UAT`; token tidak elevated, ACL privat nyata lulus.
- [x] PostgreSQL17.11-5 x64 dan pgvector0.8.7 dibangun/provision terpisah; upgrade/seed/check0004_devices/14tabel PASS.
- [x] Pada runtime terpasang: bootstrap/login/ganti wajib, absensi sintetis, laporan, backup/restore dan native credential lintas proses PASS.
- [x] Kedua kamera, buka ulang, simultan1280x720 dan jalur gagal melalui runtime frozen PASS,7kasus; tidak menyimpan gambar.
- [x] Probe model/database dengan adaptor Ethernet **Disconnected** PASS; jaringan dikembalikan Up.
- [x] Repair versi sama, uninstall dan reinstall mempertahankan konfigurasi/cadangan/sentinel serta71 anggota dan1riwayat sintetis.
- [ ] Registrasi/wajah/IN-OUT manual, cabut USB fisik dan audio dari aplikasi terpasang.
- [ ] Buka XLSX/PDF pada Excel/reader Windows; alur lengkap tanpa internet.
- [ ] Review pengguna; baru boleh lanjut Tahap15.

Upgrade/rollback lintas rilis belum berlaku sebagai bukti pada paket Windows pertama: tidak tersedia rilis Windows terdahulu. Repair versi sama bukan uji kompatibilitas versi lama. Prosedur migrasi/pengaman/recovery tetap tersedia; restore transaksi/gagal/crash juga diuji pada suite Windows.

## Bukti Windows dan batasnya

| Pemeriksaan | Hasil | Bukti |
|---|---|---|
| Regresi penuh setelah pemasangan Poppler |455 PASS,2 FAIL timeout,1 SKIP,1063,71detik | `evidence/stage-14-windows-tests-final.xml` |
| Ulang terpisah kedua kasus timeout + parametrisasinya |3 PASS,12,54detik; tanpa perubahan batas produksi | `evidence/stage-14-windows-timeout-recheck.xml` |
| ACL Windows | Lulus dalam regresi: protected DACL current user+SYSTEM; grant Everyone dibuang | Suite penuh dan `tests/test_private_files.py` |
| Finalizer/probe frozen | PASS termasuk worker AI siap dan frame kosong | `evidence/stage-14-windows-frozen-final.log` |
| Akun standar terpasang | Non-elevated; package-check dan DB PASS | `evidence/stage-14-clean-elevated.txt`, `stage-14-clean-package-check.log`, `stage-14-clean-database.log` |
| UAT fungsi runtime terpasang |71anggota sintetis,1IN,71baris XLSX/PDF; restore membuang1foto sintetis+5embedding dan menjaga riwayat; native credential resume lintas proses PASS | `evidence/stage-14-clean-frozen-uat.log`, `stage-14-clean-frozen-resume.log` |
| Offline | Ethernet Disconnected; AI probe dan DB lokal PASS | `evidence/stage-14-clean-offline-network.json`, `stage-14-clean-offline-package.log`, `stage-14-clean-offline-database.log` |
| Repair/uninstall/reinstall | Konfigurasi/cadangan/sentinel tetap,71anggota/1riwayat/0embedding/1akun | `evidence/stage-14-clean-lifecycle-result.txt`, `stage-14-clean-preserved-data.log` |
| Kamera frozen akhir |7 PASS: tiap kamera60frame, reopen1frame, simultan143/60frame, missing index dan RTSP localhost gagal dengan aman | `evidence/stage-14-windows-cameras-frozen-reconnected.json` |
| Ekspor aktual runtime Windows | XLSX2sheet,71baris; PDF18halaman seluruh71ID ada; render awal/tengah/akhir terbaca | `evidence/stage-14-windows-export.xlsx`, `.pdf`, `.txt` |
| Instalasi akun pengguna | GUI halaman masuk dan Buat Super Admin pertama terlihat; DB baru terpisah dari Mac | `evidence/stage-14-user-install-result.txt`, `stage-14-user-database.log` |

Run penuh belum dilaporkan sebagai satu run hijau. Kedua timeout terjadi ketika VM menjalankan pekerjaan tambahan; run terpisah lulus. Satu SKIP adalah pembuatan symlink yang tidak diizinkan token Windows standar; kebijakan sistem tidak diubah. Tes symlink terpisah menggunakan hak SYSTEM yang sudah tersedia **1PASS**,0,60detik (`evidence/stage-14-windows-symlink-system.xml`). Satu FutureWarning InsightFace/skimage upstream tetap ada. Snapshot coverage macOS di bawah mendahului perbaikan Windows; tidak dianggap coverage Windows.

Probe kamera pertama sesudah instalasi sempat4FAIL/3PASS. Inventaris saat itu hanya FaceTime; USB tidak terdeteksi. Recheck sumber dilakukan ketika USB sedang disambungkan kembali (5PASS/2FAIL); setelah pengguna menghubungkan USB dan kedua perangkat berstatusOK, ulang frozen7/7PASS. Kegagalan awal pembukaan laptop belum terisolasi sepenuhnya; pantau uji mandiri/soak. Tidak menaikkan timeout produksi atau mengaktifkan reconnect indeks lokal untuk menutupi kegagalan. Pengujian kamera memakai helper build-only dari `scripts/check_cameras.py`, `QApplication.processEvents` sebagai pengganti QtTest, candidate PYZ/DLL yang sama; bukan bukti otomatis klik halaman kamera.

UAT fungsi memakai `scripts/testing/windows_frozen_uat.py`, entry diagnostik sementara di samping `_internal` aplikasi terpasang, dengan PATH tanpa Python pengembangan. Guard hanya menerima database baru `stargate_clean14` pada127.0.0.1:55434; foto kotak hijau12x12, embedding one-hot sintetis, bukan wajah nyata. Helper menggunakan service produksi, owner helper frozen untuk restore dan credential vault native. EXE diagnostik tidak disertakan installer. Akun standar sementara dinonaktifkan setelah uji; aplikasi pada akun `kevind` tetap tersedia. Tidak menyalin database/foto/kredensial kerja Mac atau memulihkan database kerja.

PostgreSQL uji Windows merupakan proses loopback terpisah, belum service otomatis. Konfigurasi akun pengguna berada di `%LOCALAPPDATA%\StarGate`, mengarah ke database baru `stargate_local` pada55434; peluncur restart tersedia sesuai panduan. Password akun aplikasi Anda harus diisi sendiri melalui UI.

## Temuan yang ditangani

- DACL Windows menggantikan asumsi chmod0600 untuk foto, marker, log, backup dan pengaman restore; ACL ditetapkan sebelum penulisan.
- Kit menyertakan pytest.ini agar tidak mengoleksi tes CPython prasyarat; kandidat lock Windows/hash serta panduan uji ikut kit terbaru.
- Capture group bertanda tangan mencegah hasil pertama kamera kedua yang terlambat menjadi OUT setelah cooldown sebelum wajah meninggalkan kedua kamera.
- Klik Pulihkan saat session poll tidak lagi hilang; maintenance menunggu pekerjaan sebelumnya.
- ONNX memerlukan direktori DLL saudara `onnx.libs`; finalizer memakai helper delvewheel resmi PyInstaller dan menjaga folder sebelum hashing manifest. Probe model diulang lulus.
- Tes ekspor memakai UTF-8 eksplisit dan Poppler pada PATH pengujian saja; Poppler bukan kebutuhan aplikasi pengguna.
- Wrapper build penelitian kini mewajibkan probe model sebelum membuat installer. Tidak ada perubahan runtime setelah candidate ini kecuali finalizer DLL yang sudah diterapkan sebelum kompilasi installer.

Detail: [catatan bug](../bugs.md), inventaris/lisensi `evidence/stage-14-windows-environment.json`, manifest akhir `evidence/stage-14-windows-build-final.json` dan hash installer `evidence/stage-14-windows-installer.json`.

## Bukti macOS

Hasil verifikasi yang tersedia:

| Lapisan | Hasil | Bukti |
|---|---|---|
| Regresi macOS, PostgreSQL test, model dan keychain uji | **452 PASS**, 0 failure/error/skip; 917,37 detik | evidence/stage-14-tests.xml |
| Coverage app/database/ai | **89,97%**, 7.115/7.908 statement; 793 miss | evidence/stage-14-summary.json; .local/stage-14-coverage.json |
| Fokus path/config/kit/probe source | **25 PASS**, 5,97 detik | evidence/stage-14-focused.xml |
| Native macOS Cocoa final | **69 PASS**, 0 failure/error/skip; 280,02 detik | evidence/stage-14-native.xml |
| Portabilitas codec sesudah guard fchmod | **8 PASS**, 10,75 detik | evidence/stage-14-backup-portability.xml |
| Koneksi data kerja baca-saja | **PASS**, revision0004_devices, 14 tabel, tanpa migrate/restore | evidence/stage-14-summary.json |

Angka coverage mengukur proses induk; bootstrap/probe yang dijalankan subprocess diuji melalui output/exit/resource/spawn dan tidak digabungkan ke coverage induk. Guard ketersediaan fchmod mempertahankan jalur POSIX dan diverifikasi ulang melalui 8 tes codec, termasuk simulasi API hilang. Ini tidak menguji ACL Windows.

Native awal68PASS/1FAIL menemukan permintaan audit hilang ketika poll sesi aktif. Antrean diperbaiki dan fixture kini menahan poll secara terkontrol; native69 dan regresi452 berikutnya lulus. Run regresi awal dihentikan setelah menangkap kasus yang sama; tidak dihitung sebagai run PASS. Satu FutureWarning upstream InsightFace/skimage tetap ada. Bukti tersebut berada di proyek pengembangan; jangan mengartikannya sebagai hasil executable Windows.

Probe source Qt/native/spawn dan worker AI nyata pada frame kosong PASS. Tidak membuka kamera, menyimpan wajah atau mengubah database kerja. pip check PASS, tzdata2026.5 dipin eksplisit untuk fallback IANA di Windows. Syntax Python/spec dan tautan panduan diperiksa. Tidak ada klaim build Windows dari macOS atau klaim dukungan arsitektur yang belum diuji.

ONNX Runtime telemetry dimatikan melalui API resmi pada recognizer dan probe; ini tidak menggantikan uji offline Windows dengan internet diputus. Dokumentasi: https://onnxruntime.ai/docs/api/python/api_summary.html#onnxruntime.disable_telemetry_events.

Portabilitas backup: panggilan fchmod kini bersyarat karena Python3.11 menyediakan API tersebut hanya di Unix. Jalur POSIX tidak berubah; 8 tes codec dijalankan ulang termasuk simulasi API tidak tersedia. ACL Windows kemudian diuji pada kelanjutan Windows di atas. Referensi: https://docs.python.org/3.11/library/os.html#os.fchmod.

