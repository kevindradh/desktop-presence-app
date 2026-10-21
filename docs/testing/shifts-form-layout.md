# Form Shift yang ringkas

Arah mengikuti Grup dan Anggota atas permintaan pengguna: ruang kerja hijau StarGate, font sistem, ENERGY 1 / RHYTHM 2 / MOTION 1.

Nama shift berpasangan dengan Toleransi terlambat, lalu Jam mulai dengan Jam selesai. Dua kolom mengurangi jumlah baris sekaligus menempatkan pasangan jam berdampingan. Lebar input dibagi sama, dengan jarak horizontal 20 px dan vertikal 12 px seperti halaman Anggota. Label buddy dan urutan Tab mengikuti urutan visual; kontrol jam tetap memiliki bagian jam dan menit bawaan Qt.

Tombol menjadi Tambah, Simpan, Hapus, dan Muat ulang, konsisten dengan Grup. Petunjuk selesai hari yang sama/berikutnya tetap dinamis. Penjelasan panjang diganti lokasi penugasan dan aturan membuat shift baru untuk mengganti jam/toleransi yang sudah digunakan. Kalimat lama tentang fitur kehadiran yang belum tersedia dihapus karena fitur tersebut sudah tersedia. Nama shift tetap dapat diedit sesuai aturan layanan yang ada.

## Verifikasi dan Delivery Gate

- PASS, Hard Gate: delapan tes integrasi administrasi lulus, meliputi Grup, Shift, Anggota, penugasan dan pembatasan Operator. Form dijalankan dengan Qt offscreen pada 650×600, 900×720 dan 1180×820; input sejajar, terpisah dan berada dalam form. Tab melewati isian dengan urutan yang benar; Tambah mengosongkan draf. Petunjuk lintas hari diperiksa pada 20:00–04:00. Gambar hasil render ditinjau tanpa input/tombol terpotong. Status kosong, proses, galat, konfirmasi dan warna/kontras tetap mengikuti komponen lama. Tidak ada aset, klaim, atau tema baru.
- PASS, Purpose-Gate: setiap perubahan susunan/jarak dijelaskan di atas; warna dan font mengikuti halaman Anggota. Tidak menambah efek, ikon, badge, ilustrasi, atau animasi.
- PASS, Liveliness: dial eksplisit di atas; tabel menjadi fokus, form dan tindakan berurutan di bawahnya. Ruang antarbagian dan aksen hijau tetap mengikuti identitas aplikasi.
- PASS, Craftsmanship: layanan dan aturan penyimpanan tidak diubah; label tindakan singkat, petunjuk penting dipertahankan. Delapan regresi dan pemeriksaan keyboard/ukuran mendukung perilaku serta tata letak. Perubahan ini untuk aplikasi desktop.
- PASS, Copywriting: teks baru memakai istilah yang sudah ada, menyebut tindakan/lokasi secara langsung, tanpa klaim, jargon, atau tanda pisah panjang.

Bukti: `evidence/shifts-simple.xml` dan `evidence/shifts-simple.png` (halaman terpisah tanpa data nyata).

## Revisi petunjuk penugasan

Sesuai review pengguna, petunjuk lokasi Anggota > Penugasan shift dihapus. Keterangan membuat shift baru untuk mengganti jam/toleransi yang sudah digunakan tetap ditampilkan. PASS untuk copywriting dan Purpose-Gate: hanya menghapus kalimat lokasi yang tidak diperlukan; label tindakan, layout, dan perilaku tidak berubah. Bukti gambar di atas merupakan tampilan sebelum penghapusan kalimat ini.
