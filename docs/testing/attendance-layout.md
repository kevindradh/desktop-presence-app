# Halaman Kehadiran

Permintaan pengguna: kamera besar seperti dialog registrasi, dropdown perangkat/lokasi di atas, tindakan mulai di kanan, serta daftar hasil yang langsung bertambah. Hilangkan pengantar, checkbox persetujuan berulang, rincian similarity/anti-spoof, dan uraian AUTO. Muat ulang dipertahankan sementara sampai review berikutnya.

Arah mengikuti halaman Anggota/Grup/Shift: warna hijau StarGate dan font sistem, ENERGY 1 / RHYTHM 2 / MOTION 1. Kontrol ringkas di atas memberi ruang utama pada preview. Kamera minimum 480×360 tanpa batas tinggi 300 px sebelumnya; ruang sisa diberikan pada kamera. Bingkai kosong memakai warna yang sama dengan dialog registrasi. Riwayat tetap di bawah dengan tinggi 180–220 px dan gulir tabel sendiri. Pada jendela pendek, halaman tetap bisa digulir.

Dropdown memuat nama perangkat dan lokasi, dengan pilihan Semua kamera bila tersedia beberapa perangkat. Pilihan tunggal membuka satu stream; Semua kamera membuka daftar perangkat yang tersedia melalui validasi batas stream lama. Preview beberapa kamera disusun vertikal agar masing-masing tetap lebar. Nama panjang tidak memaksa lebar halaman. Perangkat/mode terkunci selama proses. Kamera tetap hanya dimulai setelah pengguna menekan Mulai, dan tetap berhenti saat meninggalkan halaman/logout/timeout/tutup.

Penghapusan checkbox mengikuti persetujuan awal yang dinyatakan pengguna. Ini tidak mematikan pemeriksaan keaslian, ambang pengenalan, atau aturan absensi. Nilai konfigurasi tetap digunakan layanan, hanya rincian teknisnya yang dihapus dari layar. Hasil scan, penolakan, dan galat perangkat/model tetap ditampilkan. Riwayat dimuat otomatis setelah transaksi sukses; Muat ulang tidak diperlukan untuk melihat hasil scan baru.

## Bukti pengujian

- `evidence/attendance-layout.xml`: 22 tes UI/demo lulus. Mencakup scan masuk/keluar, satu event pada dua kamera, suara setelah commit, spoof tidak tersimpan, perubahan pengaturan, penghentian/logout/timeout/tutup, serta Muat ulang tanpa berkedip dan permintaan reload digabung.
- `evidence/attendance-layout-sizes.xml`: pemeriksaan lanjutan lulus pada 1000×740, 1180×820 dan 1440×900. Preview minimum terpenuhi, kontrol di dalam halaman, tidak ada gulir horizontal halaman, pilihan kamera dipertahankan, dan bingkai kosong kembali setelah Hentikan. Tab serta fungsi mode memakai kontrol Qt yang sama.
- `evidence/attendance-layout/stage-10-attendance-synthetic.png`: hasil render ditinjau. Warna di kamera adalah frame sintetis, bukan wajah nyata. Gambar diambil sebelum label mode dipendekkan dari Otomatis (masuk / keluar) menjadi Otomatis.

## Delivery Gate

- PASS, Hard Gate: aplikasi dijalankan; kontrol dropdown/Mulai/Hentikan/Muat ulang dan siklus hidup diuji melalui alur database terpisah. Pemeriksaan ukuran dan gambar membuktikan batas kamera/kontrol; tabel lebar memakai gulir internal. Tema/kontras dan fokus Qt mengikuti komponen yang sama. Status kosong, proses, hasil dan galat dipertahankan. Tidak ada aset atau klaim baru.
- PASS, Purpose-Gate: susunan, ukuran, warna bingkai dan alasan mempertahankan Muat ulang dijelaskan di atas. Tidak menambah ikon, badge, efek atau animasi.
- PASS, Liveliness: dial eksplisit; kamera menjadi fokus, kontrol atas dan riwayat bawah membentuk urutan kerja. Aksen hijau dan bingkai mengikuti identitas StarGate.
- PASS, Craftsmanship: tombol tetap terhubung ke layanan berizin; tes memastikan penyimpanan mendahului suara/riwayat dan dua kamera tidak menggandakan event. Kamera dimulai secara eksplisit dan dihentikan sesuai siklus sesi. Perubahan ukuran berlaku untuk aplikasi desktop.
- PASS, Copywriting: label langsung menyebut tindakan/perangkat/lokasi; tanpa klaim, jargon baru, atau penjelasan AUTO berulang. Teks teknis hanya dihapus dari presentasi, aturan pemrosesan tetap digunakan.

Pengujian memakai kamera/wajah sintetis; belum merupakan uji webcam atau akurasi wajah nyata untuk layout baru ini.
