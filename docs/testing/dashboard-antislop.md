# Review Dashboard dengan antislop

Tanggal: 21 Oktober 2026. Mode: during, dipilih pengguna dalam percakapan.
Lingkup: Dashboard desktop PyQt6. Sidebar dan halaman lain mengikuti tampilan yang sudah ada.

## Arah dan alasan desain

Reading this as: Dashboard kehadiran untuk pengelola, dalam gaya hijau StarGate yang tenang, ENERGY 1 / RHYTHM 2 / MOTION 1.
Arah berasal dari antarmuka StarGate yang sudah digunakan dan revisi pengguna: judul sederhana, tanpa chip pratinjau dan tanpa footer petunjuk.

- Warna: hijau StarGate menandai Hadir; jingga tetap membedakan Terlambat pada grafik.
- Susunan: Hadir menjadi fokus, diikuti status pendukung, aktivitas, lalu grafik untuk penelusuran lebih lanjut.
- Tipografi: font sistem mengikuti kebiasaan aplikasi desktop macOS/Windows; angka Hadir lebih besar agar mudah ditemukan.
- Jarak: sela 18 px memisahkan bagian; padding 22/20 px mengelompokkan ringkasan tanpa enam kartu terpisah.
- Kartu: satu panel menyatukan angka yang saling berkaitan; pasangan panel grafik memudahkan perbandingan shift/grup dan dua rentang waktu.
- Ikon dan gambar: tidak ditambahkan karena angka, label, dan grafik sudah menyampaikan informasi yang diperlukan.
- Gerak: tidak ada animasi dekoratif; pembaruan data tetap memakai polling yang menjaga fokus input.
- Tema: ruang kerja terang yang sudah menjadi identitas StarGate dipertahankan untuk membaca tabel; tidak ada toggle tema baru.

## Perubahan teks dan keadaan data

Label Absent pada Dashboard menjadi Tidak hadir, dengan istilah asal pada tooltip. Perhitungan tidak berubah.
Hadir tetap mencakup Terlambat. Belum masuk dan Tidak hadir tetap mengikuti akhir shift.
Tooltip Anggota aktif menjelaskan bahwa jumlahnya mengikuti keadaan saat ini, bukan tanggal historis.
Jumlah 20 catatan, 12 shift/grup, 30 hari, dan 12 bulan berasal dari batas query di `DashboardService`.
Tampilan memuat memakai titik-titik, bukan angka nol. Kegagalan awal menampilkan data belum tersedia.
Jika pembaruan gagal setelah pernah berhasil, angka terakhir tetap terlihat bersama pesan data belum diperbarui.
Pesan aktivitas kosong hanya muncul setelah pemuatan berhasil.

## Bukti pengujian

- Pengujian Qt offscreen menjalankan jendela aplikasi dan database PostgreSQL uji, memakai schema sementara dan data sintetis.
- Hasil UI: 12 lulus, tanpa kegagalan atau error; `evidence/dashboard-antislop-ui.xml`.
- Pengujian layanan Dashboard: 15 lulus pada pemeriksaan gabungan sebelum pengujian UI akhir; layanan perhitungan tidak diubah.
- Tangkapan layar: `evidence/dashboard-antislop/`. Nama dan angka pada gambar adalah data uji, bukan hasil penelitian.
- Ukuran jendela: 1000×740, 1180×820, 1440×900; tidak ada gulir horizontal pada area Dashboard.
- Kalender: klik tombol kalender membuka popup; Escape menutupnya.
- Keyboard: Tab melewati bagian tanggal menuju Ikuti hari ini; Space mematikan dan mengaktifkannya.
- Tanggal: pemilihan tanggal lain mematikan Ikuti hari ini dan memuat data tanggal tersebut; hasil permintaan lama diabaikan.
- Polling: perubahan dari terminal lain tampil otomatis, fokus tanggal tetap, kamera dan heartbeat antarmuka tetap berjalan.
- Navigasi, keluar akun, dan tutup jendela saat pemuatan menghentikan polling; sesi dicabut menghapus data dari tampilan.
- Demo: tombol check-in terminal lain memperbarui Dashboard; tombol akhir shift memajukan waktu simulasi.
- Peringatan plugin offscreen tentang aktivasi/grab keyboard adalah keterbatasan lingkungan Qt uji; bukan pengujian native Windows.
- Installer Windows belum dibangun ulang untuk revisi ini.

## Delivery Gate

Status berikut berlaku untuk perubahan Dashboard desktop ini. Mobile bukan target aplikasi; ukuran desktop minimum mengikuti batas jendela aplikasi.

