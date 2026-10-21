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

## Tab Data anggota dan Penugasan shift

Sesuai permintaan pengguna, form/foto/tindakan/riwayat kini berada pada tab Data anggota, sedangkan daftar dan form penugasan berada pada tab Penugasan shift. Pencarian, tabel anggota, dan pagination tetap di atas kedua tab.
Alasan: tab membuka bagian penugasan langsung tanpa melewati form data dan riwayat; pilihan anggota dan draf tidak direset saat berpindah tab. Membuka form baru kembali ke Data anggota. Penugasan yang berhasil tidak memindahkan tab.
Tombol tindakan dibagi menjadi baris pengelolaan anggota dan baris wajah agar ukuran minimum tab tidak memaksa gulir horizontal. Warna tab aktif mengikuti hijau StarGate; tab lain memakai putih dan penanda fokus keyboard.
Tanpa anggota terpilih, tab shift menampilkan petunjuk memilih anggota. Hak akses lama tetap berlaku: Operator dapat melihat penugasan tetapi tidak mendapatkan form perubahan shift.

Delapan tes antarmuka administrasi lulus, termasuk dua tab, Ctrl+Tab, perpindahan dengan klik, draf/anggota yang tetap dipilih, penggantian pilihan pada tab shift, form baru, penugasan/akhiri penugasan, serta pembatasan Operator. Tiga ukuran jendela pada tes anggota dan tab shift tidak memiliki gulir horizontal di area halaman.
Hasil: `evidence/members-tabs.xml`. Tangkapan layar sintetis yang diperiksa: `evidence/members-data-tab.png` dan `evidence/members-shift-tab.png`.
Delivery Gate: Hard Gate PASS, kontrol tab dan hak akses diuji; Purpose-Gate PASS, alasan tab/warna/tombol dicatat di atas; Liveliness PASS, arah dan dial tetap mengikuti tema StarGate; Craftsmanship PASS, delapan regresi lulus dan kedua tab ditinjau secara visual. Kriteria form yang tidak berubah mengikuti pemeriksaan sebelumnya.

## Tab ketiga: Riwayat kehadiran

Sesuai review berikutnya, riwayat dipindah dari Data anggota ke tab tersendiri: Riwayat kehadiran. Susunan menjadi Data anggota, Penugasan shift, Riwayat kehadiran. Pilihan anggota tetap digunakan bersama ketiganya.
Alasan: pengguna dapat membaca riwayat tanpa melewati form/foto dan dapat mengedit anggota tanpa tabel riwayat di bawahnya. Sisa tinggi tab Data anggota diarahkan ke ruang bawah, sehingga jarak antarfield tidak membesar.
Verifikasi mencakup klik dan Ctrl+Tab melalui tiga tab, draf serta pilihan anggota yang dipertahankan, satu baris riwayat anggota pertama, dan riwayat kosong saat memilih anggota lain tanpa berpindah dari tab Riwayat kehadiran.
Delivery Gate mengikuti pemeriksaan sebelumnya untuk arah, tema, kontras dan kontrol yang tidak berubah; pemisahan riwayat mengikuti pilihan pengguna dan tidak mengubah query ataupun penyimpanan kehadiran.
PASS: delapan uji administrasi lulus; bukti pada `evidence/members-three-tabs.xml`. Pratinjau sintetis tab ketiga diperiksa pada `evidence/members-history-tab.png`.

## Form shift dua kolom dan riwayat tanpa jumlah event

Form shift menjadi dua kolom sesuai permintaan: Shift berpasangan dengan Tanggal mulai, Tanggal akhir berpasangan dengan Tanpa tanggal akhir, dan Penugasan yang diakhiri berpasangan dengan Tanggal akhir berlaku. Tombol masing-masing tindakan berada setelah kelompok isiannya. Tujuannya memperpendek form tanpa mencampur tindakan menetapkan dan mengakhiri penugasan.
Jarak 20/12 px, label buddy, urutan Tab dan batas minimum ukuran mengikuti form anggota dua kolom. Kontrol tetap memakai tinggi bawaan Qt, sehingga dropdown dan tanggal sejajar menurut titik tengahnya.
Teks Riwayat tersimpan dan jumlah event tidak lagi ditampilkan ketika ada riwayat. Petunjuk saat belum memilih anggota atau belum ada riwayat tetap muncul; label disembunyikan tanpa ruang kosong ketika tabel berisi data.
PASS: delapan regresi administrasi lulus. Pemeriksaan meliputi penetapan/akhir penugasan, batas tanggal, tiga ukuran jendela, kolom di dalam form tanpa gulir horizontal halaman, pemisahan hak akses, riwayat terisi tanpa label jumlah, dan pesan riwayat kosong.
Delivery Gate mengikuti arah/tema sebelumnya: tata letak mempunyai alasan, kontrol menjalankan tindakan yang sama, tidak menambah klaim/angka, serta kedua tab diperiksa secara visual. Bukti: `evidence/members-shift-columns.xml`, `evidence/members-shift-two-columns.png`, dan `evidence/members-history-clean.png`.
