# Revisi dialog registrasi wajah

Revisi mengikuti permintaan pengguna: fokus pada kamera, panduan sudut aktif, dan tindakan singkat. Arah mengikuti StarGate, ENERGY 1 / RHYTHM 2 / MOTION 1.

- Checkbox persetujuan tidak dibuat pada dialog registrasi/tes wajah. Alat Uji AI Tahap 7 tetap meminta checkbox seperti sebelumnya.
- Judul isi dan paragraf panjang tentang lima sudut disembunyikan; identitas anggota dan panduan sudut aktif tetap ada.
- Preview tidak lagi dibatasi maksimum 400 px. Ukuran minimum frame 640×360, ukuran awal dialog 1120×820 dan minimum 900×720.
- Latar frame memakai hijau gelap StarGate agar area kosong dan tepi gambar mudah dikenali, tanpa teks pengganti saat berhenti.
- Sesuai klarifikasi pengguna, preview mengikuti gerakan seperti cermin: tangan kanan tampil di sisi kanan layar. Hanya pixmap tampilan yang dibalik horizontal; frame inferensi dan foto dalam hasil capture tetap memakai orientasi sumber. Panduan hidung ke kiri/kanan gambar diselaraskan dengan preview ini. Foto selesai capture juga ditampilkan dengan orientasi preview yang sama.
- Label tindakan: Mulai, Hentikan & hapus, Capture, Batal, Simpan. Dua tombol bawah sama lebar, Batal di kiri dan Simpan di kanan; Simpan memakai warna utama tema.
- Log rutin model/kualitas/similarity dan ringkasan konfigurasi disembunyikan. Pesan kegagalan penting tetap ditampilkan; hasil tes wajah tetap menyebut cocok atau tidak cocok tanpa skor teknis.
- Hentikan & hapus mengosongkan frame dan membuang packet, foto serta referensi sementara. Hasil kamera/inferensi yang datang setelah penghentian tidak menghidupkan ulang hasil capture. Sesudah lima sampel lengkap, tindakan ini tetap dapat digunakan sebelum Simpan, lalu Mulai mengulang dari sudut pertama.
- Aturan lima sudut, kualitas/keaslian, ambang registrasi 0,85, penyimpanan atomik, penggantian set lama, dan retensi tidak diubah.

## Verifikasi dan Delivery Gate

Delapan uji dialog dengan database terisolasi dan kamera/wajah sintetis lulus: registrasi/registrasi ulang tanpa penyimpanan parsial, penghentian sesudah capture lengkap dan pengulangan, batal, logout, ganti password, tutup, timeout, serta tes wajah setelah restart. Beberapa kondisi merupakan parameter pada satu skenario tes.
Tiga uji tambahan lulus: preview mengikuti gerakan, frame inferensi/foto tidak berubah, panduan kiri/kanan sesuai, dan frame kosong setelah Stop, serta dua regresi Alat Uji AI yang tetap membutuhkan checkbox.
Ukuran dialog 900×720 dan 1120×820 diperiksa; frame, Batal, dan Simpan berada dalam batas dialog. Tombol bawah sama lebar. Gambar hasil sintetis ditinjau pada `evidence/enrollment-dialog-compact.png`.
Hasil pengujian: `evidence/enrollment-dialog-ui.xml` (8 lulus) dan `evidence/enrollment-preview.xml` (3 lulus). Pengujian offscreen ini tidak menyatakan bahwa perangkat kamera fisik telah diuji ulang.

| Gate | Hasil dan bukti |
|---|---|
| Hard Gate | PASS: label nyata, tanpa klaim akurasi atau angka hasil rekaan; perubahan mendapat arahan eksplisit pengguna; frame dan tombol diuji pada dua ukuran; Stop/Batal/Save menjalankan tindakan nyata; tidak ada checkbox tersembunyi yang otomatis dicentang. |
| Purpose-Gate | PASS: frame diperbesar untuk menangkap pose, warna gelap membatasi area video, tombol Simpan memakai warna tema untuk tindakan penyimpanan; tidak menambah gambar, ikon, efek atau animasi. |
| Liveliness | PASS: dial dan arah di atas dinyatakan; kamera menjadi fokus, panduan singkat serta dua tindakan bawah menjadi struktur yang sesuai registrasi. |
| Craftsmanship | PASS: 11 pengujian lulus; pratinjau diperiksa; tidak mengubah cara AI memutuskan kelayakan sampel atau cara menyimpan data. |

