# Panduan operasional StarGate

Panduan ini mengikuti aplikasi desktop yang dibangun untuk lomba, penelitian dan uji internal. Status pengujian serta batas versi tersedia pada [laporan Tahap15](testing/stage-15.md); panduan bukan pernyataan bahwa seluruh SLA sudah lulus.

## Mulai menggunakan

Pasang paket Windows sesuai [panduan installer](testing/stage-14-auto-manual.md). Pada pemasangan baru, buat Super Admin pertama lalu login. Password buatan sendiri tidak memaksa langkah ganti password. Pengguna dapat menggantinya lewat **Ganti password**. **Ingat saya** memakai penyimpanan kredensial sistem operasi; gunakan pada komputer dan akun Windows yang sesuai.

Untuk ruang simulasi yang disiapkan di Parallels, buka **StarGate Uji Parallels.cmd** pada desktop. Ruang ini terpisah dari konfigurasi sebelumnya dan berisi data SMP fiktif. Akun simulasinya dijelaskan pada [panduan seeder](school-seeder.md).

## Halaman menurut peran

| Peran | Halaman yang tersedia |
|---|---|
| Super Admin | Seluruh halaman, termasuk Pengguna, Audit aktivitas dan Cadangan dan pemulihan |
| Admin | Dashboard, Anggota, Grup, Shift, Perangkat, Kehadiran, Laporan, Pengaturan, Audit aktivitas, Pemeriksaan aplikasi |
| Operator | Dashboard, Anggota, Kehadiran, Laporan, Pemeriksaan aplikasi |
| Viewer | Laporan |

Layanan memeriksa izin saat membaca maupun menyimpan. Menyembunyikan menu bukan satu-satunya pemeriksaan akses. Reset password dan penonaktifan akun mencabut sesi sesuai aturan aplikasi. Jangan membagikan akun Super Admin untuk kegiatan harian.

## Grup, shift dan anggota

1. Buat grup sesuai kelas atau unit kerja.
2. Buat shift beserta jam mulai, selesai dan toleransi terlambat. Shift yang berakhir setelah tengah malam mengikuti tanggal mulai shift.
3. Di **Anggota**, isi ID, nama, grup dan informasi lain yang diperlukan. ID harus unik.
4. Pilih **Registrasi wajah**, kamera yang sesuai, lalu **Mulai**. Ikuti arahan depan, kiri, kanan, atas dan bawah. Auto capture membutuhkan wajah yang layak dan posisi yang stabil; **Capture** tersedia sesuai keadaan dialog.
5. Simpan setelah lima sudut lengkap. Pembatalan tidak mengganti set wajah lama. Registrasi ulang mengganti set lama setelah penyimpanan set baru berhasil.
6. Pada tab penugasan, pilih shift serta rentang tanggal. Hindari penugasan yang bertumpang tindih. Tab riwayat menampilkan peristiwa kehadiran yang tersimpan.
7. **Tes wajah** memeriksa kecocokan anggota terpilih tanpa membuat kehadiran baru.

Nonaktif anggota menghapus embedding dan foto kelolaan sesuai [kebijakan biometrik](biometric-retention.md); data anggota dan riwayat kehadiran dipertahankan. Untuk memakai biometrik kembali, anggota memerlukan registrasi wajah baru sesuai alur yang tersedia.

## Perangkat dan absensi

Tambahkan nama, lokasi, jenis kamera, resolusi/FPS dan sumber yang sesuai di **Perangkat**. Untuk RTSP, masukkan kredensial langsung pada aplikasi. Jangan mengirim URL yang berisi password melalui chat atau memasukkannya ke laporan pengujian.

Di **Kehadiran**, pilih kamera/perangkat dan mode yang diizinkan, lalu mulai absensi. Preview ditampilkan mirror; ini tidak berarti data pembanding harus dibalik. Preview yang berjalan belum membuktikan bahwa wajah lolos liveness atau identitas sudah cocok.

