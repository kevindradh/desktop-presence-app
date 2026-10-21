<!-- Draf review, 21 Oktober 2026. Pembagian halaman merupakan panduan penataan; Markdown belum menetapkan ukuran kertas, font, atau jumlah halaman cetak. -->

<!-- HALAMAN 1 — COVER -->

[PERLU DILENGKAPI: logo resmi NALATICO]

# StarGate: Aplikasi Kehadiran dengan Pengenalan Wajah pada Komputer

**Nama anggota:** [PERLU DILENGKAPI: nama lengkap setiap anggota]

**Kategori peserta:** Pelajar

**Bidang lomba:** [PERLU DILENGKAPI: nama bidang sesuai pendaftaran]

**NALATICO 2026**  
**Nala Technology and Science Competition**

---

<!-- HALAMAN 2 — ABSTRAK -->

## ABSTRAK

*Pencatatan kehadiran perlu dilakukan dengan teliti agar nama dan waktu kedatangan tidak tertukar. StarGate dikembangkan untuk membantu pekerjaan tersebut melalui pengenalan wajah menggunakan kamera pada komputer. Tujuannya adalah membuat aplikasi yang menghubungkan data anggota, jadwal, pencatatan kehadiran, dan laporan. Pengembangan dilakukan bertahap, mulai dari merancang tampilan, menghubungkan kamera, memasang model pengenalan wajah yang sudah tersedia, hingga menguji penyimpanan dan pemulihan data. Model adalah program yang telah dilatih oleh pengembangnya untuk menjalankan tugas tertentu. Pengujian awal memakai kamera nyata dan data buatan khusus untuk menguji fungsi aplikasi. Pada pengujian akhir kamera di Windows, tujuh skenario lulus, termasuk penggunaan dua kamera bersamaan. Aplikasi terpasang juga berhasil membuat laporan dari 71 baris data buatan dalam bentuk Excel dan PDF. Uji pemulihan berhasil mempertahankan riwayat kehadiran dan menghapus data wajah sesuai aturan proyek. Namun, hasil ini belum menunjukkan tingkat ketepatan pengenalan wajah pada banyak orang. Jumlah peserta, ketepatan pengenalan, waktu pencatatan, dan kemampuan menolak foto atau video palsu masih perlu diukur. Dengan demikian, StarGate telah menjadi prototipe, yaitu versi awal aplikasi, yang dapat dipasang dan menjalankan fungsi dasar yang diuji. Pengujian langsung bersama pengguna masih diperlukan sebelum aplikasi digunakan lebih luas.*

**Kata kunci:** kehadiran, pengenalan wajah, kamera, aplikasi komputer, StarGate.

---

<!-- HALAMAN 3 — PENDAHULUAN -->

## 1. PENDAHULUAN

### 1.1 Latar Belakang

Dalam pencatatan kehadiran manual, pengelola perlu memeriksa nama dan mencatat waktu kedatangan. Data tersebut kemudian perlu dirangkum menjadi laporan. Jika dilakukan berulang, pekerjaan ini dapat menyita waktu dan membuka kemungkinan salah catat. Pada penelitian ini, kemungkinan tersebut menjadi alasan perancangan. Belum ada pengamatan di sekolah tertentu yang membuktikan seberapa sering kesalahan itu terjadi.

Salah satu cara yang dapat dicoba adalah memakai kamera untuk mengenali wajah anggota yang sudah terdaftar. Akan tetapi, mengenali wajah saja belum cukup. Aplikasi juga perlu memeriksa jadwal, menyimpan catatan, dan menyediakan laporan yang dapat dibaca pengelola.

StarGate dirancang untuk menghubungkan kebutuhan tersebut dalam satu aplikasi komputer. Aplikasi ini memakai model pengenalan wajah yang sudah tersedia. Fokus karya adalah menghubungkan bagian-bagian sistem dan menguji cara kerjanya, bukan membuat model kecerdasan buatan baru.

