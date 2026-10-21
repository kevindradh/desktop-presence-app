# Tahap 10 — absensi wajah dan aturan shift

Tanggal: 19 Oktober 2026. Status: implementasi/verifikasi otomatis PASS; menunggu uji mandiri kamera/audio dan review pengguna. Tahap 11 belum dimulai.

Pengguna menyetujui review Tahap 9 dan mengizinkan lanjut. Pengguna secara eksplisit memilih menolak check-in sebelum shift dan mengizinkan mulai tepat jam shift. Persetujuan review tidak diubah menjadi skor/jumlah percobaan wajah nyata yang tidak dilaporkan.

## Perilaku yang tersedia

Menu **Kehadiran** untuk Super Admin/Admin/Operator memakai perangkat yang sudah disimpan. Operator dapat menjalankan perangkat yang tersedia, tanpa memperoleh hak mengelola perangkat atau menampilkan kredensial RTSP. Viewer tetap hanya Reports. Kamera baru dibuka setelah persetujuan peserta, pemilihan perangkat/mode, dan **Mulai absensi**. Maksimum stream mengikuti konfigurasi kamera (default dua).

Pipeline kamera → RetinaFace → liveness bila aktif → ArcFace → pgvector → validasi → transaksi attendance/audit berjalan di luar thread GUI. Satu target terbesar dipilih deterministik per kamera sesuai Tahap 7. Foto/video/probe dari scan tidak disimpan sebagai aset atau embedding baru. Probe sementara bertanda tangan memuat versi model, skor liveness, binding sesi/perangkat/pengaturan, sequence dan freshness. Bukan bukti attestation terhadap host yang sudah dikuasai.

Setiap transaksi memeriksa sesi/role terbaru, perangkat/lokasi, versi konfigurasi, liveness dan kecocokan. Versi mencakup nilai serta updated_at, sehingga konfigurasi yang berubah lalu dikembalikan pun membatalkan hasil lama. Saat konfigurasi/perangkat berubah, scan ditolak dan pengguna diminta mulai ulang. Tidak ada pesan/suara sukses sebelum commit. Jika database/audit gagal, tidak ada attendance parsial. Probe gagal/tidak dikenal tidak menambah riwayat.

### Transisi

| Kondisi sebelumnya | AUTO | Mode eksplisit yang sah |
|---|---|---|
| Belum masuk shift | IN | IN |
| IN | OUT | OUT, BREAK_OUT |
| BREAK_OUT | BREAK_IN | BREAK_IN |
| BREAK_IN | OUT | OUT, BREAK_OUT |
| OUT | Ditolak sampai sesi shift berikutnya | Tidak menerima event tambahan pada sesi yang sama |

Jeda default **60 detik berlaku per anggota lintas kamera/terminal**; <60 ditolak, tepat 60 lolos jeda dan masih harus lolos state. Memilih IN eksplisit tetap menolak IN kedua. Setelah sukses pada kamera yang sama, wajah perlu tidak terdeteksi setidaknya satu detik untuk mengaktifkan scan berikutnya. Ini mencegah wajah yang terus berdiri di kamera berubah menjadi OUT setelah 60 detik. Orang berbeda tetap dapat diproses. Penahan ini tambahan pencegahan salah scan, bukan pengganti cooldown/liveness.

### Shift dan tanggal

- Penugasan tanggal harus berlaku. Tanpa kalender khusus, penugasan berlaku setiap tanggal dalam rentangnya; baris kalender nonhari kerja/izin yang tersedia menolak IN baru.
- Check-in dimulai tepat jam shift dan berakhir sebelum jam selesai. 08:00 + grace 10: 08:05 dan tepat 08:10 Present, sesudah 08:10 Late. Status IN dipertahankan pada event berikutnya; OUT awal ditandai terpisah.
- Shift 20:00–04:00 memakai tanggal kerja saat mulai, walaupun OUT lewat tengah malam. Waktu disimpan absolut UTC dan ditampilkan dalam zona aplikasi; pemilihan tanggal shift mengikuti zona lokasi kamera.
- Sesi IN yang belum ditutup diprioritaskan sebelum membuka sesi shift baru. OUT manual boleh setelah shift selesai. BREAK_IN setelah akhir shift masih boleh untuk menyelesaikan istirahat terbuka, kemudian OUT setelah jeda; memulai istirahat baru setelah akhir shift ditolak.
- Riwayat anggota menampilkan sumber Scan/Otomatis dan tetap tersimpan saat anggota dinonaktifkan.

### Checkout otomatis