| Pemeriksaan | Status dan bukti |
|---|---|
| R-02, tanda pisah panjang | PASS: teks Dashboard memakai titik, koma, atau kurung; placeholder memakai titik-titik. |
| R-03, tata letak | PASS: tiga ukuran desktop diuji; angka berada dalam panel, filter tidak bertabrakan, area Dashboard tanpa gulir horizontal. |
| R-17, angka | PASS: angka berasal dari snapshot layanan; angka batas mengikuti query yang sudah ada. |
| R-18, testimoni | PASS: tidak ada testimoni. |
| R-23, aset | PASS: tidak membuat logo, foto, avatar, atau struktur navigasi baru. |
| R-24, navigasi | PASS: tidak menambah tautan; pengujian meninggalkan Dashboard melalui rute anggota yang tersedia. |
| R-25, kontras | PASS: teks utama pada putih 12,15:1; muted pada putih 5,05:1 dan latar ruang kerja 4,68:1; angka hijau pada putih 7,16:1. Angka sumbu grafik kini memakai warna muted. |
| R-26, kontrol | PASS: kalender membuka/menutup; tanggal memuat snapshot lain; checkbox mengubah pengikutan tanggal. |
| R-27, keadaan data | PASS: loading, kosong, error awal, data lama saat error, dan pemulihan diuji. |
| R-28, FAQ | PASS: tidak ada FAQ. |
| R-32, keyboard | PASS: Tab dan Space diuji; fokus tanggal dan checkbox memiliki bingkai hijau; Escape menutup kalender. |
| R-33, perubahan sumber | PASS: perubahan ditulis langsung pada widget dan stylesheet; tidak menambah skrip penambal. |
| R-34, tema | PASS: tema terang yang dikirim tetap digunakan; tidak ada toggle dengan tema yang tidak berfungsi. |
| R-35, dijalankan | PASS: jendela Qt dijalankan dalam tes offscreen; daftar interaksi tercatat di atas dan tangkapan layar diperiksa. |
| R-36, klaim | PASS: tidak menambah klaim keamanan, performa, atau akurasi. |
| R-37, arah | PASS: Design Read dan ketiga dial dinyatakan sebelum perubahan, mengikuti identitas StarGate yang ada. |
| R-38, isi | PASS: data operasional berasal dari layanan; bukti demo dilabeli sintetis. |
| R-01, gradasi/glow | PASS: tidak memakai gradasi atau glow; hijau mengikuti identitas yang sudah ada. |
| R-04, ikon | PASS: tidak menambah ikon dekoratif. |
| R-06, tipografi | PASS: font sistem untuk keterbacaan desktop; tidak menambah monospace atau label kapital dekoratif. |
| R-07, latar berpola | PASS: latar ruang kerja polos, tanpa grid dekoratif. |
| R-08, panah | PASS: tidak menambah panah pada CTA; panah kalender merupakan kontrol bawaan. |
| R-09, badge | PASS: tidak menambah badge. |
| R-10, kaca | PASS: tidak memakai blur atau glassmorphism. |
| R-12, bayangan | PASS: panel memakai batas tipis tanpa bayangan. |
| R-13, glow | PASS: tidak ada efek glow. |
| R-14, kartu | PASS: enam kartu status diganti satu ringkasan; panel grafik berpasangan untuk perbandingan data. |
| R-19, animasi | PASS: tidak menambah animasi; polling tidak mengambil fokus input. |
| R-22, ilustrasi | PASS: tidak menambah ilustrasi. |
| Dial dinyatakan | PASS: ENERGY 1 / RHYTHM 2 / MOTION 1. |
| Dial sesuai hasil | PASS: warna tenang, susunan ringkasan/tabel/grafik bervariasi, tanpa animasi dekoratif. |
| Fokus utama | PASS: angka Hadir 48 px, angka pendukung 25 px. |
| Ruang sebagai struktur | PASS: panel ringkasan, daftar aktivitas, dan pola kehadiran dipisahkan dengan jarak dan judul. |
| Aksen | PASS: hijau pada angka Hadir; jingga hanya untuk membandingkan keterlambatan di grafik. |
| Identitas | PASS: hijau StarGate, bahasa Indonesia, tanggal kerja dan hubungan Hadir/Terlambat menjadi motif tampilan. |
| Design Read | PASS: arah dinyatakan dalam percakapan sebelum pembuatan dan dicatat di atas. |
| C-1, alasan | PASS: alasan warna, susunan, font, jarak, kartu dan ketiadaan ilustrasi dicatat di atas. |
| C-2, fungsi | PASS: filter dan checkbox memiliki interaksi yang diuji; tidak ada tombol baru tanpa fungsi. |
| C-3, isi | PASS: bagian mengikuti kebutuhan pemantauan kehadiran, bukan bagian pemasaran. |
| C-4, ketahanan | PASS: keadaan data, keyboard, fokus saat polling dan tiga ukuran desktop diuji. |
| C-5, bukti | PASS: layanan menjadi sumber angka; tangkapan layar demo dijelaskan sebagai data sintetis. |
| R-05, susunan | PASS: ringkasan, tabel dan grafik memiliki komposisi sesuai jenis informasi masing-masing. |
| R-11, radius | PASS: panel memakai radius 11 px mengikuti tema; kontrol tidak dibuat berbentuk kapsul. |
| R-15, CTA | PASS: Ikuti hari ini menyatakan perilakunya; tidak ada CTA pemasaran. |
| R-16, kata kosong | PASS: teks menjelaskan status dan hitungan, tanpa klaim AI atau kata pemasaran. |
| R-20, karakter | PASS: hierarki Hadir dan status turunan mengikuti aturan kehadiran StarGate yang sebenarnya. |
| R-21, tema | PASS: mempertahankan ruang kerja terang StarGate untuk membaca angka dan tabel; tidak memaksakan tema gelap. |
| R-29, palet | PASS: hijau dan jingga, ditambah latar dan teks netral. |
| R-30, orisinalitas | PASS: komposisi berasal dari isi Dashboard yang ada, tanpa meniru produk lain. |
| R-31, keputusan | PASS: setiap keputusan utama mempunyai alasan satu baris di bagian arah desain. |

