# Logo StarGate

Logo berasal dari PNG transparan yang diberikan pengguna, `Forest Green Archway Star Emblem.png`. Berkas PNG disalin tanpa mengubah bentuk, warna, atau proporsinya. ICO dan ICNS merupakan konversi format untuk ikon sistem operasi.

## Penerapan

- Logo dan nama StarGate berada di tengah panel masuk, pembuatan Super Admin, ganti password, dan persiapan aplikasi.
- Sidebar memakai simbol hijau dengan alas putih kecil supaya terbaca di latar gelap; nama StarGate tetap di sebelahnya.
- QApplication dan kedua jendela utama memakai ikon yang sama.
- Spec PyInstaller menyertakan aset dan ikon executable; Inno Setup memakai ikon untuk installer. Source kit menyertakan PNG, ICO, dan ICNS.
- Versi source installer berikutnya adalah0.14.3-research. Installer dan arsip0.14.2 yang sudah dibuat tetap dipertahankan dan belum memuat perubahan logo ini.

## Aset

`resources/branding/stargate.png`: PNG asli1254×1254, transparan. `stargate.ico`: ukuran16,24,32,48,64,128,256piksel. `stargate.icns`: format ikon macOS. Pembacaan UI memakai resource bundle, terpisah dari folder data pengguna.

## Pemeriksaan

- PASS: PNG di proyek identik dengan berkas yang diberikan pengguna.
- PASS: preview panel masuk, pembuatan Super Admin pada1000×740 dan sidebar diperiksa; tombol tetap terlihat dan tidak ada overflow horizontal pada navigasi.
- PASS:31tes packaging/session (PostgreSQL nyata),1SKIP tes model yang tidak diaktifkan pada run ini;9tes shell/bootstrap tambahan lulus.
- PASS: source package-check untuk Qt/plugin/native/spawn dan keberadaan logo; tidak mengklaim uji executable Windows baru.
- PASS: aset berada dalam allowlist source kit dan konfigurasi bundle/installer.

## Pemeriksaan desain

Arah mengikuti logo pilihan pengguna dan antarmuka hijau yang sudah ada. ENERGY1/RHYTHM1/MOTION1: identitas bertambah melalui simbol, tanpa animasi atau perubahan layout halaman lain. Alas putih menjaga kontras simbol hijau pada sidebar. Posisi merek di panel masuk tetap terpisah dari judul formulir. Ikon tidak menerima fokus keyboard dan memiliki nama aksesibel. Tidak ada aset ilustrasi atau klaim produk tambahan.
