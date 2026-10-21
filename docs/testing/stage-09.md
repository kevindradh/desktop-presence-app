# Tahap 9 — pengaturan dan konfigurasi aktif

Tanggal: 19 Oktober 2026. Status: implementasi/verifikasi otomatis PASS; review pengguna disetujui dan Tahap 10 diizinkan.

Pengguna menyatakan review Tahap 8 sudah OK dan mengizinkan lanjut. Penerimaan pengguna dicatat tanpa mengarang jumlah percobaan, skor wajah nyata, atau hasil per kondisi yang tidak dikirim. RTSP positif nyata tetap tertunda.

## Cakupan

- Menu **Pengaturan** tersedia untuk Super Admin/Admin. Operator/Viewer tidak dapat membaca/mengubah melalui layanan pengaturan maupun navigasi.
- Delapan nilai operasional disimpan pada tabel settings yang sudah ada: similarity 0,60; ukuran wajah Auto; timeout 3 detik; anti-spoof aktif; ambang anti-spoof 0,85; duplicate window 60 detik; awal check-in Shift; checkout otomatis nonaktif sebagai default opsional.
- Nilai numerik tervalidasi: similarity/keaslian 0–1, timeout >0 sampai 300 detik, duplicate window bilangan bulat 1–86400 detik. Boolean ketat, bukan string atau angka. Auto/Shift adalah satu-satunya mode yang ditentukan PDF; tidak mengarang pilihan lainnya.
- Snapshot konfigurasi berasal dari database saat alur capture/probe dibuat, melekat pada binding HMAC privat. Uji wajah tersimpan memakai similarity, timeout dan kebijakan liveness snapshot tersebut. Perubahan di tengah proses tidak mencampur konfigurasi baru/lama; mulai pemeriksaan baru untuk mengambil nilai terbaru. Proses query probe menggunakan ambang snapshot yang sama, bukan nilai .env atau nilai terbaru pada saat tombol Bandingkan ditekan.
- Registrasi lima sudut tetap memakai liveness aktif/0,85 sesuai kebijakan enrollment Tahap 8; similarity identitas dan timeout mengikuti snapshot. Mengubah anti-spoof tidak menurunkan pemeriksaan registrasi.
- Setiap perubahan nonrahasia mencatat setting_key, nilai lama/baru dan aktor. Menyimpan nilai yang sama tidak membuat audit perubahan. Batch perubahan dan audit berada dalam satu transaksi. Konflik snapshot menolak simpan, mempertahankan isian, dan meminta muat ulang eksplisit.
- Tidak menambah dependency/migrasi. Tabel settings harus lengkap/valid; nilai hilang/rusak gagal tertutup, tidak diam-diam beralih ke .env. Jalankan seed/pemeriksaan database jika belum lengkap.

## Batas tahap

Duplicate window, awal shift dan checkout otomatis disimpan untuk modul absensi Tahap 10. Tahap 9 tidak mencatat attendance, belum membuktikan seluruh US-028 pada absensi end-to-end, dan tidak mengklaim checkout otomatis telah berjalan. Liveness engine dan perubahan ambang pada query pengenalan sudah dapat diuji melalui **Anggota → Uji wajah tersimpan**.

Pada Tahap 10, hasil scan dengan konfigurasi kedaluwarsa harus ditolak/diperiksa ulang sebelum commit; kebijakan liveness aktif wajib berlaku pada setiap attendance baru. Snapshot uji probe Tahap 9 tidak boleh dipakai untuk membenarkan commit attendance dengan anti-spoof lama yang nonaktif. Skenario perubahan pengaturan saat scan berlangsung ditambahkan ke PLAN Tahap 10.

Alat mandiri `scripts/demo_ai.py` tetap laboratorium tanpa database, memakai konfigurasi .env. Gunakan `main.py` untuk menguji perubahan dari menu Pengaturan. Pengaturan koneksi database, rahasia, zona waktu, session timeout/lockout tidak diedit pada halaman ini.

## Uji mandiri