Panduan mandiri diperbarui pada `stage-08.md` dan `stage-09.md` untuk label/keterangan yang kini tampil.

## Panel langkah di dalam frame kamera

Sesuai permintaan pengguna, langkah dan panduan sudut kini berupa panel di bagian atas preview kamera. Teks 18 px, tebal, di atas latar hijau pucat dengan teks hijau gelap agar terbaca di atas video. Margin 16 px menjaga panel di dalam frame dan posisi/tingginya dihitung ulang saat kamera berubah ukuran atau panduan berganti.
Panel tidak mengambil klik atau membalik teks saat pixmap kamera dibalik. Saat Hentikan & hapus dipilih, panel ikut disembunyikan sehingga frame benar-benar kosong; Mulai menampilkannya kembali.
PASS: delapan tes alur dialog dan satu tes preview/layout lulus. Batas panel diperiksa pada ukuran dialog 900×720 dan 1120×820. Bukti: `evidence/enrollment-guide-ui.xml`, `evidence/enrollment-guide-layout.xml`, dan pratinjau sintetis `evidence/enrollment-guide-step1.png` yang telah diperiksa.
Delivery Gate tetap mengikuti arah dan kontrol di atas; panel mempunyai tujuan menunjukkan langkah aktif, tidak menambah angka rekaan atau animasi, dan tidak mengubah hasil inferensi/penyimpanan.

## Auto capture registrasi

Mulai mengaktifkan pengambilan otomatis untuk registrasi lima sudut. Tombol Capture tetap dapat digunakan secara manual; Tes wajah tetap membutuhkan Periksa wajah ini. Tidak ada penyimpanan otomatis: pengguna meninjau hasil dan memilih Simpan setelah set lengkap.
Kebijakan awal auto capture mensyaratkan waktu stabil minimal 0,6 detik dan minimal tiga pemeriksaan valid, pada frame kamera berbeda, dengan jeda pemeriksaan tidak melebihi dua detik. Posisi/ukuran wajah, yaw/pitch/roll, dan identitas harus konsisten sepanjang interval. Ini batas penerimaan yang ditetapkan dalam kode, bukan hasil penelitian akurasi atau janji durasi pengambilan.
Setiap pemeriksaan melewati validasi draft yang sama: satu wajah, kualitas layak, liveness kelas asli dengan skor minimal 0,85, sudut yang sedang diminta, dan identitas sesuai referensi. Ketidaksesuaian menghapus penghitung stabilitas. Setiap sampel berhasil juga mengulang penghitung untuk sudut berikutnya.
Stabilitas diperiksa di worker inferensi; UI tidak menyalin keputusan validasi kualitas. Referensi sementara untuk stabilitas dihapus saat reset, capture berhasil, atau worker berhenti. Frame yang sama tidak dihitung berulang oleh auto capture.
PASS: 23 tes inti/preview/inferensi dan sembilan tes dialog dengan data sintetis lulus. Regresi mencakup lima pose otomatis tanpa klik Capture, tanpa data DB sebelum Simpan, input tidak layak, pose salah, gerakan/identitas berubah, jeda panjang, interval terlalu singkat, frame berulang, fallback manual, penghapusan dan mulai ulang, serta pembatalan sesi.
Hasil: `evidence/auto-capture-core.xml` dan `evidence/auto-capture-ui.xml`. Delivery Gate fungsi/kejujuran tetap PASS: auto capture mempunyai tindakan dan pengaman nyata, tidak mengubah ambang model atau menyimpan tanpa Simpan. Pengujian ini sintetis; pengambilan pada kamera dan wajah nyata tetap perlu dicoba pengguna.