### 1.2 Rumusan Masalah

1. Bagaimana membuat aplikasi kehadiran yang menghubungkan kamera, data anggota, dan jadwal?
2. Apakah fungsi kamera, pencatatan, laporan, serta pencadangan dan pemulihan data dapat berjalan pada prototipe?
3. Bagian apa yang masih perlu diuji sebelum StarGate dipakai dalam kegiatan nyata?

### 1.3 Tujuan Penelitian

Penelitian ini bertujuan membangun versi awal atau prototipe aplikasi kehadiran berbasis pengenalan wajah, menguji fungsi dasarnya, dan mencatat keterbatasan yang masih ditemukan.

### 1.4 Manfaat Penelitian

**a. Manfaat akademis**

Karya ini menjadi sarana belajar tentang pemrograman, pengolahan gambar, penyimpanan data, dan pengujian aplikasi. Pengembangan juga mengajarkan bahwa hasil uji perlu dicatat dengan jujur.

**b. Manfaat praktis**

StarGate diharapkan membantu pengelola menghubungkan data anggota, jadwal, dan laporan kehadiran. Manfaat berupa penghematan waktu belum diukur sehingga belum dapat dinyatakan sebagai hasil penelitian.

### 1.5 Batasan Masalah

Pengembangan dilakukan pada macOS dan pemasangan aplikasi diuji pada Windows melalui Parallels, yaitu perangkat lunak untuk menjalankan Windows di komputer Mac. Pengujian kamera memakai kamera laptop dan webcam USB. Kamera jaringan nyata belum tersedia. Data buatan dipakai untuk menguji beberapa fungsi penyimpanan dan laporan. Pengujian ketepatan wajah pada banyak peserta belum selesai. Model wajah digunakan dalam lingkup penelitian nonkomersial sesuai ketentuan pengembangnya [3].

---

<!-- HALAMAN 4 — METODE -->

## 2. METODE

### 2.1 Perancangan dan Desain

Karya dibuat dengan cara merancang, membangun, menguji, lalu memperbaiki aplikasi secara bertahap. Setiap bagian diperiksa sebelum pekerjaan dilanjutkan. Alat utama yang digunakan ditunjukkan pada Tabel 1.

**Tabel 1. Bagian utama StarGate dan kegunaannya.**

| Bagian | Kegunaan dalam proyek |
|---|---|
| Python dan PyQt6 | Menulis program serta membuat jendela, tombol, dan formulir aplikasi. PyQt menghubungkan Python dengan alat pembuat tampilan Qt [1]. |
| OpenCV dan RetinaFace | Membaca gambar kamera dan mencari letak wajah pada gambar. OpenCV menyediakan alat pengolahan gambar dan video [2]. |
| ArcFace melalui InsightFace | Mengubah ciri wajah menjadi kumpulan angka untuk dibandingkan dengan data terdaftar [3]. |
| MiniFASNetV2 | Membantu memeriksa tanda wajah asli atau tampilan tiruan, seperti foto. Model berasal dari proyek Silent-Face-Anti-Spoofing [4]. |
| PostgreSQL dan pgvector | Menyimpan data anggota, jadwal, catatan kehadiran, serta angka ciri wajah untuk pencocokan. |

Angka ciri wajah tetap diperlakukan sebagai data pribadi. Pengguna perlu memberi izin sebelum wajahnya didaftarkan. Adanya pemeriksaan wajah tiruan juga tidak berarti semua bentuk kecurangan pasti dapat dicegah.

### 2.2 Diagram Blok Sistem

```text
Pendaftaran anggota dan wajah
              |
              v
      Data anggota tersimpan
              |
              v
Kamera --> Pemeriksaan gambar dan wajah
                         |
                         v
              Pencocokan data anggota
                         |
                         v
              Pemeriksaan aturan jadwal
                         |
                         v
              Penyimpanan kehadiran
                         |
                         v
                Ringkasan dan laporan
```

