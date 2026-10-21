# Form Grup

Mengikuti permintaan pengguna, halaman Grup tidak lagi menampilkan kalimat pembuka tentang pengelolaan grup dan riwayat. Nama grup dan Deskripsi berada dalam satu baris, masing-masing sebagai kolom isian. Tombol menjadi Tambah, Simpan, Hapus, dan Muat ulang.

Arah tetap mengikuti halaman Anggota: ruang kerja hijau StarGate, font sistem, ENERGY 1 / RHYTHM 2 / MOTION 1. Dua kolom memperpendek form dan membagi lebar input secara seimbang. Jarak horizontal 20 px mengikuti form Anggota; label tetap di samping input dan terhubung melalui buddy Qt. Urutan Tab dari Nama grup ke Deskripsi. Tidak ada aset, warna, atau animasi baru.

## Verifikasi dan Delivery Gate

- PASS, Hard Gate: aplikasi dijalankan dengan Qt offscreen. Form diperiksa pada ukuran 650×600, 900×720, dan 1180×820; kedua input sejajar dan berada dalam batas form. Tab menuju Deskripsi, tombol Tambah mengosongkan draf. Pengujian database terpisah lulus untuk membuat, mengedit, membatalkan penghapusan, menghapus, menolak penghapusan grup yang digunakan, serta memuat ulang. Status kosong, proses, dan galat tetap memakai layanan yang sama. Tidak ada klaim, aset, navigasi, atau tema baru; warna/kontras mengikuti tema sebelumnya.
- PASS, Purpose-Gate: susunan dan jarak mempunyai alasan di atas. Tidak menambah gradasi, ikon, badge, ilustrasi, bayangan, atau efek gerak.
- PASS, Liveliness: dial mengikuti halaman Anggota. Tabel menjadi area utama; form dan baris tindakan berada setelah tabel. Ruang antarbagian serta aksen hijau mengikuti identitas aplikasi.
- PASS, Craftsmanship: tindakan lama tetap berjalan melalui layanan berizin yang sama. Label singkat menyebut tindakan secara langsung, tanpa jargon, klaim, atau tanda pisah panjang. Gambar hasil render diperiksa; tidak ada input atau tombol yang terpotong. Dukungan perangkat tetap desktop.

Bukti: `evidence/groups-form.xml` (1 tes integrasi lulus) dan `evidence/groups-form.png` (halaman terpisah tanpa data nyata).
