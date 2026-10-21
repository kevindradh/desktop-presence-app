# Aplikasi demo Tahap 10

Demo menyiapkan akun yang langsung masuk, satu peserta sintetis dengan lima embedding, shift 08:00–17:00 WIB dengan toleransi 10 menit, dan dua kamera sintetis. Tidak perlu membuat akun, mendaftarkan wajah, atau menunggu jam shift nyata. Aplikasi dan PostgreSQL test tetap diperlukan; model AI dan webcam fisik tidak diperlukan untuk demo ini.

## Menjalankan

Dari folder proyek:

```bash
.venv/bin/python scripts/local_postgres.py start
.venv/bin/python scripts/demo_attendance.py
```

Konfigurasi database test mengikuti instalasi proyek yang sudah ada. Jika belum siap, demo menampilkan pesan gagal; tidak beralih ke database development.

## Cara tercepat

1. Pada tab **Uji otomatis**, klik **Jalankan semua (9 skenario)**.
2. Tunggu status tiap skenario menjadi **LULUS**, **GAGAL**, atau **ERROR**. Antarmuka tetap dapat digunakan. LULUS muncul setelah kondisi yang diharapkan diperiksa terhadap hasil transaksi database, bukan label tetap.
3. Pilih baris untuk melihat event/waktu/status yang tersimpan. **GAGAL** berarti hasil berbeda dari harapan; **ERROR** berarti uji tidak selesai dan bukan lulus.
4. Klik **Simpan hasil JSON** dan pilih lokasi. Berkas memuat status semua skenario; yang belum dijalankan tetap **BELUM DIUJI**. Hasilnya dapat dikirim kembali untuk review.
5. Untuk mengulang, klik Jalankan semua atau pilih satu baris lalu **Jalankan yang dipilih**. Setiap pengulangan menggunakan data baru.

Sembilan skenario: alur IN → BREAK_OUT → BREAK_IN → OUT serta wajah terus terlihat; cooldown lintas kamera; sebelum/tepat awal shift; tepat toleransi Present; setelah toleransi Late; wajah tidak dikenal; penolakan probe spoof; konfigurasi berubah saat scan; checkout otomatis tanpa OUT ganda. Semua memakai layanan absensi dan PostgreSQL/pgvector asli dengan input sintetis dan waktu absensi terkontrol.

## Mencoba halaman Kehadiran

Tab **Coba halaman Kehadiran** memuat halaman aplikasi yang sama dengan data yang sudah siap. Jam absensi dimulai pukul 08:00 WIB pada tanggal saat demo dibuka dan hanya maju melalui tombol simulasi. Jam komputer dan jam sesi login tidak diubah. Jam pada header aplikasi tetap jam nyata; rujuk label **WIB** di kontrol demo untuk waktu absensi.

1. Pilih **Kamera sintetis 1**, mode **Otomatis**, centang persetujuan, lalu **Mulai absensi**. Hasil IN ditampilkan setelah commit.
2. Pilihan **Peserta terdaftar** mensimulasikan satu identitas yang tersedia. Pratinjau berupa bidang warna hijau, bukan video webcam. **Wajah tidak dikenal** dan **Spoof sintetis** dapat dicoba melalui pilihan di atas halaman.
3. Untuk scan berikutnya, pilih **Tidak ada wajah**, tunggu lebih dari satu detik agar penahan identitas dilepas. Klik **+61 detik simulasi**, lalu pilih peserta lagi. Dalam AUTO, hasil berikutnya adalah OUT. Jika muncul pesan proses masih berjalan, ulangi klik setelah proses selesai.
4. Untuk mencoba istirahat, setelah IN hentikan kamera lalu ubah mode ke Mulai istirahat; majukan waktu 61 detik dan mulai lagi. Ulangi untuk Selesai istirahat dan Keluar. Penggantian mode tetap mengikuti kontrol aplikasi asli.
5. Amati tombol **Muat ulang** selama scan; tidak boleh berkedip mengikuti transaksi setiap frame.
6. Untuk checkout otomatis pada sesi yang masih IN: hentikan kamera, buka Pengaturan, aktifkan checkout otomatis dan simpan. Kembali ke Kehadiran, klik **Ke akhir shift (17:00)**, tunggu proses, lalu **Muat ulang**. Event OUT bertanda Otomatis tampil pada akhir shift. Timer berkala pada demo dihentikan; tombol perubahan waktu memicu pemeriksaan otomatis secara eksplisit agar tidak perlu menunggu waktu nyata.
7. Setelah OUT, tutup demo dan buka kembali untuk memperoleh sesi interaktif baru. Skenario otomatis dapat diulang tanpa menutup aplikasi.

Kedua tab menggunakan schema berbeda: menjalankan skenario otomatis tidak mereset/menambah event pada tab interaktif. Di demo ini akun masuk otomatis; jika keluar akun atau perlu mengulang pengaturan awal, tutup dan buka demo kembali. Password sementara dibuat acak dan tidak ditampilkan.

## Data dan batas hasil

- Seluruh data disimpan pada schema sementara milik demo di **stargate_test**, bukan data operasional. Schema otomatis dibersihkan saat demo ditutup normal. Penutupan paksa/crash dapat menyisakan schema sementara; demo tidak menghapus schema yang tidak dimilikinya.
- Kamera selalu sumber sintetis; tidak membuka laptop/USB/RTSP. Tidak ada wajah/foto/embedding orang nyata yang dibaca atau disalin. Embedding sintetis dipisahkan memakai versi khusus demo.
- Ekspor hasil berisi nama skenario dan riwayat sintetis, tanpa token sesi, password atau vektor.
- Simulasi spoof menguji penolakan hasil liveness/aturan penyimpanan, bukan kemampuan model membedakan foto/video nyata. Simulasi kamera tidak membuktikan USB/RTSP atau pengenalan wajah nyata lulus.
- Demo membantu uji aturan dan interaksi dengan cepat. Uji kamera, speaker, wajah terdaftar/unknown, foto cetak dan replay nyata tetap mengikuti [panduan Tahap 10](stage-10.md). Review tahap belum dinyatakan disetujui.

## Verifikasi demo

11 tes integrasi demo PASS: sembilan skenario melalui layanan asli, penolakan target database development, dan antarmuka demo/ekspor/IN–OUT/penutupan worker. Uji antarmuka native macOS juga menjalankan semua sembilan skenario serta memastikan tab interaktif tidak berubah karena uji otomatis.

Bukti: [tes demo](evidence/stage-10-demo-tests.xml), [tes native](evidence/stage-10-demo-native.xml), [tampilan skenario](evidence/stage-10-demo-scenarios.png), [tampilan interaktif](evidence/stage-10-demo-interactive.png). Ini verifikasi tambahan; coverage dan jumlah suite penuh Tahap 10 sebelumnya tidak dihitung ulang. Tahap 11 belum dimulai.