**Gambar 1. Alur utama StarGate.** Setiap pemeriksaan harus memenuhi syarat sebelum catatan disimpan. Jika wajah tidak dikenali atau syarat lain tidak terpenuhi, aplikasi tidak boleh menampilkan pencatatan berhasil.

### 2.3 Proses Pembuatan

Pembuatan dimulai dengan menelaah kebutuhan proyek dan menyusun rencana. Setelah itu, dibuat tampilan aplikasi serta penyimpanan data. Pengelolaan akun, anggota, kelompok, jadwal, dan perangkat kamera ditambahkan secara bertahap.

Berikutnya, kamera dihubungkan dengan pemeriksaan dan pencocokan wajah. Pendaftaran disiapkan untuk mengambil wajah dari lima sudut. Setelah bagian tersebut tersedia, ditambahkan pencatatan masuk dan keluar, ringkasan kehadiran, laporan, serta pencadangan data. Aplikasi kemudian dikemas menjadi pemasang Windows dan diuji pada akun Windows biasa.

### 2.4 Pengujian

Pengujian fungsi dilakukan dengan membandingkan hasil yang diharapkan dan hasil yang muncul. Kamera dinilai berhasil jika dapat mengirim gambar, dibuka kembali, dan dihentikan dengan baik. Laporan dinilai berhasil jika memuat seluruh data uji. Pemulihan diperiksa dengan membandingkan data sebelum dan sesudah proses tersebut.

Data buatan digunakan untuk memeriksa alur penyimpanan tanpa menganggapnya sebagai data peserta nyata. Pengujian wajah langsung yang masih perlu dilengkapi mencakup wajah terdaftar, orang lain, foto cetak, foto pada layar, dan pemutaran video. Percobaan perlu dicatat satu per satu. Percobaan ulang wajah terdaftar dilakukan pada kesempatan berbeda dari pendaftarannya.

---

<!-- HALAMAN 5 — HASIL DAN PEMBAHASAN -->

## 3. HASIL DAN PEMBAHASAN

### 3.1 Realisasi Prototipe

StarGate sudah berbentuk aplikasi dengan halaman masuk, pengelolaan anggota dan jadwal, perangkat kamera, pencatatan kehadiran, ringkasan, dan laporan. Aplikasi juga memiliki pembatasan akses berdasarkan tugas pengguna serta fasilitas cadangan dan pemulihan data. Pemasang Windows sudah dibuat dan berhasil dijalankan pada Windows 11 melalui Parallels.

### 3.2 Hasil Pengujian dan Analisis

Tabel 2 memuat hasil yang tersedia dalam catatan proyek sampai 21 Oktober 2026.

**Tabel 2. Hasil pengujian fungsi prototipe.**

| Pengujian | Hasil yang tercatat |
|---|---|
| Kamera pada paket Windows | Tujuh skenario akhir lulus. Kamera laptop dan USB dapat mengirim gambar berukuran 1280 × 720, termasuk saat digunakan bersamaan. |
| Laporan dari data buatan | Seluruh 71 baris masuk ke berkas Excel dan PDF. PDF berisi 18 halaman. Angka ini bukan jumlah peserta penelitian. |
| Cadangan dan pemulihan | Pada data uji, 71 anggota dan satu riwayat kehadiran tetap ada setelah pemulihan. Foto uji dan lima kumpulan angka ciri wajah dihapus sesuai aturan pemulihan proyek. |
| Hapus dan pasang ulang aplikasi | Pengaturan, cadangan, dan data uji tetap tersedia. |
| Pemeriksaan tanpa jaringan internet | Komponen model dan koneksi penyimpanan lokal lulus saat jaringan Windows diputus. Seluruh alur penggunaan tanpa internet belum diuji langsung. |