## Pemeriksaan copywriting

PASS: tidak ada angka atau fitur baru yang dikarang; tidak ada buzzword, tanda pisah panjang, penekanan kapital, atau kutipan dekoratif.
PASS: label kontrol spesifik; penjelasan singkat memakai bahasa pengelola sehari-hari; kalimat tidak dipaksa menjadi tiga bagian atau slogan.
PASS: bentuk pasif seperti “dihitung” menjelaskan aturan sistem, tanpa menyembunyikan pelaku yang diperlukan pengguna.
Audit draf: kalimat penjelas yang terlalu padat dipisah menurut konteks ringkasan, aktivitas, dan grafik. Tidak ditemukan fakta tambahan di luar layanan yang sudah ada.
Pemeriksaan baca: setiap kalimat menjelaskan angka, batas, atau tindakan nyata; tidak ada penutup pemasaran.

## Revisi ringkasan sesuai review pengguna

Empat kalimat penjelas tentang tanggal kerja, shift malam, cakupan Hadir, dan peralihan Belum masuk ke Tidak hadir dihapus atas permintaan pengguna. Panel hanya menampilkan judul dan angka; susunan kosong di samping Hadir juga dihapus.
Delivery Gate di atas tetap PASS untuk lingkup revisi ini: warna, font, arah desain, perhitungan, dan kontrol tetap sama; perubahan hanya mengurangi teks dan merapikan susunannya.
R-03/R-32/R-35 PASS: dua tes UI terarah lulus, meliputi tiga ukuran desktop, kalender, keyboard, filter tanggal, serta tombol simulasi check-in dan akhir shift. Bukti: `evidence/dashboard-summary-trimmed.xml`.
R-02/R-16/R-31 PASS: tidak menambah teks baru; penghapusan memberi ruang untuk angka yang dibutuhkan pengelola.
Pratinjau dengan data sintetis diperiksa pada `evidence/dashboard-summary-trimmed.png`.

## Revisi kartu sesuai pilihan pengguna

Pengguna meminta enam hitungan kembali menjadi kartu terpisah seperti sebelum antislop. Urutan sekarang: Hadir, Terlambat, Belum masuk, Tidak hadir, Izin, Anggota aktif; susunan tiga kolom dan dua baris. Teks penjelas yang telah dihapus tidak dikembalikan.
R-14/R-31 PASS: ukuran dan tipografi kartu dibuat setara untuk membandingkan enam hitungan, sesuai pilihan pengguna. Pilihan ini menggantikan fokus angka Hadir yang lebih besar pada versi sebelumnya; identitas hijau dan tema tetap sama.
R-03/R-32/R-35 PASS: dua tes UI terarah lulus; ketiga ukuran desktop tidak menunjukkan kartu bertabrakan atau gulir horizontal pada Dashboard. Kalender, keyboard, filter tanggal, dan dua kontrol demo tetap berfungsi. Bukti: `evidence/dashboard-cards.xml`; pratinjau sintetis diperiksa pada `evidence/dashboard-cards.png`.
Delivery Gate sebelumnya tetap berlaku untuk item yang tidak berubah. Perubahan susunan dan hierarki mengikuti pilihan eksplisit pengguna di atas.