- Check-in ditolak sebelum shift mulai; tepat jam mulai boleh masuk.
- Tepat batas toleransi masih hadir tepat waktu; setelah batas itu terlambat.
- Jeda peristiwa mengikuti pengaturan, bawaan60detik. Mode **Masuk** tidak membuat IN ganda.
- Mode otomatis memilih peristiwa berikutnya berdasarkan status sesi. Orang yang tetap di depan kamera ditahan agar tidak langsung menghasilkan peristiwa berikutnya.
- Untuk scan berikutnya, tinggalkan area kamera agar wajah tidak terdeteksi setidaknya satu detik, lalu kembali setelah jeda cukup.
- Sukses/notifikasi mengikuti hasil transaksi yang telah tersimpan. Notifikasi yang hilang tidak menghapus catatan.
- Jika perangkat dicabut, hentikan proses dan periksa sumbernya sebelum mulai kembali. Jangan mengandalkan nomor kamera yang sama setelah perangkat berubah.

Checkout otomatis bersifat opsional dan memerlukan aplikasi terbuka dengan sesi berhak Kehadiran. Peristiwa otomatis bukan bukti peserta secara fisik tetap ada sampai akhir shift. Rincian batas IN/OUT/istirahat dan skenario uji ada di [Tahap10](testing/stage-10.md).

## Dashboard dan laporan

Pilih tanggal kerja pada dashboard; **Hari ini** kembali mengikuti tanggal saat ini. Hadir mencakup yang terlambat. Belum masuk berlaku sebelum shift selesai; tidak hadir baru dihitung sesudah shift selesai jika tidak ada check-in/izin yang sesuai.

Pada **Laporan**, pilih rentang tanggal, grup, anggota, shift dan status yang diperlukan. Ekspor XLSX/PDF memakai seluruh snapshot hasil filter, termasuk baris di halaman lain. Bila data berubah setelah laporan dimuat, refresh laporan untuk membuat snapshot baru sebelum ekspor. Periksa filter dan zona waktu sebelum menyerahkan laporan.

## Cadangan dan pemulihan

Hanya Super Admin yang membuka **Cadangan dan pemulihan**. Buat cadangan dengan kata sandi tersendiri dan simpan kata sandinya dengan aman. Cadangan terenkripsi tidak menggantikan pengaturan akses media penyimpanannya. Retensi operasional yang disetujui adalah7hari; salinan eksternal perlu dikelola pemiliknya.

Sebelum restore, hentikan kegiatan pada terminal lain, periksa isi/identitas cadangan, dan pastikan cadangan masih berlaku. Restore mengganti data bisnis serta sesi dengan snapshot, membuat pengaman sesuai prosedur, dan memerlukan login kembali. Foto serta embedding tidak dipulihkan untuk pengenalan; anggota harus registrasi wajah ulang. Tinjau akun aktif dan sumber RTSP sesudah pemulihan.

Rincian validasi, kata sandi pengaman, kondisi transaksi ambigu dan kerusakan total ada di [prosedur Tahap13](testing/stage-13.md). Jika koneksi hilang saat konfirmasi restore, periksa keadaan aktual sebelum mencoba ulang.

## Jika terjadi masalah

| Gejala | Langkah awal |
|---|---|
| Database belum siap | Tutup aplikasi, periksa ruang disk dan jalankan pemeriksaan setup pada panduan Windows; jangan menghapus folder database |
| Kamera tidak muncul/berhenti | Periksa izin kamera dan sambungan ke Windows melalui menu USB Parallels; hentikan pemakai kamera lain |
| Wajah tidak diterima | Periksa pencahayaan, posisi, ukuran wajah, penugasan, status anggota dan pesan aplikasi; jangan menurunkan anti-spoof hanya untuk membuat tes lulus |
| Data tidak berubah setelah simpan | Periksa pesan konflik, refresh dan tinjau nilai terkini sebelum menyimpan ulang |
| Ekspor gagal | Pastikan folder dapat ditulis dan berkas tujuan tidak sedang dibuka |
| Toast error muncul | Catat nomor referensi, langkah dan waktu. Simpan log untuk pemeriksaan; jangan menyertakan password, foto, embedding atau URL kredensial |

Data Windows berada di `%LOCALAPPDATA%\StarGate` untuk pemasangan biasa. Runtime aplikasi berada di `%LOCALAPPDATA%\Programs\StarGate`. Uninstall mempertahankan data pengguna. Jangan memakai `fresh` atau menghapus folder data sebagai langkah perbaikan umum. Prosedur reset testing yang memang disengaja ada di [panduan fresh](database-fresh.md).