Pada percobaan kamera sebelumnya, beberapa pemeriksaan gagal. Pemeriksaan perangkat menunjukkan webcam USB sempat tidak terhubung ke Windows. Setelah dihubungkan kembali, tujuh skenario akhir lulus. Kegagalan awal pembukaan kamera laptop belum sepenuhnya diketahui penyebabnya sehingga perlu dipantau kembali.

**Data yang masih perlu dilengkapi:** jumlah peserta dan percobaan wajah, jumlah pengenalan yang benar dan salah, waktu pencatatan, hasil percobaan foto atau video palsu, serta tanggapan pengguna. Data tersebut belum diberi angka karena belum tersedia dalam catatan pengujian.

### 3.3 Pembahasan

Hasil awal menunjukkan bahwa bagian-bagian utama prototipe sudah dapat dihubungkan dan beberapa fungsi penting berjalan sesuai pengujian. Laporan dapat dibuat dari data uji, sedangkan pemulihan tidak hanya mengembalikan catatan, tetapi juga menjalankan aturan penghapusan data wajah. Setelah pemulihan, anggota perlu mendaftarkan wajah kembali.

Namun, keberhasilan penyimpanan dan kamera tidak sama dengan ketepatan mengenali orang. Data buatan tidak dapat menggantikan percobaan wajah nyata. Karena itu, hasil saat ini belum membuktikan bahwa StarGate lebih cepat daripada pencatatan manual atau mampu mencegah semua penggunaan foto dan video palsu. Pengukuran bersama peserta masih diperlukan untuk menilai hal tersebut.

---

<!-- HALAMAN 6 — PENUTUP -->

## 4. PENUTUP

### 4.1 Kesimpulan

StarGate telah dikembangkan menjadi prototipe aplikasi kehadiran yang menghubungkan data anggota, jadwal, kamera, dan laporan. Aplikasi berhasil dipasang pada Windows melalui Parallels. Pengujian akhir kamera serta pengujian laporan, cadangan, dan pemulihan dengan data buatan menunjukkan hasil sesuai skenario yang diperiksa.

Tujuan membangun prototipe dan memeriksa fungsi dasarnya telah tercapai pada bagian yang diuji. Namun, ketepatan pengenalan wajah, waktu pencatatan, dan kemampuan menolak wajah tiruan belum dapat disimpulkan. StarGate masih memerlukan pengujian langsung bersama pengguna sebelum digunakan lebih luas.

### 4.2 Saran

Pengujian berikutnya sebaiknya melibatkan peserta yang memberi izin, dengan variasi cahaya dan posisi wajah. Hasil wajah terdaftar, orang lain, foto, dan video perlu dicatat terpisah. Waktu pencatatan juga perlu diukur dan dibandingkan dengan cara manual pada kegiatan yang sama.

Aplikasi selanjutnya perlu diuji pada komputer Windows lain, penggunaan kamera dalam waktu lebih lama, dan kamera jaringan jika tersedia. Pengelolaan izin, penyimpanan, dan penghapusan data wajah harus tetap diperhatikan.

---

<!-- LAMPIRAN — DI LUAR ENAM HALAMAN UTAMA -->

## LAMPIRAN

### A. Daftar Pustaka