Default nonaktif, diaktifkan lewat Pengaturan. Saat aplikasi terbuka dan pengguna dengan hak Attendance sudah masuk, pemeriksaan dilakukan setelah login dan setiap 10 detik, maksimal 100 sesi jatuh tempo per transaksi. Saat aplikasi tertutup tidak ada service sistem terpisah; login berikutnya melakukan catch-up. Event OUT memakai waktu akhir shift, ditandai **Otomatis**, mempertahankan status/group sesi IN, tidak mengganti OUT manual, dan tidak membuat OUT tanpa IN. Sesi terbuka anggota yang kemudian nonaktif tetap dapat difinalisasi. Jika istirahat belum kembali, checkout otomatis menutup sesi tanpa mengarang BREAK_IN. Audit memakai aktor yang menjalankan pemeriksaan otomatis. Ini bukan bukti bahwa orang hadir secara fisik sampai akhir shift.

## Tes mandiri

Untuk persiapan dan skenario otomatis satu klik, jalankan [aplikasi demo Tahap 10](stage-10-demo.md). Data awal, kamera/wajah sintetis, jam simulasi dan ekspor hasil sudah tersedia; data operasional tidak dipakai.

Untuk pengujian lebih cepat, gunakan [template checklist dan hasil tes mandiri](stage-10-manual-template.md): persiapan sekali, jalur satu anggota sekitar 10–15 menit, skenario pelengkap, dan format laporan masalah. Semua hasil awal berstatus BELUM DIUJI.

1. Tutup aplikasi lama. Jalankan PostgreSQL lokal dan `main.py`; login Super Admin/Admin. Operator dapat menjalankan absensi setelah Admin menyiapkan perangkat/shift.
2. Gunakan anggota uji yang sudah diregistrasi lima sudut, masih aktif dan memiliki penugasan shift hari ini. Pastikan jam shift sesuai jam lokal. Jangan mengubah jam sistem untuk menguji.
3. Pada Pengaturan, untuk awal gunakan similarity 0,60, anti-spoof aktif/0,85, jeda 60 detik dan checkout otomatis nonaktif. Simpan, lalu buka Kehadiran.
4. Pilih satu kamera yang benar, mode **Masuk** atau **Otomatis**, centang persetujuan peserta, lalu Mulai absensi. Tunggu model/kamera siap. Wajah terdaftar yang lolos harus menghasilkan pesan sukses, suara, dan satu baris IN. Periksa juga Anggota → riwayat setelah meninggalkan halaman.
5. Tetap berada di depan kamera melewati 60 detik: tidak boleh otomatis tercatat OUT. Setelah itu tinggalkan area kamera minimal satu detik, kembali setelah jeda cukup: AUTO menghasilkan OUT. Jika kembali sebelum 60 detik, scan ditolak. Tepat batas 60 diuji otomatis dengan jam terkontrol; manual lebih mudah tunggu 61 detik.
6. Untuk mode IN, hentikan lalu mulai kembali dengan mode yang sama; IN kedua pada shift yang sama ditolak walau jeda sudah lewat. Setelah OUT, scan ketiga pada shift sama ditolak.
7. Uji istirahat pada sesi shift baru/anggota uji lain: IN → (jeda) BREAK_OUT → (jeda) BREAK_IN → (jeda) OUT. Hentikan dan ubah mode sebelum mulai lagi. Mode tidak sah tidak boleh menambah baris.
8. Uji wajah belum terdaftar serta foto cetak/replay dengan anti-spoof aktif: tidak ada baris/suara sukses untuk wajah tidak dikenali atau yang ditolak keasliannya. Jika sebuah serangan lolos, laporkan sebagai temuan; keberhasilan beberapa percobaan tidak membuktikan target akurasi produksi.
9. Untuk batas shift, buat shift uji beberapa menit ke depan dan tugaskan anggota uji. Scan sebelum mulai harus ditolak; mulai tepat jamnya diizinkan. Untuk pulang awal, OUT sebelum akhir mendapat tanda Ya. Kasus 08:05/08:10/08:11 dan shift malam diuji otomatis; uji nyata dapat memakai jadwal yang sesuai tanpa mengubah jam komputer.
10. Untuk checkout otomatis, gunakan sesi uji yang masih IN dan shift singkat. Hentikan kamera bila perlu, aktifkan checkout otomatis melalui Pengaturan dan biarkan aplikasi terbuka/melewati akhir shift. Dalam sekitar 10 detik setelah akhir, periksa riwayat dengan Muat ulang: satu OUT bertanda Otomatis pada jam akhir shift. Ulangi Muat ulang/login: tidak ada OUT tambahan. OUT manual yang sudah tersimpan tetap Scan. Kembalikan kebijakan operasi setelah tes.
11. Jika ada dua perangkat dengan nomor/sumber berbeda, pilih keduanya memakai Cmd/Ctrl. Tunjukkan anggota yang sama hampir bersamaan: hanya satu event tersimpan dalam jeda. Kamera lokal tidak otomatis dibuka ulang saat USB dicabut; aplikasi berhenti dan meminta pemeriksaan nomor kamera/mulai manual.
12. Saat absensi berjalan, coba Hentikan, pindah menu, ganti password, logout dan tutup aplikasi. Kamera/model berhenti, tidak ada scan baru. Transaksi yang sudah dimulai tetap diselesaikan atomik; tidak dibatalkan paksa di tengah commit.
13. Uji perubahan pengaturan dari akun Admin lain ketika kamera aktif: hasil dari konfigurasi lama tidak disimpan, muncul permintaan mulai ulang. Pada pemeriksaan baru, nilai terbaru dan status anti-spoof terlihat. Session timeout juga menghentikan pemeriksaan; input wajah tidak memperpanjang sesi operator.
14. Tutup/buka aplikasi dan periksa riwayat kembali. Jika anggota uji dinonaktifkan, biometrik dihapus sesuai retensi dan riwayat attendance tetap ada. Gunakan data uji untuk tindakan ini.

