# Strategi pengujian dan penerimaan

Tanggal: 18 Oktober 2026. Status: usulan baseline Tahap 0; seluruh pengujian produk NOT RUN.

## Lingkungan dan pemisahan hasil

- Development: macOS arm64 (disetujui). Distribution: Windows (disetujui); versi Windows, CPU/RAM/GPU dan driver kamera dicatat sebelum uji deployment.
- Database awal PostgreSQL lokal satu komputer (disetujui), dengan pgvector nyata; test database terpisah dari data operasional.
- Jangan mengganti PostgreSQL dengan SQLite untuk mengklaim integrasi pgvector lulus.
- Unit test boleh menggunakan stub untuk error deterministik; test model/kamera nyata tetap terpisah.
- Untuk setiap run catat commit/versi kode, versi Python/dependensi/model, OS/hardware, kamera/resolusi/FPS, ukuran database, setting, timestamp/zona waktu, dan alat ukur.
- CPython sistem 3.14.8 hanya hasil inventaris. Versi runtime proyek diputuskan dan di-lock setelah pemeriksaan kompatibilitas Tahap 1.

## Lapisan verifikasi

1. Unit: validasi field, aturan role, state absensi, cooldown, grace, tanggal shift, agregasi dan format. Fake clock untuk kasus batas waktu; jangan memakai sleep untuk unit test.
2. Integration: PostgreSQL/pgvector, transaksi/race, migrasi, settings, audit, file ekspor, backup/restore.
3. UI: alur per role, tombol/validasi, feedback, navigasi, worker, startup/shutdown. Test manual yang terlihat ditinjau bersama pengguna.
4. Hardware/model: webcam internal/USB/RTSP nyata, RetinaFace, ArcFace, MiniFASNet; frame prerecorded membantu regresi tetapi bukan bukti semua perangkat lulus.
5. Performance/reliability: benchmark terkontrol, multi-camera, durasi panjang, gangguan DB/kamera, packaging macOS/Windows.
6. UAT: jalankan TC katalog pada build distribusi dengan data yang disetujui; dokumentasikan penerimaan pengguna.

## Usulan protokol SLA (perlu keputusan D-20/D-21)

- Gunakan jam monotonic resolusi tinggi untuk latency; jangan mengurangi timestamp kalender.
- Laporkan semua pengamatan, jumlah sampel, p50/p95/max, kegagalan dan kondisi cold/warm. Usulan gerbang latency: p95 memenuhi target pada hardware target; maksimum tetap dilaporkan, tidak disembunyikan. Kriteria statistik ini belum ditetapkan PDF dan perlu disetujui.
- Detection <300 ms dari frame siap sampai bbox/landmark; recognition <500 ms mencakup embedding sampai identitas/similarity; DB search ditimer terpisah; attendance save <200 ms dari transaksi dimulai sampai commit.
- End-to-end dari frame dengan wajah layak diterima pipeline sampai commit dan feedback; antrean frame ikut dihitung. Ukur juga waktu pengguna mengikuti instruksi bila ada. Target MVP <=2s; usulan gunakan <2s untuk memenuhi ringkasan yang lebih ketat.
- Startup dari peluncuran proses sampai UI dapat dipakai dan model/koneksi wajib siap, <5s. Loading model belum selesai tidak boleh dianggap ready. Usulan 20 run startup dan >=200 scan valid per konfigurasi target; jelaskan bila sampel kurang.
- Database: minimal 10.000 member x 5 embedding (50.000 vector 512D). Usulan >=1.000 query independen, cold/warm terpisah, search <=100ms. Data sintetis dapat mengukur kinerja, bukan akurasi biometrik. Baseline exact; jika approximate diperlukan, ukur dampak recall terhadap hasil identitas.
- Recognition: usulan pilot >=20 relawan dewasa, enrollment 5 sudut; probe pada sesi berbeda, tidak menggunakan frame enrollment sebagai probe. Target evaluasi akhir >=1.000 genuine probe ditambah >=1.000 unknown/impostor probe; jumlah ini tidak menjamin generalisasi populasi 10.000. Jangan menambahkan klaim tersebut.
- Recognition accuracy dihitung sebagai correct enrolled identity / seluruh genuine probe pada protokol yang dilaporkan. Laporkan pula wrong identity, false rejection, dan false acceptance pada unknown probe; jangan mencampur true negative untuk menaikkan angka. Usulan target >98% untuk memenuhi ringkasan; MVP >=98% dilaporkan juga. Keputusan batas FAR/FRR tambahan belum ditentukan PDF.
- Liveness: usulan >=100 percobaan tiap kategori foto cetak, foto layar, video replay, dengan variasi pencahayaan/kamera; setelan threshold tidak diubah menggunakan holdout. Attack rejection = serangan ditolak / total serangan, target >=95%; laporkan per kategori dan agregat serta tingkat penolakan wajah asli. Test fixture serangan wajib ditolak sesuai US-009; skor agregat tidak menggantikan kegagalan AC.
- Availability: usulan observasi pilot 30 hari dalam jam layanan yang ditetapkan; availability = (waktu layanan terjadwal - downtime) / waktu layanan terjadwal x 100%. Laporkan planned/unplanned downtime dan penyebab. Target 99,5% belum terbukti sebelum periode cukup; jangan mengklaim SLA dari soak test singkat.
- Soak test awal usulan 8 jam dua stream pada hardware target sebelum pilot. Catat memori, CPU, frame queue, latency, reconnect dan crash. Jumlah kamera target final belum diketahui.

## Definisi hasil dan bug

- PASS: expected terpenuhi dengan bukti aktual.
- FAIL: expected tidak terpenuhi; buat bug dan hubungkan ID test.
- BLOCKED: prasyarat/keputusan/perangkat tidak tersedia; tidak dihitung PASS.
- NOT RUN: belum dijalankan.
- Coverage target >=80% untuk kode aplikasi yang disepakati. Cantumkan exclusion, jangan mengecualikan domain/service utama hanya untuk mencapai angka. Coverage tidak menggantikan pemeriksaan AC.
- Bug severity: Critical (data hilang/akses tidak sah/absensi salah sistemik), High (fitur inti gagal), Medium (fungsi terbatas dengan workaround), Low (kosmetik). Usulan; pemetaan akhir disepakati pada D-20.
- Gerbang tahap: semua kasus cakupan tahap PASS; kasus BLOCKED/NOT RUN tetap membuat gerbang tertunda. Implementasi belum memenuhi DoD bila audit/role atau dokumentasi belum diuji.
- Perbaikan: simpan reproduksi, akar penyebab, perubahan dan uji ulang; regresi dibatasi ke area terdampak, lalu full suite pada Tahap 15.

## Bukti dan penutupan

Simpan ringkasan per tahap di `stage-NN.md`, bukti tersanitasi di folder tahap, serta catatan defect di `../bugs.md`. Jangan menyimpan wajah asli, password, token, credential URL atau database dump di Git. Persetujuan tahap dicatat terpisah dari PASS teknis. Hasil tahap 0 adalah pemeriksaan dokumen, bukan pengujian aplikasi.