[1] Riverbank Computing. (Tanpa tahun). *What is PyQt?* [Situs resmi PyQt](https://www.riverbankcomputing.com/software/pyqt/intro). Diakses 21 Oktober 2026.

[2] OpenCV. (Tanpa tahun). *Introduction*. [Dokumentasi resmi OpenCV](https://docs.opencv.org/4.x/d1/dfb/intro.html). Diakses 21 Oktober 2026.

[3] InsightFace. (Tanpa tahun). *InsightFace: 2D and 3D Face Analysis Project*. [Repositori resmi InsightFace](https://github.com/deepinsight/insightface). Diakses 21 Oktober 2026.

[4] MiniVision. (Tanpa tahun). *Silent-Face-Anti-Spoofing*. [Repositori resmi MiniVision](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing). Diakses 21 Oktober 2026.

### B. Biodata Peserta

[PERLU DILENGKAPI: salin tabel berikut untuk setiap anggota.]

| Identitas | Isian |
|---|---|
| Nama lengkap | [PERLU DILENGKAPI] |
| NISN | [PERLU DILENGKAPI] |
| Jenis kelamin | [PERLU DILENGKAPI] |
| Tempat dan tanggal lahir | [PERLU DILENGKAPI] |
| Alamat | [PERLU DILENGKAPI] |
| Nomor telepon | [PERLU DILENGKAPI] |
| Alamat email | [PERLU DILENGKAPI] |
| Riwayat kompetisi | [PERLU DILENGKAPI sesuai pengalaman sebenarnya] |

### C. Logbook Kegiatan

Ringkasan berikut bersumber dari tanggal pada dokumen proyek. Catatan ini perlu dicocokkan dengan kegiatan dan peran peserta yang sebenarnya sebelum menjadi logbook lomba.

| No. | Tanggal | Kegiatan/Tugas | Foto/Dokumen | Catatan/Hasil/Kendala & Solusi |
|---|---|---|---|---|
| 1 | 18 Oktober 2026 | Persiapan perangkat lunak dan kamera | Catatan pengujian Tahap 1 | Persiapan dan uji kamera dicatat. [PERLU DILENGKAPI: peran peserta dan dokumentasi kegiatan.] |
| 2 | 19 Oktober 2026 | Pengembangan pemeriksaan dan pencocokan wajah | Catatan pengujian Tahap 7 | Komponen model diuji; hasil uji fungsi belum menjadi ukuran ketepatan pada banyak peserta. |
| 3 | 20 Oktober 2026 | Pengembangan laporan, cadangan, dan pemulihan | Catatan Tahap 12–13 | Ekspor serta pemulihan diperiksa dengan data uji. |
| 4 | 21 Oktober 2026 | Pengujian aplikasi terpasang di Windows | Catatan Tahap 14 | Kamera USB sempat tidak terdeteksi. Setelah dihubungkan kembali, tujuh skenario kamera akhir lulus. |

### D. Data Pendukung

Bukti pengujian dalam proyek:

1. [Ringkasan Tahap 14](../testing/evidence/stage-14-summary.json).
2. [Data tujuh skenario kamera Windows akhir](../testing/evidence/stage-14-windows-cameras-frozen-reconnected.json).
3. [Hasil uji fungsi pada aplikasi terpasang](../testing/evidence/stage-14-clean-frozen-uat.log).
4. [Pemeriksaan data setelah pemasangan ulang](../testing/evidence/stage-14-clean-preserved-data.log).
5. [Contoh laporan Excel, seluruhnya data buatan](../testing/evidence/stage-14-windows-export.xlsx) dan [PDF](../testing/evidence/stage-14-windows-export.pdf).

Catatan tambahan: uji otomatis Windows terakhir mencatat 455 pemeriksaan lulus, dua melewati batas waktu, dan satu dilewati karena akun Windows biasa tidak memiliki izin membuat tautan berkas tertentu. Dua kasus yang melewati batas waktu lulus saat diulang terpisah; pemeriksaan yang dilewati juga lulus secara terpisah dengan akun sistem yang memiliki izin. Hasil ini tidak ditulis sebagai satu pengujian penuh yang langsung lulus seluruhnya dan bukan persentase ketepatan pengenalan wajah.

[PERLU DILENGKAPI: tabel percobaan wajah nyata, persetujuan peserta, pengukuran waktu, dan dokumentasi tampilan aplikasi yang boleh dilampirkan. Jangan memasukkan kata sandi atau data wajah mentah ke lampiran terbuka.]

### E. Surat-menyurat

[PERLU DILENGKAPI: surat atau dokumen administratif yang benar-benar tersedia dan diminta panitia. Jika tidak ada, tuliskan “Tidak ada” setelah dikonfirmasi.]
