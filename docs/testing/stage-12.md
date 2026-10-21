# Tahap 12 - Laporan dan ekspor Excel/PDF

Tanggal: 20 Oktober 2026. Review Tahap 11 diterima dan lanjut Tahap 12 diizinkan. Implementasi/verifikasi teknis Tahap 12 PASS; review pengguna disetujui 20 Oktober 2026 dan lanjut Tahap 13 diizinkan.

## Format yang disetujui

Pengguna menyetujui pada 20 Oktober 2026: satu baris per anggota, shift, dan tanggal kerja; jam masuk/keluar, istirahat, status Hadir/Terlambat/Absent/Izin/Belum masuk dan pulang awal. Ekspor mencakup **seluruh hasil filter**, bukan hanya halaman yang sedang terlihat.

Menu Laporan tersedia untuk seluruh peran yang memiliki permission reports, termasuk Viewer. Viewer tetap hanya dapat membuka Laporan. Pilihan periode Harian, Mingguan (Senin-Minggu), Bulanan dan Rentang khusus mengatur rentang tanggal inklusif. Filter tersedia untuk grup, pencarian ID/nama anggota, shift dan status. Filter Hadir (termasuk terlambat) menerima PRESENT/LATE; Hadir tepat waktu dan Terlambat juga dapat dipilih terpisah.

Tanggal laporan adalah **tanggal kerja saat shift dimulai**. Shift malam yang keluar lewat tengah malam tetap pada baris tanggal awal shift, dengan waktu penuh pada laporan/ekspor. Nama/kode/shift/perangkat memakai label yang tersedia saat pemuatan; grup untuk sesi IN berasal dari group_id historis saat IN. Riwayat tetap ada setelah anggota nonaktif.

Tanpa IN, sumber laporan adalah penugasan aktif, izin dan kalender LOCAL, mengikuti D-13/Tahap 11: Belum masuk sebelum akhir shift, Absent mulai akhir shift, Izin dari catatan izin, tanggal nonkerja tidak membuat absensi palsu. Penugasan bertumpang tindih atau event tanpa IN ditandai **Perlu diperiksa**, bukan dipaksakan menjadi Hadir/Absent. Ini perhitungan dari sumber saat dimuat, bukan rekonstruksi versi lama penugasan/izin/keaktifan yang belum disimpan. Penugasan tanpa lokasi tetap memakai zona organisasi/kalender LOCAL pada deployment satu lokasi; editor izin/kalender belum ditambahkan.

## Snapshot, pagination dan file

Klik **Tampilkan laporan** untuk membangun hasil. UI menampilkan 50 baris per halaman, tetapi Excel/PDF memakai semua baris dari hasil yang sama. Filter berubah akan mengosongkan hasil dan menonaktifkan ekspor sampai dimuat ulang. Tidak ada polling yang menimpa filter/fokus. Absensi baru yang tersimpan setelah hasil ditampilkan tidak menyusup ke ekspor; muat ulang untuk memasukkannya. Waktu pemuatan, zona dan seluruh filter ditulis pada metadata file.

Snapshot hanya berada di memori layanan, terikat token sesi, maksimal dua hasil per instance dan berlaku 15 menit. Hak/sesi diperiksa saat pemuatan, permintaan ekspor dan sebelum publikasi file. Batas satu permintaan: paling lama 366 hari, maksimal 50.000 kandidat baris dan 200.000 event. Melebihi batas menghasilkan pesan untuk mempersempit filter, bukan file terpotong yang dilaporkan sukses. Batas kandidat diterapkan sebelum status diturunkan; filter grup/anggota/shift atau rentang yang lebih sempit dapat digunakan.

**Excel** memakai Pandas/OpenPyXL sesuai PRD. Sheet Kehadiran memuat ringkasan semua baris, sheet Detail event memuat event terkait untuk baris yang lolos filter. Keduanya mempunyai metadata, tanggal/waktu bertipe tanggal, header filter, pembekuan identitas/header dan pembungkusan teks. Nama/ID diawali `=` tetap literal, bukan formula. Sel kosong tetap kosong, bukan jam masuk palsu. File merupakan snapshot, bukan workbook model yang menghitung absensi ulang saat diedit.

