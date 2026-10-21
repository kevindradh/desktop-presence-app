# Hasil Tahap 7 — deteksi, embedding, pencarian dan liveness

Tanggal: 19 Oktober 2026. **Implementasi tersedia; gerbang pengujian nyata awal belum lulus.** Pengguna mengizinkan lanjut setelah review Tahap 6, dengan RTSP positif masih tertunda, dan menyetujui uji wajah sementara di memori. Tidak memulai Tahap 8.

## Implementasi dan batas data

- RetinaFace Caffe OpenCV CPU, confidence >=0,60, mempertahankan aspect ratio saat deteksi; bounding box dikembalikan ke koordinat input. Tidak memuat SCRFD atau FaceAnalysis.
- Model InsightFace 106 landmark membutuhkan bbox RetinaFace, kemudian lima titik (38/88/86/52/61) untuk transformasi ArcFace 112×112. Validasi urutan/geometri menolak landmark degenerat. Lima titik ditampilkan di pratinjau alat uji untuk pemeriksaan posisi.
- ArcFace w600k_r50 melalui get_feat InsightFace: input BGR crop; adapter melakukan BGR→RGB dan normalisasi tepat sekali. Output 512 finite, L2-normalized; model version menyertakan checksum ArcFace/landmark dan versi alignment.
- EmbeddingRepository menyimpan normalized vector; identify memakai cosine similarity = 1−cosine_distance, threshold 0,60 inklusif. Query hanya member/sample aktif dan model version sama, satu skor terbaik per member. Integrasi DB memakai data sintetis, termasuk embedding dari input tekstur buatan melalui model nyata. Tidak ada identitas biometrik asli dimasukkan database.
- MiniFASNetV2 crop berkonteks 2,7× bbox menjadi 80×80, **BGR float CHW 0–255**, softmax kelas 1 live; harus argmax 1 dan probability >=0,85. Ini satu checkpoint, bukan ensemble dua model.
- Default config similarity 0,60, anti-spoof aktif/0,85, recognition timeout 3 detik, max face size Auto. Alat uji menunjukkan konfigurasi yang benar-benar dimuat; bila anti-spoof dimatikan secara eksplisit lewat konfigurasi, hasil bukan bukti liveness.
- Kualitas awal: bbox minimal 64px, tidak memotong batas frame (margin 2px), gray mean 30–225, Laplacian variance >=35. Heuristik belum dikalibrasi pada holdout; tidak menurunkan threshold otomatis agar uji lulus.
- Registration/lab menolak lebih dari satu wajah. Recognition API memilih area terbesar, kemudian confidence dan koordinat secara deterministik; UI lab tetap menuntut satu orang.
- Berkas model dan definisi MiniFASNet dicek SHA256 sebelum parsing/torch.load(weights_only=True). Model hilang/rusak menolak pemeriksaan; tidak download otomatis atau melewati liveness yang aktif.
- Satu proses spawn menyimpan model selama sesi; satu frame shared-memory maksimal 960×540, satu permintaan aktif, tanpa backlog. Watchdog 3 detik menghentikan proses native macet; hasil yang tiba setelah deadline ditolak. Loading awal dibatasi 30 detik dan bukan bagian SLA scan.
- Alat uji terpisah tidak memiliki koneksi database. Frame, hasil embedding dan referensi hanya di memori; input shared slot dibersihkan setelah dibaca, frame lokal dibersihkan setelah analisis dan referensi dibuang saat clear/stop/close/proses dihentikan. Python/native allocator tidak memberi jaminan forensic secure erase; tidak ada janji semacam itu.

Tidak ada dependensi atau migrasi baru. Model lisensi evaluasi penelitian/nonkomersial dan clearance distribusi dari Tahap 1 tetap berlaku; Tahap 7 tidak menyelesaikan izin distribusi model.

## Bukti dan status pengujian

Regresi akhir **233 PASS, 0 fail/error/skip**, satu FutureWarning upstream; coverage **91,14% (4034/4426 statement)**. **7 tes kontrol proses/GUI macOS native PASS**. Hasil run akhir ada di [ringkasan](evidence/stage-07-summary.json), [JUnit regresi](evidence/stage-07-tests.xml), dan [JUnit native macOS](evidence/stage-07-native.xml). Coverage mencakup app, database **dan ai**, tanpa mengecualikan proses anak. Badan proses anak tidak seluruhnya tercatat oleh coverage parent; bukti proses/model nyata dicatat terpisah. Tidak menyimpulkan akurasi dari persentase coverage.