Gangguan database sebelum commit, kegagalan audit, race, replay packet dan batas mikrodetik diuji otomatis di database uji; jangan merusak database development untuk simulasi. Audit baru tersimpan pada database, antarmuka inspeksi audit tetap Tahap 13. Dashboard real-time/rekap/ekspor tetap tahap berikutnya.

## Bukti dan batas pengujian

Regresi akhir **334 PASS, 0 failure/error/skip**, coverage app+database+ai **89,90% (5285/5879 statements)**, durasi **295,17 detik**. Empat kasus tambahan expiry selama query/write serta continuous face lintas dua kamera juga lulus pada run terarah sebelum regresi akhir. **47 tes GUI native macOS PASS**, durasi **112,47 detik**, termasuk dua kamera sintetis, aturan feedback/suara, stop/logout/timeout/close, settings, enrollment, administrasi dan fokus input. Pemeriksaan skema development baca saja PASS: revision 0004_devices, at_head/schema_valid true. Satu FutureWarning upstream InsightFace/scikit-image tetap terlihat. Pengujian otomatis memakai schema stargate_test terisolasi, wajah/frame sintetis dan fixture publik berlabel. Suara sukses diuji sebagai permintaan pemutaran setelah commit; keluaran speaker nyata, absensi kamera nyata dan foto/replay harus diuji mandiri. Tidak mengklaim benchmark/SLA atau semua RTSP/Windows lulus dari pengujian ini.

Context7: [transaksi SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), [row locking](https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.Select.with_for_update), [Qt QSoundEffect](https://doc.qt.io/qt-6/qsoundeffect.html). Tidak ada library/migrasi baru. WAV sukses dua nada dibuat lokal dan tidak memakai aset audio pihak ketiga.

Bukti akhir: [regresi XML](evidence/stage-10-tests.xml), [GUI native XML](evidence/stage-10-native.xml), [gambar UI sintetis](evidence/stage-10-attendance-synthetic.png), [ringkasan](evidence/stage-10-summary.json). Coverage lengkap tersimpan lokal di .local/stage-10-coverage.json.

Perbaikan kasus dua kamera: stream yang mengenali anggota dalam cooldown ikut menahan anggota tersebut sampai ada satu detik tanpa wajah, sehingga kamera kedua yang melihat wajah terus-menerus tidak menghasilkan OUT ketika cooldown habis. Ini tetap memakai kondisi detektor, bukan bukti fisik bahwa orang benar-benar meninggalkan lokasi.

Tinjauan visual gambar UI native sudah dilakukan: teks, kontrol, status konfigurasi dan notifikasi tersimpan terlihat; area warna adalah fixture kamera sintetis. Riwayat di bawah preview dapat dilihat dengan menggulir. Bukti screenshot tidak memuat wajah nyata. Tidak ada sesi tes yang masih berjalan.

Review pengguna diterima pada 20 Oktober 2026 dan Tahap 11 diizinkan. Persetujuan ini tidak menambahkan jumlah percobaan kamera/foto/replay/audio yang belum dilaporkan. Hasil dan batas verifikasi berikutnya dicatat pada [Tahap 11](stage-11.md).
