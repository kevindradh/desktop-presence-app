# Form Pengguna

Mengikuti permintaan pengguna, judul Pengguna di dalam halaman dihapus karena judul utama sudah disediakan shell. Pengantar pengelolaan akun, petunjuk mengganti password sendiri, petunjuk menonaktifkan akun, dan placeholder panjang password dihapus. Label Password awal menjadi Password.

Form dua kolom memasangkan Username/Nama lengkap dan Peran/Password, lalu Status di kiri. Jarak horizontal 20 px dan vertikal 12 px mengikuti Anggota/Grup/Shift. Label buddy dan Tab mengikuti urutan visual. Tombol menjadi Tambah, Simpan, Refresh dan Reset password; Reset password tetap menyebut objek tindakannya agar tidak tertukar dengan pengosongan form. Pesan hasil operasi dan galat dari controller tetap dapat tampil.

Arah tetap memakai tema hijau StarGate dan font sistem, ENERGY 1 / RHYTHM 2 / MOTION 1. Tabel menjadi area utama, diikuti form dan baris tindakan; tidak ada aset, warna, atau animasi baru.

## Verifikasi dan Delivery Gate

- PASS, Hard Gate: tiga tes integrasi lulus untuk pembuatan, pengeditan, reset password, nonaktifkan pengguna, penyimpanan yang menunggu polling, serta pembatalan saat sesi gagal. Form dijalankan dengan Qt offscreen pada 650×600, 900×720 dan 1180×820; input sejajar dan berada di dalam form. Tab Username/Nama lengkap/Peran/Password diperiksa. Render ditinjau tanpa teks atau kontrol terpotong; warna/kontras/fokus memakai tema yang sama. Tidak ada klaim/aset baru.
- PASS, Purpose-Gate: penghapusan judul menghindari duplikasi; dua kolom memperpendek form; jarak dan label tombol konsisten dengan halaman sebelumnya. Tidak menambah dekorasi atau efek.
- PASS, Liveliness: dial eksplisit di atas, tabel/form/tindakan tetap membentuk urutan kerja dan memakai aksen hijau StarGate.
- PASS, Craftsmanship: fungsi controller, validasi password, perizinan, dan pembatasan akun tetap sama. Pesan galat tidak dihapus. Penggantian label tidak mengubah reset password menjadi edit password langsung.
- PASS, Copywriting: teks baru menyebut tindakan secara singkat sesuai arahan pengguna, tanpa jargon atau klaim baru.

Bukti: `evidence/users-layout.xml` (3 tes lulus) dan `evidence/users-layout.png` (form terpisah tanpa data nyata).

## Keterangan Ganti password

Review pengguna berikutnya meminta penghapusan kalimat persyaratan panjang byte UTF-8 dan perbedaan password pada halaman Ganti password. Kalimat tersebut dihapus beserta ruang label melalui parameter deskripsi kosong. Validasi layanan tetap berlaku. Delivery Gate revisi teks PASS: tidak menambah kontrol, aset atau klaim; susunan isian, tema dan fungsi tetap sama. Diff diperiksa; tes fungsional tidak diulang untuk penghapusan satu keterangan saja.