**PDF** memakai ReportLab, A4 landscape, header tabel berulang, pembungkusan nama panjang, nomor halaman dan metadata periode/zona. Baris normal dijaga utuh; baris yang terlalu tinggi untuk satu halaman dapat berlanjut. Istirahat berulang tetap ditulis lengkap. Font Vera bawaan ReportLab disematkan untuk karakter yang didukung; CJK memakai CID standar HeiseiMin-W3 dan telah dirender pada lingkungan macOS ini. Karakter di luar cakupan font (misalnya emoji tertentu) menghasilkan pesan untuk memakai Excel, bukan diganti kotak secara diam-diam. Portabilitas font/reader dan distribusi Windows tetap diuji pada Tahap 14.

Ekspor berjalan pada worker dengan progress dan pembatalan. Data ditulis ke file sementara privat pada folder tujuan; file akhir dipublikasikan hanya setelah selesai dan hak akses diperiksa kembali. Batal/error sebelum publikasi membersihkan file sementara dan tidak mengganti file lama. File yang sudah selesai dipublikasikan dilaporkan sukses walaupun tombol batal ditekan pada saat publikasi. Save dialog meminta konfirmasi untuk file yang sudah ada; tanpa izin overwrite, tujuan yang muncul bersamaan tidak ditimpa. Publikasi tanpa overwrite memakai hard link satu filesystem; filesystem yang tidak mendukungnya menampilkan kegagalan simpan, bukan fallback yang menimpa file. Lokasi tidak dapat ditulis/file sedang dikunci ditangani dengan pesan aman.

Tidak ada migrasi/dependensi runtime baru. Data foto, embedding, token sesi dan kredensial RTSP tidak dimasukkan ke laporan. Laporan berisi identitas serta kehadiran sesuai role Reports; lokasi penyimpanannya dipilih pengguna. Audit lengkap dan backup/restore tetap Tahap 13.

## Demo cepat

```bash
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/demo_reports.py
```

Demo menggunakan akun **Viewer**, 65 baris sintetis, contoh status izin/absent/terlambat dan nama Unicode/panjang. Login, filter awal dan pemuatan laporan disiapkan otomatis. Data berada pada schema sementara milik demo di stargate_test, bukan data operasional. Tutup normal membersihkan schema sendiri; jangan menyapu schema lain bila demo pernah dipaksa berhenti.

1. Pastikan halaman pertama menampilkan **1-50 dari 65**. Klik Berikutnya: **51-65 dari 65**.
2. Dari halaman kedua, klik Ekspor Excel dan pilih folder/nama file. Buka file: sheet Kehadiran harus berisi **65 baris data**, bukan 15. Detail event hanya berisi event yang benar-benar tercatat, tidak mengarang event untuk Absent/Izin/Belum masuk.
3. Klik Ekspor PDF dan pilih folder/nama lain. Buka beberapa halaman, termasuk halaman akhir; nama panjang/Unicode, header, nomor halaman dan total periode harus terbaca.
4. Pilih status Terlambat, klik Tampilkan laporan: contoh awal satu baris. Ekspor harus sama-sama satu baris. Coba grup, shift serta pencarian nama/ID; setelah filter diubah, ekspor tidak aktif sebelum dimuat ulang.
5. Pilih nama yang tidak ada: tampilkan dan ekspor. Hasil menyatakan tidak ada data, dengan filter/periode tetap benar.
6. Coba Harian, Mingguan, Bulanan dan Rentang khusus. Jangan mengganti jam sistem. Penugasan contoh demo hanya satu tanggal, sehingga periode yang lebih lebar tidak mengarang jadwal tambahan.
7. Untuk membatalkan, gunakan Batalkan proses saat proses masih berjalan. File kecil dapat selesai sebelum tombol sempat ditekan; pembatalan terkontrol, revoke dan write failure juga diuji otomatis.
8. Tutup/buka demo untuk mengulang data awal. Contoh file yang sudah Anda simpan tetap berada di lokasi pilihan Anda; pembersihan demo hanya menyentuh data sementara demo.

## Uji mandiri pada aplikasi utama

Tutup aplikasi lama, buka `main.py` dan menu Laporan. Gunakan anggota/tanggal uji yang riwayatnya diketahui, termasuk satu sesi malam dan event istirahat bila tersedia. Cocokkan satu baris dengan IN/OUT/break di riwayat anggota; Hadir/Terlambat berasal dari IN, sedangkan Izin/Absent/Belum masuk dari jadwal. Jangan menjumlah semua event sebagai orang hadir.

