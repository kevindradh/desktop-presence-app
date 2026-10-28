# Gerbang penerimaan yang masih terbuka

Daftar ini melanjutkan PLAN.md. Persetujuan review tahap sebelumnya dan data simulasi tidak menggantikan bukti pengujian yang belum tersedia.

| Pekerjaan | Bukti yang diperlukan | Keadaan saat ini |
|---|---|---|
| Coverage unit ≥80% | Klasifikasi suite unit yang jelas, pengujian perilaku yang bermakna, laporan scope/exclusion | Gabungan89,73%; subset tanpa database/model43,56%, masih mencakup UI/native credential. Target unit murni belum terbukti |
| Akurasi wajah ≥98% | Percobaan peserta dengan probe berbeda dari enrollment; jumlah benar, salah identitas, ditolak; probe tidak terdaftar | Pengguna menyatakan belum ada catatan nyata |
| Penolakan spoof ≥95% | Foto cetak, foto layar dan video replay; jumlah diterima/ditolak per jenis, serta penolakan wajah asli | Protokol tersedia; catatan terukur belum tersedia |
| Search ≤100ms | Semua latency dan query pertama pada konfigurasi target; pemeriksaan cache/I/O/penjadwalan | p95 produksi50,92ms;3/1.000query>100ms, maksimum228,82ms, query pertama132,26ms. PERF-B001 tetap OPEN |
| Latency pipeline | Detection, recognition, save dan end-to-end terpisah, konfigurasi kamera/model, semua latency serta ringkasan | Search diukur terpisah; search tidak mewakili seluruh pipeline |
| Startup <5detik | Pengukuran sampai UI dapat dipakai dan komponen wajib siap, beberapa pengulangan | Smoke startup bukan sertifikasi batas waktu |
| Stabilitas kamera0 | Uji buka/tutup serta isolasi penyebab gagal pertama pada runtime final | CAM-B004 OPEN; percobaan pertama gagal, preview/reopen ulang lulus1280x720 tanpa patch capture produksi |
| Soak/multi-kamera | Pengamatan berjam-jam pada kamera target, memori/CPU/antrean, putus-sambung dan pemulihan | Kamera kedua ditunda; observasi panjang belum selesai |
| Availability99,5% | Jam layanan, periode observasi, downtime aktual dan rumus perhitungan | Periode pengamatan belum tersedia |
| RTSP positif | Sumber RTSP nyata dan pengujian kredensial/putus-sambung; rahasia dimasukkan langsung di aplikasi | Perangkat belum tersedia |
| Windows AMD fisik | Instalasi akun standar, kamera/AI, login, absensi, ekspor, cadangan/pemulihan pada perangkat customer | Pengguna memilih Parallels dahulu; hasil VM tidak membuktikan seluruh AMD |
| UAT dan penerimaan V1 | Semua AC yang diwajibkan selesai, defect ditinjau, hasil akhir diterima pengguna | Kandidat internal dapat diuji; gerbang V1 belum ditutup |

Gunakan [protokol penerimaan](acceptance-strategy.md) dan [peta31 user story](stage-15-acceptance-map.md) untuk mencatat hasil. Sediakan catatan jumlah/latency tanpa mengirim foto, embedding atau kredensial. Pengujian manusia memerlukan persetujuan peserta sesuai kebijakan proyek. Usulan jumlah sampel dan periode pada protokol belum berubah menjadi hasil aktual atau jaminan statistik.

Saat bukti baru tersedia, catat tanggal, versi paket/hash, perangkat, setelan, jumlah percobaan dan hasil. Ulangi kasus gagal setelah perbaikan, kemudian perbarui PLAN.md. Jangan mengubah NOT RUN atau BLOCKED menjadi PASS hanya karena installer berhasil dibuat.