1. Tutup aplikasi lama, jalankan PostgreSQL lokal dan `main.py`. Masuk sebagai Super Admin atau Admin.
2. Buka **Pengaturan**. Pastikan nilai tersimpan tampil. Jika belum pernah diubah, default sesuai daftar di atas.
3. Ubah ambang kecocokan menjadi **0,65**, timeout menjadi **4**, jeda menjadi **90**, lalu **Simpan pengaturan**. Harus ada pesan berhasil. Kembali ke menu lain lalu Pengaturan, tutup/buka aplikasi dan login: nilai tetap sama.
4. Pilih anggota aktif yang sudah diregistrasi, buka **Uji wajah tersimpan**. Teks konfigurasi harus menunjukkan similarity **0,65** dan timeout **4**. Berikan persetujuan sementara, mulai kamera, ambil probe dan bandingkan. Skor 0,60–<0,65 harus tidak cocok pada ambang 0,65; wajah yang mendapat skor lebih tinggi tetap dapat cocok. Jangan mengharapkan skor wajah nyata selalu berada pada rentang batas ini.
5. Aktifkan anti-spoof, set ambang keaslian yang diinginkan dan simpan. Buka pemeriksaan baru: status aktif/ambang benar, probe yang ditolak keasliannya tidak dapat diteruskan ke pembandingan. Jika menonaktifkannya untuk uji, peringatan **NONAKTIF** terlihat dan pemeriksaan baru memakai kebijakan itu. Kembalikan aktif setelah pengujian. Jangan memakai hasil foto/replay satu percobaan sebagai bukti ketahanan produksi.
6. Buka registrasi lima sudut: liveness tetap aktif/0,85 walau pengenalan sementara dinonaktifkan anti-spoof. Ini kebijakan registrasi yang disengaja.
7. Coba nilai di luar rentang/tipe pada form. Widget membatasi masukan; jangan mengubah database development secara langsung untuk membuat nilai rusak. Validasi layanan untuk input tidak valid diuji otomatis.
8. Ketik/edit angka dan tunggu beberapa detik. Pemeriksaan sesi tidak boleh mereset nilai atau menghilangkan fokus input.
9. Jika tersedia dua sesi Admin, muat Pengaturan pada keduanya. Simpan perubahan di sesi A, lalu coba simpan isian lama di sesi B: ditolak karena sesi lain mengubahnya. **Muat ulang dari database** mengambil nilai terbaru. Isian tidak otomatis ditimpa saat pesan konflik tampil.
10. Login sebagai Operator/Viewer: menu Pengaturan tidak tersedia. Pengujian otomatis juga menolak pemanggilan langsung layanan.
11. Checkout otomatis/jeda/awal shift cukup diperiksa persistensinya pada tahap ini; pengujian perilaku absensi menunggu Tahap 10. Kembalikan nilai yang dipilih untuk operasi setelah selesai.

Jika menemukan masalah, catat langkah, role, nilai sebelum/sesudah, pesan yang tampil dan konfigurasi yang terlihat pada pemeriksaan baru. Tidak perlu mengirim foto, embedding, password atau isi .env.

## Verifikasi otomatis

Regresi lengkap setelah perbaikan lifecycle: **284 PASS, 0 failure/error/skip**, coverage app+database+ai **90,37% (4703/5204 statements)**, durasi 254,61 detik. Model terpasang diuji pada input sintetis/fixture publik yang sudah dipakai Tahap 7; tidak membaca kamera atau mengubah biometrik development. Satu FutureWarning upstream InsightFace/scikit-image tetap terlihat. Pemeriksaan skema development baca saja PASS: revision 0004_devices, at_head/schema_valid true. **37 tes native macOS PASS** (83,55 detik), termasuk settings, enrollment, administrasi, login/fokus dan reuse pekerjaan. Tujuh uji fokus terisolasi juga PASS. Bukti ini tidak menggantikan review pengguna.

Bukti: [regresi XML](evidence/stage-09-tests.xml), [GUI native XML](evidence/stage-09-native.xml), [tampilan sintetis](evidence/stage-09-settings.png), [ringkasan](evidence/stage-09-summary.json). Laporan coverage lengkap tersimpan lokal pada .local/stage-09-coverage.json.

Dokumentasi SQLAlchemy diperiksa melalui MCP Context7: [transaksi Session](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), [FOR UPDATE](https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.Select.with_for_update). Row lock berurutan dan snapshot yang dibandingkan mencegah overwrite tanpa pemberitahuan, di dalam guard auth transaksi yang sama.

## Debug lifecycle Qt

Run awal regresi lengkap dihentikan setelah terbukti deadlock: sample proses memperlihatkan GUI menunggu mutex koneksi Qt pada QTimer.singleShot, sementara destructor worker di thread lain menunggu GIL. TaskController kini memakai timer join persisten yang terhubung saat init. Poll tetap nonblocking dan tidak memulai tugas berikut sebelum thread bergabung. Uji tambahan menjalankan 100 pekerjaan berurutan sambil heartbeat GUI aktif; suite penuh dan native diulang setelah perubahan. Run awal yang dihentikan tidak dianggap PASS. Penghentian paksa dapat meninggalkan schema fixture sintetis di stargate_test; schema tanpa bukti kepemilikan tidak dihapus massal. Database development tidak diubah.

Uji native awal juga mengalami kegagalan pada prasyarat fokus, sebelum polling session diuji. Pengulangan terisolasi masih menunjukkan aktivasi asynchronous. Helper tes kini menaikkan/mengaktifkan jendela dan menunggu `QTest.qWaitForWindowActive`, sesuai [dokumentasi QWidget](https://doc.qt.io/qt-6/qwidget.html#activateWindow) dan [QTest](https://doc.qt.io/qt-6/qtest.html#qWaitForWindowActive), diperiksa melalui Context7. Assertion fokus selama/sehabis polling dan pengetikan tidak dilemahkan. Tujuh kasus terkait terisolasi lulus sebelum pengulangan paket native akhir.

Pemeriksaan akhir setelah perubahan helper aktivasi (tanpa perubahan produksi tambahan): **12 tes fokus/settings/lifecycle pada mode biasa PASS**, bukti [XML regresi terarah](evidence/stage-09-focus-regression.xml). Tidak ada sesi tes yang masih berjalan.

Review pengguna: setelah panduan tes mandiri, pengguna menyatakan review sudah OK dan mengizinkan Tahap 10. Tidak ada skor/jumlah trial tambahan yang dilaporkan.