| ID | Skenario | Status |
|---|---|---|
| AI-01 | Input/opsi invalid, unit normalization, cosine sama/ortogonal/lawan | PASS, unit terkendali |
| AI-02 | No face, multi-face, target deterministik, kecil/terpotong/gelap/terang/blur | PASS, input terkendali; deteksi blank juga model nyata |
| AI-03 | BGR/range MiniFASNet, crop boundary, live class/threshold inclusive, spoof tidak mengeluarkan embedding | PASS, unit + model nyata; bukan penerimaan serangan fisik |
| AI-04 | Missing/corrupt checksum menolak load, typed model output dan geometry invalid | PASS, unit dan model terpasang |
| AI-05 | Detektor, 106 landmark, alignment dan ArcFace nyata saling terhubung | PASS pada fixture publik lokal scikit-image; gambar/embedding tidak disalin ke proyek |
| AI-06 | Real model process ready→analyze blank→no_face→stop; tanpa embedding keluar dari proses | PASS, model nyata |
| AI-07 | PostgreSQL roundtrip, known/unknown numerik, model version, member/sample nonaktif | PASS; identitas/vektor sintetis dan input tekstur model nyata, bukan akurasi manusia |
| AI-08 | Load/inference hang, hasil terlambat, single request/backpressure, clear/restart/force cleanup | PASS dengan worker sintetis |
| AI-09 | Consent, reference/compare/clear, scalar trial log, stop, close saat inference berjalan | PASS pada Qt offscreen dan macOS; kamera sintetis untuk screenshot |
| AI-10 | Kamera nyata nomor 0, delapan permintaan, release | PASS transport/deteksi/quality rejection: seluruhnya partial_face; tidak mencapai acceptance live/recognition |
| AI-11 | Wajah asli layak lolos liveness, referensi dan probe berbeda frame/session, orang lain tidak cocok | NOT RUN penuh; memerlukan uji mandiri peserta |
| AI-12 | Foto cetak, foto layar dan video replay melalui kamera | NOT RUN; pengguna akan menguji sendiri |
| AI-13 | SLA/akurasi/anti-spoof statistik penuh, 10.000 anggota, Windows | NOT RUN; Tahap 15/14 |

Bukti kamera agregat tanpa gambar/embedding: [camera smoke](evidence/stage-07-camera.json). Wajah pada sesi itu terdeteksi menyentuh batas gambar; engine menolak sebelum liveness/embedding. Jangan menyebutnya keberhasilan pengenalan atau penolakan spoof. Screenshot [alat uji](evidence/stage-07-lab-synthetic.png) hanya bidang warna dan respons buatan, bukan bukti pengenalan wajah asli.

## Dokumentasi dan temuan

MCP Context7 memilih `/deepinsight/insightface` untuk alignment dan preprocessing ArcFace. Pencarian MiniFASNet tidak menemukan paket upstream yang sesuai, sehingga kode resmi pada commit manifest diperiksa langsung. Referensi:

