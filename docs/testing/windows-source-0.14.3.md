# Pengujian paket source Windows0.14.3

28 Oktober2026. Paket source siap setup dibuat dari kode proyek,75wheel WindowsCPython3.11x64 dengan hash sesuai lock, runtime PostgreSQL17/pgvector0.8.7 terverifikasi, serta aset model sesuai manifest. Python dan Visual C++ Runtime merupakan prasyarat eksternal; tidak ada executable aplikasi StarGate di paket. Entry aplikasi adalah `main.py`.

Paket: `dist/StarGate-Source-Windows-x64-0.14.3.zip`,605.743.625byte. SHA256 `8a1dcbc2afd83e124e984195be255de8b9eebc10beefc0c3ecf05ac0e5d32141`. Terdapat231berkas source dan1.692berkas pendukung. [Metadata](evidence/windows-source-0.14.3/artifact.json).

## Hasil aktual

- PASS: SHA256 arsip, CRC seluruh isi ZIP, entry `main.py`/duaCMD, serta pemeriksaan bahwa `.env`, database, foto anggota, embedding, log dan environment Python tidak ikut dikemas.
- PASS: ekstraksi pada folder source baru tanpa `.venv-win` dan tanpa profil data uji sebelumnya.
- PASS: SETUP-WINDOWS.cmd membuat venv baru, memasang wheel dengan `--no-index --require-hashes --only-binary`, serta pip check tanpa konflik.
- PASS: database lokal baru dibuat pada profil uji terpisah; schema14tabel aplikasi valid di revision `0006_search_storage`. Users/member/attendance/embedding masing-masing0; pengguna membuat Super Admin sendiri.
- PASS: source `main.py --package-check --verify-models` memeriksa Qt/plugin/native/spawn dan worker AI memakai frame kosong. Kamera tidak dibuka, wajah nyata tidak dipakai.
- PASS: setup ulang pada profil uji yang sama selesai tanpa `fresh`.
- PASS: cluster sumber uji dihentikan setelah pengujian. Aplikasi/data installer yang ada tidak direset.
- PASS:4tes pemeriksaan manifest untuk berkas model/lisensi, perubahan model, file runtime tambahan dan path keluar folder. Regresi alat paket16PASS/1SKIP terpisah; SKIP model pada suite tersebut ditopang probe source Windows di atas.

Pengujian memakai Windows11 ARM64 Parallels dengan CPython3.11.17 x64. Komputer AMD fisik belum diuji. Tidak mematikan jaringan Windows secara keseluruhan; pemasangan library dipaksa dari wheelhouse lokal melalui flag pip dan log menunjukkan berkas lokal. Tidak mengklaim akurasi biometrik/SLA atau seluruh UI manual lulus dari pemeriksaan setup.

Bukti: [schema dan hitungan](evidence/windows-source-0.14.3/source-check.json), [setup](evidence/windows-source-0.14.3/setup.log.tail.txt), [setup ulang](evidence/windows-source-0.14.3/repeat.log.tail.txt).

## Perbaikan saat pengujian

Preflight pertama berhenti sebelum membuat venv/database: dua aset deklaratif, `third_party/minifasnet/LICENSE` dan `MiniFASNet.py`, sudah di-hash tetapi belum dihitung dalam himpunan berkas pendukung karena berada di luar tiga folder binary. Pemeriksaan diperbaiki untuk turut menghitung aset deklaratif tersebut; verifikasi hash seluruh aset dipertahankan. Arsip percobaan pertama disimpan terpisah dan tidak menjadi paket unduhan final. Pengujian diulang sebelum venv/data dibuat dan berhasil. Tidak menghapus pengaman untuk meloloskan paket.

[Petunjuk pemasangan laptop](../windows-source-setup.md). Berkas tersebut juga disertakan sebagai `SOURCE-README.md` di dalam paket, dengan referensi notice relatif terhadap root paket. Python3.11x64 serta Visual C++ Runtime resmi dipasang terlebih dahulu; setelah itu gunakan SETUP-WINDOWS.cmd dan RUN-WINDOWS.cmd.
