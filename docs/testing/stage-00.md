# Hasil Tahap 0 - Kebutuhan dan skenario uji

Tanggal: 18 Oktober 2026 (Asia/Jakarta). Status: **Lulus**. Pengguna menyetujui review dan menginstruksikan lanjut pada 18 Oktober 2026. Detail yang belum ditentukan tetap mengikuti batas tahap di decisions.md.

## Lingkungan dan pekerjaan aktual

- Proyek awal berisi dua PDF dan PLAN.md; belum ada kode aplikasi atau repository Git teramati.
- Host: Darwin arm64, Python sistem 3.14.8. Tidak ada pemasangan, pemanggilan kamera, pengunduhan model, atau perubahan DB.
- Seluruh halaman sumber dibaca ulang melalui ekstraksi teks. Tabel hak akses PRD h.10 telah diperiksa secara visual pada pembacaan sebelumnya; tanda izin tidak tersedia pada ekstraksi teks biasa.
- MCP Context7 digunakan untuk dukungan ORM pgvector; library `/pgvector/pgvector-python`; bukti sumber dirujuk pada decisions.md.

## Checklist hasil

- [x] Matriks 31 user stories dan 28 kelompok kebutuhan PRD/DoD dibuat.
- [x] 59 kelompok test dengan kasus positif, negatif, batas dan gangguan dibuat.
- [x] 23 keputusan/ketentuan diidentifikasi; status usulan dipisahkan dari keputusan pengguna.
- [x] Pengguna menetapkan macOS untuk development, Windows untuk distribusi.
- [x] Pengguna menetapkan PostgreSQL lokal satu komputer dahulu.
- [x] Spesifikasi fixture sintetis, empat akun role dan prosedur sampel wajah disiapkan.
- [x] Strategi pengukuran SLA, coverage, UAT dan bug disiapkan sebagai usulan.
- [x] Dokumen keputusan, matriks, testing, bug, index dan PLAN diperbarui.
- [ ] Pilihan versi/dependensi/model dan rincian perangkat siap diverifikasi pada instalasi.
- [x] Usulan terdefinisi ditinjau dan diterima sebagai baseline; retensi/persetujuan data wajah tetap ditentukan sebelum penggunaan data nyata.
- [x] Pengguna meninjau hasil Tahap 0 dan menyatakan dapat lanjut ke Tahap 1.

## Pemeriksaan dokumen

| ID | Langkah dan expected | Hasil aktual | Hasil |
|---|---|---|---|
| DOC-01 | Bandingkan US-001..031 dengan baris matriks; semua unik dan lengkap | 31 ID tersedia, tidak ada yang hilang atau duplikat | PASS |
| DOC-02 | Setiap kebutuhan memiliki ID test dan tahap | 59 baris kebutuhan dipetakan satu-ke-satu ke 59 kelompok test | PASS |
| DOC-03 | Referensi D-* pada matriks/katalog terdefinisi | Referensi sesuai daftar 23 keputusan | PASS |
| DOC-04 | Tautan lokal menuju berkas yang ada | Pemeriksaan awal menemukan stage-00.md belum dibuat; laporan ini dibuat lalu tautan diperiksa ulang | PASS setelah perbaikan |
| DOC-05 | Fence Markdown seimbang pada seluruh dokumen | Pemeriksaan struktur lulus | PASS |
| DOC-06 | Review isi terhadap sumber termasuk konflik | AC seluruh US dipetakan; gap PRD dicatat pada SPEC-001..009 dan D-01..23; keputusan yang belum final tetap terbuka | PASS untuk pencatatan; penerimaan keputusan pending |
| DOC-07 | Konfirmasi target OS dan DB langsung dari pengguna | macOS development, Windows distribution, PostgreSQL lokal satu komputer | PASS |
| DOC-08 | Persetujuan kebutuhan/usulan dan penutupan tahap | Pengguna menyetujui dan memberi instruksi lanjut | PASS |

Pemeriksaan struktur memakai skrip Python sekali jalan yang membaca Markdown tanpa mengubah data produk. Ini bukan unit test aplikasi dan tidak menghasilkan klaim coverage.

## Batas hasil

Seluruh TC-US-* dan TC-PRD-* tetap NOT RUN. Tidak ada benchmark, login, kamera, liveness, koneksi PostgreSQL, packaging Windows atau pengujian aplikasi yang sudah lulus. Desain sampel bukan pengumpulan data; akun fixture belum dibuat.

## Langkah berikutnya

Tinjau usulan pada decisions.md, terutama aturan scan/cooldown, hak Users, statistik izin/jadwal dan interpretasi SLA. Setelah keputusan dasar/pemilihan teknis siap serta gerbang tahap diterima, jalankan Tahap 1 dan catat smoke test di stage-01.md. Keputusan fitur berikutnya dapat diselesaikan sebelum tahap terkait sesuai batas di daftar keputusan; jangan membiarkannya terlewat.

Persetujuan penutupan: pengguna, 18 Oktober 2026, “sudah saya review dan sudah OK, bisa dilanjutkan”. Tahap 1 diizinkan dimulai; tidak ada persetujuan pengumpulan dataset wajah yang disimpulkan dari review ini.
