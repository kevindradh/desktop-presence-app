# Form Perangkat dua kolom

Permintaan pengguna: samakan keringkasan halaman Perangkat dengan Anggota, Grup, dan Shift. Hapus pengantar penambahan kamera, catatan nomor webcam/kerahasiaan RTSP, serta petunjuk maksimum stream dan pemilihan Cmd/Ctrl. Pembatasan stream dan perlindungan sumber RTSP tetap dijalankan layanan.

Arah mengikuti ruang kerja hijau StarGate dan font sistem, ENERGY 1 / RHYTHM 2 / MOTION 1. Dua kolom mengurangi jumlah baris dengan pasangan Nama perangkat/Jenis, Resolusi/FPS, Nomor kamera lokal/Sumber RTSP, lalu Lokasi/Tampilkan sumber. Jarak 20 px horizontal dan 12 px vertikal mengikuti form Anggota. Label terhubung ke input melalui buddy Qt; Tab mengikuti urutan visual dan melewati field yang nonaktif.

Tombol menjadi Tambah, Simpan, Hapus, Refresh, Tes koneksi, Pratinjau, dan Hentikan. Tampilkan sumber tetap tersedia dengan label pendek; sumber tersimpan tetap tidak diisikan kembali. Placeholder penggantian RTSP dan pesan galat tetap ada karena membantu tindakan yang diperlukan.

## Verifikasi dan Delivery Gate

- PASS, Hard Gate: tujuh tes UI/database terpisah lulus untuk tambah/edit/hapus/batal, masking dan pembersihan sumber RTSP, perubahan jenis, dua preview sintetis, tes koneksi, putus kamera dan mulai ulang manual, serta pelepasan kamera saat navigasi/logout/password/tutup/timeout. Form dijalankan dengan Qt offscreen pada 720×600, 900×720 dan 1180×820; pasangan field sejajar, tidak bertumpuk dan berada dalam batas form. Tab awal dan keadaan RTSP diperiksa. Gambar form serta halaman dengan preview ditinjau; warna/kontras/fokus tetap memakai tema yang sama. Tidak ada aset atau klaim baru.
- PASS, Purpose-Gate: alasan pasangan, jarak dan label dicatat di atas. Tidak menambah ikon, badge, gradasi atau animasi. Dua baris tombol mempertahankan pemisahan pengelolaan data dan penggunaan kamera.
- PASS, Liveliness: dial tetap mengikuti halaman lain; tabel menjadi area utama, diikuti form dan tindakan, dengan aksen hijau StarGate serta ruang antarbagian yang sama.
- PASS, Craftsmanship: kontrol memakai callback dan layanan lama; teks yang dihapus tidak menghilangkan validasi maupun perlindungan kredensial. Preview kamera pada ukuran pendek tetap dapat dilihat melalui gulir halaman.
- PASS, Copywriting: label singkat menyebut tindakan secara langsung sesuai istilah pengguna, tanpa klaim atau jargon baru.

Bukti: `evidence/devices-layout.xml` (7 lulus), `evidence/devices-layout-form.png`, dan `evidence/devices-layout/`. Gambar memakai data/frame sintetis, tanpa wajah atau kredensial nyata. Tidak melakukan uji kamera fisik/RTSP nyata untuk revisi tampilan ini.