## Tombol Hari ini

Checkbox Ikuti hari ini diganti tombol Hari ini atas permintaan pengguna. Label menyebut tindakan langsung: kembali ke tanggal saat ini menurut zona aplikasi. Sesudah ditekan, tanggal mengikuti pergantian hari hingga pengguna memilih tanggal lain.
R-15/R-26/R-31 PASS: tombol menjalankan pengembalian tanggal, bukan toggle tersembunyi atau tombol tanpa tindakan; hasil pemuatan lama diabaikan saat tombol ditekan di tengah permintaan.
R-03/R-32/R-35 PASS: 13 tes Dashboard UI lulus, termasuk klik tombol saat sibuk, Space melalui keyboard, pergantian hari, kalender, tiga ukuran jendela, dan fokus yang tetap selama polling. Bukti: `evidence/dashboard-today-button.xml`; tangkapan layar sintetis diperiksa pada `evidence/dashboard-today-button.png`.
Delivery Gate lain tetap berlaku untuk susunan kartu, tema, warna, dan sumber data yang tidak diubah.

## Judul aktivitas dan penghapusan status pembaruan

Judul kini 20 aktivitas terbaru; kalimat batas 20 catatan dan status sukses berisi waktu pembaruan/zona dihapus sesuai permintaan pengguna. Pesan loading dan error tetap muncul ketika diperlukan, lalu disembunyikan setelah berhasil.
R-15/R-17/R-31 PASS: judul menyebut batas query sebenarnya tanpa kalimat pendamping berulang; penghapusan status sukses memberi ruang untuk aktivitas.
R-03/R-27/R-32/R-35 PASS: empat tes UI terarah lulus, meliputi error awal, error setelah data tersedia dan pemulihan, tiga ukuran desktop, filter/keyboard, dan kontrol demo. Bukti: `evidence/dashboard-activity-title.xml`; tangkapan layar sintetis diperiksa pada `evidence/dashboard-activity-title.png`.
Delivery Gate lainnya tetap berlaku untuk komponen dan perhitungan yang tidak diubah.

## Legenda pada setiap grafik

Kalimat tentang hijau dan jingga di bawah judul Pola kehadiran dihapus. Keempat kartu grafik kini memiliki legenda Hadir dan Terlambat sendiri sesuai permintaan pengguna.
R-04/R-23/R-25/R-31 PASS: kotak warna berfungsi sebagai penanda seri yang diminta pengguna, bukan dekorasi; label memakai teks gelap pada latar putih. Legenda dan grafik menggunakan konstanta warna yang sama agar maknanya selalu sesuai.
R-03/R-32/R-35 PASS: dua tes UI terarah lulus pada tiga ukuran desktop dan kontrol filter/demo tetap berfungsi. Tampilan lengkap empat legenda diperiksa pada `evidence/dashboard-chart-legends.png`; hasil uji pada `evidence/dashboard-chart-legends.xml`.
Delivery Gate lainnya tetap berlaku untuk sumber data, susunan kartu, dan kontrol yang tidak diubah.

## Perbaikan jarak vertikal pada kartu grafik

Kasus tiga shift bersebelahan dengan delapan grup mereproduksi jarak berlebihan pada header dan legenda. Sebelum perbaikan, regresi gagal karena tinggi judul 60 px untuk kebutuhan teks 20 px. Layout kini memakai jarak 8 px dan memberikan sisa tinggi hanya pada area grafik, sehingga header, deskripsi, dan legenda tetap rapat di atas.
R-03/R-31/R-35 PASS: tiga regresi Qt offscreen lulus pada lebar konten 740, 900, dan 1200 px, dengan jumlah baris grafik tidak seimbang. Tinggi judul/legenda dan sela antarbagian diperiksa secara langsung. Bukti: `evidence/dashboard-chart-spacing.xml`; kartu sintetis diperiksa pada `evidence/dashboard-chart-spacing.png`.
Delivery Gate lainnya tetap berlaku untuk warna, legenda, data dan kontrol yang tidak diubah.
