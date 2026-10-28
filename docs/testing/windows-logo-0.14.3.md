# Windows0.14.3: pembaruan logo

28 Oktober2026. Installer dibangun dan dipasang pada akun standar Windows11 ARM64 Parallels, menjalankan aplikasi x64. Source aplikasi mengikuti commit `bac91ef`. Cakupan pembaruan adalah logo pada panel aplikasi, sidebar, ikon executable dan installer, serta alas putih untuk ikon sistem operasi.

## Identitas paket

- File: `dist/windows/StarGate-Research-Windows-x64-0.14.3.exe`.
- Ukuran: 484,978,616byte.
- SHA256: `a4085e194f8e7245a5a774b2a00ed5d243389434f827c2901c9b68a159870917`.
- Versi resource Windows: `0.14.3.0`.
- Manifest: 6231berkas, SHA256 `7c1de13213223185bb404e786acbdd8e99f2575b3d79a75bf3615b1e63c82d83`.
- Authenticode: `NotSigned`. Installer belum ditandatangani.

[Metadata](evidence/windows-logo-0.14.3/artifact.json), [manifest](evidence/windows-logo-0.14.3/build-manifest.json).

## Hasil pemeriksaan

| Pemeriksaan | Hasil |
|---|---|
| Build PyInstaller dan Inno Setup | PASS; memakai build source Windows serta runtime/model yang sudah disiapkan |
| Ikon tertanam pada aplikasi dan installer | PASS; resource PE diekstrak melalui API Windows, piksel ukuran256cocok dengan ICO yang disetujui; kedua file memiliki7ukuran ikon |
| Ikon executable terpasang | PASS; cocok dengan aset disetujui dan hasil build |
| Logo pada panel dari PYZ/bundle terpasang | PASS;4panel, ikon putih16/32/48/128/256, form Super Admin muat1000×740 |
| Qt/plugin/native/spawn/model AI | PASS dari executable terpasang; model diberi frame kosong, bukan uji wajah asli |
| Schema | PASS; `0006_search_storage` |
| Jumlah data sebelum/sesudah | Sama:80anggota,4akun,2.467kehadiran,0embedding |
| Konfigurasi default dan ruang uji | SHA256 sebelum/sesudah sama |
| Launch aplikasi produksi | Proses diluncurkan dengan ruang uji yang sama dan masih hidup setelah5detik |
| Login/dashboard/taskbar melalui kendali live | Belum dikonfirmasi; frame Parallels tidak berubah melalui alat kendali |

Perbandingan data mencakup hitungan empat tabel, revision dan hash dua konfigurasi; bukan perbandingan setiap row/aset. Tidak mengekspor konfigurasi mentah, foto atau embedding. Regresi alat paket pada Mac16PASS/1SKIP; SKIP adalah tes model yang tidak diaktifkan pada run tersebut. Pemeriksaan model nyata dari executable Windows terpasang lulus secara terpisah.

Bukti: [instalasi](evidence/windows-logo-0.14.3/install.json), [data sebelum](evidence/windows-logo-0.14.3/data-before.json), [sesudah](evidence/windows-logo-0.14.3/data-after.json), [model](evidence/windows-logo-0.14.3/package-check.json), [UI bundle](evidence/windows-logo-0.14.3/frozen-ui.json), [ikon terpasang](evidence/windows-logo-0.14.3/installed-icon.png), [panel masuk](evidence/windows-logo-0.14.3/frozen-login.png).

## Catatan alat uji

UI diuji melalui helper yang memuat modul/PYZ hasil build dan resource aplikasi terpasang, menggunakan renderer offscreen Windows. Untuk renderer tersebut, font Segoe UI sistem didaftarkan eksplisit setelah render pertama menghasilkan glyph kosong. Ini pengaturan alat uji; kode/font aplikasi produksi tetap mengikuti tema yang sudah ada.

Assertions UI pertama lulus, tetapi wrapper gagal menghapus helper executable dengan WinError5 setelah child selesai. Penghapusan ulang berhasil; wrapper sekarang memiliki retry terbatas. Helper uji sudah dihapus dari folder aplikasi dan tidak masuk installer. Penyebab lock pertama tidak diklaim sudah terisolasi. [Catatan probe](evidence/windows-logo-0.14.3/probe-notes.json).

Screenshot offscreen bukan bukti login manual atau taskbar live. Percobaan kendali Parallels tetap menampilkan frame terminal yang sama, sehingga hasil tersebut tidak dipakai sebagai bukti visual aplikasi produksi.

## Menggunakan pembaruan

Di Parallels, gunakan pintasan **StarGate Uji Parallels** pada desktop; pintasan mengikuti executable yang sudah diperbarui dan ruang data simulasi yang sama. Akun uji mengikuti [panduan seeder](../school-seeder.md).

Untuk Windows lain, tutup StarGate kemudian jalankan installer0.14.3 pada akun pemakai. Ikuti [panduan setup otomatis](../windows-auto-setup.md). Paket0.14.2 dan arsip sebelumnya tetap disimpan.

Pengujian AMD fisik, kamera/spoof nyata, SLA dan penerimaan penuh tetap mengikuti [gerbang penerimaan](remaining-acceptance.md). Pembaruan logo tidak menutup gerbang tersebut.

## Arsip penyerahan

`dist/releases/StarGate-Research-Windows-x64-0.14.3.zip` berukuran487.174.817byte. SHA256: `08de2ffdf0a5749682148b7dde8113150390dfb5cd81acc2da13177e69c3cbf3`. Seluruh116berkas release dan225source diperiksa terhadap manifest, termasuk hash installer. Source tidak membawa bobot pretrained atau data privat. [Bukti verifikasi](evidence/windows-logo-0.14.3/release.json). Arsip merupakan snapshot sebelum catatan verifikasi arsip ini ditambahkan.
