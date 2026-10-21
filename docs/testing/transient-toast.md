# Toast pengganti status bar

Permintaan pengguna: hapus status bar dan tampilkan pesan/error melalui toast di pojok kanan atas, tanpa pesan yang menetap.

Login, setup Super Admin, Ganti password, dan ruang kerja memakai satu toast pada jendela sesi. Shell mandiri memakai komponen yang sama; dialog registrasi memakai toast di dalam dialognya. Semua pemanggilan status bar di aplikasi dan demo administrasi dihapus. Banner error yang sebelumnya mengambil ruang di atas halaman juga diganti toast.

Toast ditampilkan 5 detik, mempunyai tombol Tutup, dan tidak mengambil fokus input. Pesan baru menggantikan pesan sebelumnya. Pesan identik dalam 10 detik diabaikan tanpa memperpanjang timer agar kegagalan polling tidak membuat notifikasi terus menyala. Setelah jeda, pesan identik dapat ditampilkan lagi. Posisi mengikuti resize: 20 px dari atas/kanan, lebar maksimum 460 px, teks membungkus. Teks memakai PlainText, termasuk pesan yang memuat input pengguna.

Error dari halaman Anggota, Grup, Shift, Perangkat, Pengaturan, Kehadiran, Laporan, Audit, dan Cadangan diarahkan ke toast, termasuk validasi lokal password dan koneksi. Pesan status pemuatan, data kosong, hasil laporan/cadangan, serta notifikasi absensi di dalam kamera tetap mengikuti fungsi masing-masing. Detail error tak terduga tetap melalui ErrorReporter yang memberi pesan aman dan nomor referensi; exception mentah tidak ditampilkan.

Arah mengikuti hijau StarGate dan font sistem, ENERGY 1 / RHYTHM 2 / MOTION 1. Panel peach memakai warna banner error sebelumnya untuk membedakan umpan balik dari form. Posisi overlay tidak menggeser form; lebar dibatasi agar pesan terbaca tanpa menutup seluruh area kerja. Tidak menambah aset, ikon, animasi atau navigasi.

## Verifikasi dan Delivery Gate

- PASS, Hard Gate: tes toast memeriksa hilang otomatis, deduplikasi, tampil kembali setelah jeda, tombol Tutup, pengosongan, fokus input, serta posisi di dalam jendela pada 1000×740, 1180×820 dan 1440×900. Regresi error tak terduga memastikan pesan tidak memuat exception rahasia dan tetap menyertakan referensi. Render login dan shell ditinjau; keduanya tidak memiliki QStatusBar. Label, tombol dan isi toast tidak terpotong pada gambar.
- PASS, Purpose-Gate: alasan posisi, ukuran, warna, durasi dan jeda dicatat di atas. Warna diambil dari banner lama, bukan menambah warna dekoratif. Tidak menambah efek atau ilustrasi.
- PASS, Liveliness: dial tetap eksplisit; halaman tetap menjadi fokus, toast hanya memberi umpan balik sementara dengan hierarki yang sama seperti sebelumnya.
- PASS, Craftsmanship: aturan layanan/perizinan tidak berubah, form tidak dibangun ulang, dan notifikasi tidak mereset fokus. Pengujian lintas halaman memakai database terpisah dan kamera sintetis; status persisten yang berupa error telah dipindah ke toast. Pesan pemuatan dan isi operasional tetap ada.
- PASS, Copywriting: isi pesan memakai hasil layanan atau pesan aman ErrorReporter. Tombol Tutup menyebut tindakan, tanpa klaim atau jargon baru.

Bukti: `evidence/toast-core.xml`, `evidence/toast-ui.xml`, `evidence/toast-login.png`, dan `evidence/toast-workspace.png`. Gambar memakai login dan shell dengan halaman placeholder serta data sintetis, bukan dashboard operasional terbaru. Tidak menguji kamera fisik/akurasi model untuk revisi ini.

Hasil akhir: 10 tes komponen/error/bootstrap dan 83 tes UI/database lulus (93 total). Regresi UI meliputi login, sesi, administrasi, perangkat, pengaturan, absensi, dashboard, laporan, cadangan dan registrasi wajah. Pemeriksaan sumber tidak menemukan pemanggilan statusBar yang tersisa pada aplikasi maupun skrip demo.
