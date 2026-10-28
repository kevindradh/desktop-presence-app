# Tahap 16: dokumentasi dan penyerahan kandidat

28 Oktober 2026. Dokumentasi dan prosedur paket disiapkan sambil menuntaskan pengujian Tahap15. Gerbang Tahap15 belum dianggap lulus hanya karena berkas penyerahan tersedia.

## Dokumen operasional

- [Panduan operasi](../operations.md): akun/peran, administrasi, lima sudut, penugasan, kamera, absensi, laporan, cadangan dan masalah umum.
- [Instalasi otomatis Windows](stage-14-auto-manual.md), [cara build](../windows-install.md), serta [konfigurasi eksternal](../windows11-amd-setup.md).
- [Arsitektur](../architecture.md), [database dan ERD](../database.md), [keputusan produk](../decisions.md), [retensi](../biometric-retention.md).
- [Hasil pengujian dan SLA](stage-15.md), [peta31user story](stage-15-acceptance-map.md), [daftar defect](../bugs.md).
- [Catatan kandidat dan pemulihan](../release-candidate.md), [notice dependency/model](../../packaging/THIRD_PARTY_NOTICES.md).

## Pemeriksaan DoD dua PDF

Kedua PDF asli dibaca ulang: *StarGate - Face Recognition Attendance System* dan *StarGate - User Stories dan Acceptance Criteria*. DoD berada pada bagian akhir dokumen user story; target performa/reliabilitas dan MVP berada pada PRD. Hasil ekstraksi tidak dipakai untuk menilai layout dokumen baru.

| Ketentuan | Bukti/status saat peninjauan |
|---|---|
| User story diimplementasikan | Seluruh31dipetakan ke modul dan tes; sebagian UAT nyata masih terbuka |
| Semua acceptance criteria lulus | Belum seluruhnya; lihat peta penerimaan dan kasus perangkat/serangan nyata |
| Unit test coverage≥80% | Gabungan89,73%; subset tanpa database/model43,56% (masih mencakup UI/native credential). Unit murni≥80% belum terbukti |
| Integration test lulus | Regresi akhir538PASS/1SKIP;610,67detik; tes paket terpisah5PASS |
| Tidak ada Critical/Open | PERF-B001 tetap OPEN (3query>100ms); CAM-B004 OPEN (gagal pertama, ulang lulus), penyebab belum terisolasi |
| Audit aktif dan izin diterapkan | Regresi service/UI dan pemeriksaan database tersedia |
| Dokumentasi diperbarui | Panduan operasi/arsitektur/ERD/pemulihan dan notice diperbarui |
| Performance memenuhi SLA | Pencarian diuji; startup/deteksi/recognition/save/end-to-end belum seluruhnya tersertifikasi |
| Accuracy≥98%, spoof≥95% | Belum ada catatan uji peserta/serangan nyata menurut jawaban pengguna |
| Availability99,5% | Periode pengamatan belum tersedia; tidak dihitung dari smoke test |
| Siap UAT dan penerimaan V1 | Kandidat untuk UAT internal; penerimaan penuh belum dicatat |

## Prosedur paket

`scripts/prepare_research_release.py` memeriksa ukuran/hash installer, memilih source melalui allowlist, menolak source privat/tautan, menambahkan dokumen yang ditentukan, lalu membuat manifest, archive dan sidecar SHA256. Source kit tidak berisi bobot pretrained atau lingkungan Python. Runtime binary tetap membawa notice/lisensi yang telah diperiksa saat build.

Paket akhir belum dinyatakan siap sebelum identitasnya cocok dengan hasil build dan pemeriksaan Windows. Arsip tidak diunggah otomatis. Keputusan lisensi untuk distribusi eksternal dan penerimaan produksi tidak digantikan oleh pembuatan arsip.

## Pengujian penutup yang masih diperlukan

Catatan peserta perlu memisahkan probe asli, identitas salah, penolakan wajah asli dan penerimaan orang yang tidak terdaftar. Uji spoof perlu memisahkan foto cetak, foto layar dan video replay serta jumlah yang ditolak/diterima. Catatan availability harus menyebut jam layanan, periode observasi dan downtime aktual. Gunakan protokol pada [strategi penerimaan](acceptance-strategy.md); jangan membuat data seolah pengujian telah berlangsung.

## Pemeriksaan dokumen

- PASS: peran dibandingkan dengan matriks `PERMISSIONS` aktual.
- PASS: ERD dibandingkan dengan foreign key ORM.
- PASS: batas retensi/cadangan mengikuti keputusan pengguna, tanpa angka retensi hukum baru.
- PASS: kandidat, hasil uji dan gerbang penerimaan dipisahkan; tidak menandai metrik yang belum tersedia sebagai lulus.

Uji regresi alat paket:16PASS/1SKIP pada [JUnit packaging](evidence/stage-16-packaging-regression.xml). SKIP adalah uji model yang tidak diaktifkan pada run alat ini; uji model nyata telah berjalan pada regresi aplikasi538PASS/1SKIP. Angka tersebut tidak dijumlahkan sebagai kasus unik.

Arsip penyerahan menyertakan bukti teks/JSON/XML akhir dan baseline pencarian yang dipilih secara eksplisit. Bukti historis lain yang ditautkan pada catatan lama tetap tersedia di checkout proyek; arsip tidak menyalin seluruh galeri screenshot lama.

Identitas installer akhir0.14.2, pemeriksaan model/schema/data, seluruh latency dan kedua percobaan kamera tersedia pada [bukti akhir Windows](evidence/stage-15-final-windows/). Tidak ada klaim seluruh defect ditutup. [Daftar gerbang penerimaan](remaining-acceptance.md) menjadi daftar lanjut sesudah kandidat disiapkan.

## Arsip kandidat terverifikasi

`dist/releases/StarGate-Research-Windows-x64-0.14.2.zip` selesai dibuat:484.687.661byte, SHA256 `608a00129a57045875ecd6f6e6e0a576685df53f1e7bad45e8b7497cb13223c3`. Pemeriksaan membuka arsip dan source kit, memverifikasi seluruh89berkas release dan217source terhadap manifest, serta memeriksa bahwa source tidak membawa bobot pretrained, `.env`, galeri, database, log, backup atau virtual environment. Sidecar `.zip.sha256` tersedia. [Bukti verifikasi](evidence/stage-16-release.json) mencatat hash snapshot PLAN yang dikemas sebelum checklist hasil arsip ini diperbarui.

Paket ini adalah penyerahan kandidat internal. Penerimaan V1 tetap terbuka, termasuk coverage unit, PERF-B001, CAM-B004 dan pengujian nyata/perangkat/SLA yang belum tersedia. Tidak mengunggah atau menerbitkan arsip ke layanan eksternal.
