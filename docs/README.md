# Dokumentasi pembangunan StarGate

Mulai dari [PLAN](../PLAN.md), lalu baca:

1. [Keputusan kebutuhan dan arsitektur](decisions.md): ketentuan PDF, keputusan pengguna dan usulan yang belum final.
2. [Matriks kebutuhan](requirements-traceability.md): 31 user story dan kebutuhan tambahan PRD, tahap serta ID test.
3. [Katalog test](testing/test-catalog.md): skenario positif/negatif/batas/gangguan.
4. [Strategi penerimaan](testing/acceptance-strategy.md): lapisan uji, SLA, bukti dan gerbang.
5. [Data uji](testing/test-data.md): fixture administratif dan prosedur sampel nyata.
6. [Hasil Tahap 0](testing/stage-00.md): hasil pemeriksaan dan pekerjaan tertunda.
7. [Bug dan isu](bugs.md): defect runtime dipisahkan dari gap spesifikasi.
8. [Arsitektur fondasi](architecture.md) dan [hasil Tahap 2](testing/stage-02.md).
9. [Database](database.md) dan [hasil Tahap 3](testing/stage-03.md).
10. [Login, session, role dan uji mandiri Tahap 4](testing/stage-04.md).
11. [Grup, shift, anggota dan demo uji mandiri Tahap 5](testing/stage-05.md).

12. [Perangkat, kamera dan uji mandiri Tahap 6](testing/stage-06.md).

13. [Engine AI dan uji mandiri Tahap 7](testing/stage-07.md).

14. [Registrasi lima sudut dan registrasi ulang Tahap 8](testing/stage-08.md).
15. [Retensi biometrik dan dasar sumber resmi](biometric-retention.md).

16. [Pengaturan dan konfigurasi aktif Tahap 9](testing/stage-09.md).

17. [Absensi wajah dan aturan shift Tahap 10](testing/stage-10.md).

18. [Template checklist tes mandiri Tahap 10](testing/stage-10-manual-template.md).

19. [Aplikasi demo dan pengujian otomatis Tahap 10](testing/stage-10-demo.md).

20. [Dashboard, demo cepat dan uji mandiri Tahap 11](testing/stage-11.md).

21. [Laporan, demo Viewer dan ekspor Excel/PDF Tahap 12](testing/stage-12.md).

## Status saat ini

Tahap 0–11 sudah direview pengguna pada cakupan tersedia; RTSP positif tetap tertunda. Tahap 12 tersedia dengan laporan/filter, ekspor snapshot seluruh halaman dan demo Viewer; 399 regresi PASS, 13 ekspor final dan 65 native PASS. [Laporan Tahap 12](testing/stage-12.md) memuat demo, batas dan bukti termasuk cakupan coverage. Menunggu review pengguna; Tahap 13 belum dimulai.

Dokumentasi library dicari melalui MCP Context7; jika katalog tidak memuat library yang dimaksud, gunakan sumber resmi dan catat fallback. Jangan mengirim data pribadi/rahasia ke query dokumentasi.


22. [Audit, cadangan dan pemulihan Tahap 13](testing/stage-13.md) — kebijakan 7 hari/registrasi ulang, demo dan prosedur pengujian.

23. [Persiapan/UAT Tahap14](testing/stage-14.md) dan [Instalasi Windows/Parallels](windows-install.md) — build native, data privat, PostgreSQL, upgrade dan pemulihan.