- [InsightFace norm_crop](https://github.com/deepinsight/insightface/blob/master/python-package/insightface/utils/face_align.py), [ArcFace get_feat](https://github.com/deepinsight/insightface/blob/master/python-package/insightface/model_zoo/arcface_onnx.py), [model 106 landmark dan markup](https://github.com/deepinsight/insightface/tree/master/alignment/coordinate_reg).
- [MiniVision functional.to_tensor yang dipin](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing/blob/b6d5f04ad78778917853b25c778acef6d5626d15/src/data_io/functional.py) mengembalikan float tanpa /255 walaupun docstring ToTensor mengatakan sebaliknya. Unit test menjaga channel BGR dan nilai 20/100/255 tetap sama. Perbedaan ini ditemukan sebelum penerimaan, bukan menyesuaikan ambang dari hasil kamera.
- [MiniVision crop](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing/blob/b6d5f04ad78778917853b25c778acef6d5626d15/src/generate_patches.py), [kelas live pada test upstream](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing/blob/b6d5f04ad78778917853b25c778acef6d5626d15/test.py). Skor satu model tidak dibagi dua seperti contoh ensemble upstream.
- [Fixture astronaut scikit-image](https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.astronaut): foto NASA domain publik, sudah terpasang di dependensi; hanya dibaca untuk pengujian komponen, tidak diunduh/disalin atau digunakan sebagai dataset evaluasi akurasi.

InsightFace memanggil SimilarityTransform.estimate yang menimbulkan FutureWarning deprecation pada scikit-image terpasang. Runtime saat ini berfungsi dan terkunci; tidak mengubah paket upstream/menyembunyikan warning. Kompatibilitas perlu diuji sebelum upgrade dependensi.

## Uji mandiri Tahap 7

Tutup aplikasi/preview kamera lain. Jalankan alat uji dari folder proyek:

```sh
.venv/bin/python scripts/demo_ai.py
```

Alat ini terpisah dari aplikasi kerja, tidak membutuhkan login/database, tidak mendaftarkan anggota atau membuat absensi. Menu anggota di aplikasi kerja belum dapat menyelesaikan registrasi sebelum Tahap 8. Tidak perlu reset database atau mengunduh model lagi jika berkas Tahap 1 masih tersedia.

1. Sebelum mencentang persetujuan, kamera belum terbuka dan tombol Mulai tidak aktif. Centang hanya bila seluruh peserta mengizinkan pemrosesan sementara.
2. Pilih nomor kamera 0/1 yang benar, lalu **Mulai pemeriksaan**. Tunggu model siap; cold loading dilaporkan terpisah dari waktu pemeriksaan.
3. Hadapkan satu wajah ke kamera. Pastikan seluruh wajah berada di tengah kotak/frame, tidak terlalu dekat, fokus tajam dan cahaya merata. Kotak/titik kuning adalah petunjuk terakhir, bukan bukti identitas. Status terpotong/kecil/blur/cahaya/multiple_faces harus diperbaiki sebelum mengambil referensi.
4. Dengan wajah asli yang layak, hasil seharusnya **Wajah lolos pemeriksaan awal**, skor live memenuhi 0,85 dan kelas live. Jika ditolak berulang, catat skor/kondisi; jangan menurunkan threshold untuk menyatakan lulus.
5. Klik **Ambil referensi sementara** saat wajah lolos. Tunggu tulisan referensi tersedia; bandingkan frame berikutnya dengan sedikit variasi posisi, bukan frame yang sama. Hasil diharapkan cocok pada similarity >=0,60. Referensi bukan identitas anggota dan hanya hidup selama proses ini.
6. Dengan izin peserta lain, ganti orang di depan kamera: diharapkan **Tidak cocok**, atau ditolak quality/liveness. Penolakan quality/liveness saja bukan bukti unknown identity berhasil diuji. Catat bila orang lain justru cocok.
7. Klik **Hapus referensi**, lalu pastikan perbandingan lama berhenti sebelum mengambil referensi orang lain. **Hentikan dan hapus referensi** atau tutup alat juga membuang referensi. Restart harus dimulai tanpa referensi.
8. Untuk setiap kategori **Foto cetak / Foto pada layar / Replay video**, tampilkan melalui kamera sehingga wajah memenuhi kualitas/ukuran seperti wajah asli. **Hasil yang diharapkan adalah ditolak anti-spoof.** No face/blur/terpotong dicatat sebagai uji tidak valid untuk penerimaan anti-spoof, bukan otomatis lulus.
9. Pilih kondisi yang sesuai, lalu **Catat hasil terakhir (angka saja)** satu kali per percobaan independen. Ini ringkasan di memori, hilang saat alat ditutup; tidak menulis foto, embedding, landmark atau nama orang. Catat ringkasan/hasil secara manual tanpa membagikan wajah peserta. Jangan memakai frame berulang dari satu percobaan untuk membesarkan jumlah sampel.
10. Coba tidak ada wajah, dua wajah, cahaya kurang, wajah terlalu kecil dan menutup alat ketika sedang memeriksa: UI tetap merespons, status aman, kamera/proses dilepas. Mencabut USB harus menghentikan kamera, bukan beralih ke laptop; periksa nomor sebelum mulai manual.

Checklist pelaporan sederhana:

| Kondisi | Jumlah percobaan valid | Lolos/ditolak | Skor/rentang | Catatan |
|---|---:|---|---|---|
| Wajah asli | | | | |
| Referensi sama, probe baru | | | | |
| Orang berbeda, probe valid | | | | |
| Foto cetak | | | | |
| Foto layar | | | | |
| Video replay | | | | |

Keberhasilan pilot kecil ini belum membuktikan target accuracy >98% atau spoof rejection >=95%; keduanya memerlukan protokol Tahap 15. Gagal menolak serangan valid adalah temuan yang harus diperbaiki/dievaluasi sebelum gerbang Tahap 7 lulus.

Pengujian otomatis:

```sh
STARGATE_TEST_NATIVE_KEYCHAIN=1 .venv/bin/python -m pytest --run-db --run-models --cov=app --cov=database --cov=ai --cov-fail-under=80
```

Pengujian kamera opsional menyimpan angka diagnostik saja di .local (bukan foto/embedding):

```sh
.venv/bin/python scripts/check_ai.py --camera-index 0 --samples 8
```

Pengujian kamera singkat itu tidak menggantikan percobaan wajah asli/foto cetak/replay di atas. Retensi enrollment/operasional harus ditetapkan sebelum data nyata disimpan pada Tahap 8.

## Review pengguna

Pengguna menyatakan sudah mereview dan hasil OK lalu mengizinkan Tahap 8. Review diterima sebagai persetujuan pengguna; rincian skor/jumlah per kategori tidak dikirim sehingga tidak dibuat-buat pada bukti. Target statistik dan hasil holdout tetap Tahap 15. Izin penyimpanan nyata diberikan terpisah pada Tahap 8, dengan kebijakan retensi di ../biometric-retention.md.
