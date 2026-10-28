# Kandidat rilis penelitian StarGate

Tanggal: 28 Oktober 2026. Kandidat ini ditujukan untuk lomba, penelitian dan pengujian internal sesuai pilihan pengguna. Gerbang penerimaan tetap mengikuti [PLAN](../PLAN.md) dan hasil aktual; status paket tidak berarti seluruh target akurasi/SLA telah terbukti.

## Kandidat terbaru0.14.3

Paket Windows0.14.3 memuat logo di panel aplikasi dan sidebar serta ikon berlatar putih pada executable/installer. Installer sudah dipasang pada akun standar Parallels; model, resource UI, schema serta hitungan data/hash konfigurasi lulus pemeriksaan. [Laporan pembaruan](testing/windows-logo-0.14.3.md) membedakan pengujian offscreen dan pemeriksaan live yang belum terkonfirmasi.

Installer berukuran484,978,616byte; SHA256 `a4085e194f8e7245a5a774b2a00ed5d243389434f827c2901c9b68a159870917`. Belum ditandatangani Authenticode. Riwayat0.14.2 di bawah tetap menjadi bukti putaran sebelumnya; metrik performa/biometrik tidak diukur ulang pada pembaruan logo ini.

## Isi penyerahan

- Installer Windows x64 yang sudah diperiksa beserta hash dan metadata artefaknya.
- Source build kit dengan manifest SHA256; tidak membawa `.env`, database, foto anggota, embedding, backup, log atau virtual environment.
- Panduan operasi, instalasi, arsitektur, database, retensi, hasil uji, dan daftar batasan.
- Notice dependency serta daftar berkas release yang dapat diverifikasi.

Bobot pretrained tidak disalin ke source kit. Manifest model dan petunjuk asalnya tetap disertakan; gunakan aset penelitian yang sesuai checksum dan izin penggunaan ketika membangun ulang. Installer penelitian dapat menyertakan bobot tersebut melalui flag build yang sebelumnya disetujui. Periksa [notice pihak ketiga](../packaging/THIRD_PARTY_NOTICES.md) sebelum menyerahkan binary atau source ke pihak lain. Dokumen ini tidak menetapkan lisensi baru untuk kode milik pengguna.

## Perubahan0.14.2

Source0.14.2 menambahkan jalur exact satu hasil tanpa pengelompokan seluruh anggota serta migrasi `0006_search_storage`. Migrasi menyimpan baris512D secara inline dan menata ulang nilai lama tanpa mengubah vektor, model, pose, status aktif atau riwayat. Jalur multi-hasil tetap mengelompokkan sampel per anggota. Ambang similarity, anti-spoof dan algoritme cosine tetap dipertahankan.

Perbandingan hasil sebelum/sesudah dan identitas paket akhir ada pada [Tahap15](testing/stage-15.md). Angka percobaan optimasi belum menggantikan hasil pengukuran paket akhir. Revisi source memiliki47tes terarah lulus, termasuk kesamaan hasil top-one/multi-hasil dan data sebelum/sesudah migrasi. Regresi akhir538PASS/1SKIP dan build Windows0.14.2 selesai; p95 produksi50,92ms, dengan3dari1.000query di atas100ms. Target seluruh query tetap terbuka.

## Pemasangan dan pemulihan

1. Cocokkan SHA256 installer dengan metadata artefak dari paket yang diterima.
2. Tutup aplikasi sebelum memperbarui. Simpan cadangan terenkripsi yang masih berlaku sesuai [prosedur cadangan](testing/stage-13.md).
3. Jalankan installer pada akun Windows pemakai. Konfigurasi eksternal yang sudah ada tetap dipertahankan; migrasinya mengikuti pemeliharaan eksplisit.
4. Jika memakai folder data khusus melalui `--data-dir`, hentikan cluster folder tersebut sebelum mengganti runtime, lalu jalankan `setup-local --data-dir <folder>` setelah pemasangan. Rig Parallels melakukan langkah ini untuk ruang uji terpisah.
5. Verifikasi schema, login, data anggota dan satu alur uji sebelum dipakai lebih luas. Migrasi penyimpanan melakukan penulisan ulang; sediakan ruang disk dan waktu pemeliharaan.

Untuk build dari source di Windows, ikuti [panduan pembuat paket](windows-install.md), gunakan pin Windows dan runtime PostgreSQL/pgvector yang sesuai. Lock macOS tidak menggantikan lock Windows.

Jika pembaruan gagal sebelum migrasi, pertahankan folder data dan baca log. Jika sudah bermigrasi, jangan menyalin folder PostgreSQL atau menghapus tabel untuk menurunkan versi. Periksa migrasi serta cadangan pada lingkungan pemulihan terpisah. Restore cadangan aplikasi membuang biometrik dan memerlukan registrasi ulang sesuai kebijakan.

## Batas penerimaan

Pengguna menyatakan belum mempunyai catatan uji nyata untuk akurasi, spoof dan availability. Tidak ada angka buatan untuk menutup persyaratan tersebut. AMD fisik, USB kedua dan RTSP positif juga masih mengikuti pengujian yang ditunda.

Kandidat boleh disiapkan untuk review internal. Status V1 selesai penuh tetap menunggu bukti pada daftar penerimaan dan persetujuan hasil pengguna. Menguji Parallels membantu menemukan masalah, tetapi tidak membuktikan semua perangkat AMD atau kondisi lapangan lulus.

## Identitas installer0.14.2

Installer `StarGate-Research-Windows-x64-0.14.2.exe` berukuran484.054.536byte. SHA256: `89277805552ba765accff229722d2c662849a795729700280bc23b470ae1b946`. Metadata dan manifest6227berkas berada pada [bukti build](testing/evidence/stage-15-final-windows/artifact.json). Installer belum ditandatangani Authenticode (`NotSigned`). Identitas ini terpisah dari installer0.14.1 yang dipertahankan.

Pemeriksaan source membandingkan hash repository pencarian, migrasi0006, definisi installer, spec, notice dan skrip build dengan source Windows. Build pertama gagal karena atribut READONLY pada hasil lama; setelah persiapan keluaran diperbaiki, build diulang tanpa --clean dengan cache yang tersedia; PyInstaller tetap memeriksa/membangun ulang tahap yang diperlukan dan runtime/manifest disusun kembali. Tidak menyebut pengulangan ini sebagai build bersih baru. Rincian pemeriksaan paket terpasang ditambahkan pada laporan Tahap15.

Batas kandidat yang teramati: PERF-B001 masih mencatat3query di atas100ms, dan CAM-B004 mencatat kegagalan kamera pertama meskipun pengulangan lulus. Lihat [laporan akhir](testing/stage-15.md) sebelum menentukan cakupan UAT.