Periksa grup historis, anggota nonaktif yang mempunyai riwayat, tanggal awal/akhir inklusif dan OUT malam pada tanggal kerja sebelumnya. Simpan Excel/PDF dari filter yang sama, bandingkan semua halaman. Bila ada scan baru pada proses lain, hasil yang sudah dimuat dan ekspor tetap konsisten; klik Tampilkan laporan lagi untuk memperoleh versi terbaru. Jangan mematikan database development untuk memaksakan kegagalan.

Laporan masalah cukup berisi filter, zona/waktu pemuatan, jumlah baris yang diharapkan/terlihat, format file, langkah dan pesan. Jika membagikan file dari data nyata, hapus identitas yang tidak diperlukan. Contoh otomatis pada repository hanya memakai data sintetis.

## Bukti dan batas pengujian

Regresi lengkap: **399 PASS**, nol failure/error/skip, durasi **399,25 detik**. Coverage run tersebut **90,11% (6525/7241 statements)**. Setelah run lengkap, filter UI diringkas dan pemisahan baris PDF dirapikan; kedua perubahan tampilan diverifikasi kembali melalui **13 tes ekspor final PASS** dan **65 tes native macOS PASS** (162,11 detik). Coverage penuh tidak dihitung ulang untuk perapian tampilan tersebut. Satu FutureWarning upstream InsightFace/scikit-image tetap terlihat.

Pengujian terarah awal 33 PASS mencakup layanan, ekspor, UI dan task lifecycle. PDF final contoh **71 baris / 24 halaman** diekstrak dengan Poppler untuk mencocokkan seluruh ID, jumlah halaman dan header/footer; halaman 1, 12 dan 24 ditinjau visual setelah perapian. XLSX dibuka kembali dengan OpenPyXL: 71 baris, dua sheet, nilai tanggal/waktu bertipe serta format eksplisit benar. File juga diimpor/dirender memakai runtime artifact tool untuk pemeriksaan visual kedua sheet, tanpa mengubah sumber. Microsoft Excel/reader Windows belum diuji native; ini tetap bagian Tahap 14. Pembuatan file aplikasi tetap Pandas/OpenPyXL dan ReportLab sebagaimana ketentuan proyek.

Bukti: [regresi lengkap](evidence/stage-12-tests.xml), [ekspor final](evidence/stage-12-export-final.xml), [native macOS](evidence/stage-12-native.xml), [ringkasan](evidence/stage-12-summary.json), [tampilan Viewer](evidence/stage-12-reports.png), [XLSX sintetis](evidence/stage-12-synthetic.xlsx), [PDF sintetis](evidence/stage-12-synthetic.pdf), [PDF awal](evidence/stage-12-pdf-first.png), [PDF tengah](evidence/stage-12-pdf-middle.png), [PDF akhir](evidence/stage-12-pdf-last.png), [metadata Excel](evidence/stage-12-xlsx-metadata.png), [ringkasan Excel kiri](evidence/stage-12-xlsx-summary-left.png), [ringkasan Excel kanan](evidence/stage-12-xlsx-summary-right.png), [detail event Excel](evidence/stage-12-xlsx-events.png). Coverage run lengkap tersimpan lokal di .local/stage-12-coverage.json.

Pemeriksaan database operasional **baca saja** PASS pada revision 0004_devices, at_head/schema_valid true dan 14 tabel aplikasi. Tidak ada migrasi, perubahan dependency runtime, penulisan data operasional atau pengambilan wajah nyata baru. Semua contoh di atas sintetis. Tidak ada sesi tes yang masih berjalan; review pengguna dan Tahap 13 tetap terpisah.

Referensi MCP Context7: [Pandas ExcelWriter](https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html), [Pandas to_excel](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html), [ReportLab font Unicode](https://docs.reportlab.com/reportlab/userguide/ch3_fonts/), [ReportLab tabel](https://docs.reportlab.com/reportlab/userguide/ch7_tables/). Poppler dan artifact runtime adalah alat QA lingkungan pengembangan, bukan dependensi runtime baru aplikasi.
