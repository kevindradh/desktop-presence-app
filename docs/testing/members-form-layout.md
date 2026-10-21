# Form anggota dua kolom

Permintaan pengguna: kurangi lebar field dan jumlah baris dengan dua kolom.
Arah: mengikuti ruang kerja hijau StarGate yang sudah ada, ENERGY 1 / RHYTHM 2 / MOTION 1; tidak menambah warna, ikon atau animasi.

Susunan baru:

| Baris | Kolom kiri | Kolom kanan |
|---|---|---|
| 1 | ID anggota | Nama lengkap |
| 2 | Grup | Jabatan |
| 3 | Email | Telepon |
| 4 | Foto, pratinjau dan tombol pemilih foto melintasi area isian | |

Alasan: pasangan field memperpendek form dari delapan baris menjadi empat tanpa mempersempit pratinjau foto. Kedua kolom input berbagi lebar yang sama; jarak horizontal 20 px dan vertikal 12 px memisahkan label serta input. Font dan warna mengikuti tema aplikasi. Foto tetap berukuran 100×100 dan layout menetapkan tinggi minimum agar tidak terpotong saat data berubah.
Tab mengikuti urutan visual dari kiri ke kanan setiap baris, lalu menuju pemilih foto jika tombol tersebut aktif. Label dihubungkan dengan field melalui buddy Qt.

## Verifikasi

Empat tes UI Anggota lulus. Pengujian memeriksa pasangan field pada ukuran jendela 1000×740, 1180×820, dan 1440×900; posisi input berada di dalam form dan urutan Tab mengikuti susunan baru.
Pengeditan anggota, pergantian foto, pencarian/filter/pagination, pembatalan/nonaktif, penugasan shift dan pembatasan Operator tetap diuji melalui tes yang sudah ada.
Pratinjau, tombol foto, dan pembungkus area foto seluruhnya berada di dalam batas form setelah detail anggota dimuat.
Hasil: `evidence/members-two-columns.xml`. Gambar dengan data dan foto sintetis: `evidence/members-two-columns.png`.

## Delivery Gate perubahan form

- PASS, Hard Gate: tidak menambah klaim atau identitas; label dan fungsi lama dipertahankan. Keadaan data serta perizinan mengikuti layanan yang sama. Posisi input, foto dan urutan keyboard diperiksa dalam pengujian UI; tampilan dijalankan dan gambar diperiksa.
- PASS, Purpose-Gate: dua kolom mengikuti permintaan pengguna; label dan tombol foto tetap memakai font/warna lama. Tidak menambah aset, gradasi, badge, bayangan, atau animasi.
- PASS, Liveliness: ruang kerja StarGate dan dial di atas dipertahankan; pasangan field membentuk susunan form yang ringkas, tanpa dekorasi tambahan.
- PASS, Craftsmanship: alasan susunan/jarak ditulis di atas; empat regresi UI lulus dan tidak ada perubahan pada penyimpanan anggota maupun aturan registrasi wajah.
