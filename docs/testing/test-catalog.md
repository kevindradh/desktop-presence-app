# Katalog skenario penerimaan

Tanggal: 18 Oktober 2026. Ini desain dan status ringkas pengujian; bukti hasil aktual ada pada laporan setiap tahap.

## Cara menjalankan

Setiap TC adalah kelompok skenario. Saat implementasi, pecah menjadi kasus bernomor (misalnya TC-US-001-01), tulis prasyarat, langkah, input, expected, actual, bukti, lalu PASS/FAIL. Ulangi matriks role untuk aksi yang dilindungi. Kasus tergantung D-* tetap bersyarat sampai keputusan disetujui.

| ID test | Skenario positif, negatif, batas, dan gangguan | Oracle / acuan expected | Tahap | Status |
|---|---|---|---|---|
| TC-US-001 | Login benar; password salah; username asing; field kosong; audit; tidak ada session pada penolakan | US-001; D-16 | 4 | NOT RUN |
| TC-US-002 | Matriks seluruh role; akses langsung service; navigasi dan mutasi tanpa izin | US-002; D-09,D-10 | 4 | NOT RUN |
| TC-US-003 | Valid; tiap field wajib kosong; kamera/DB gagal; rollback; Operator dapat registrasi | US-003; D-14 | 8 | NOT RUN |
| TC-US-004 | Lima sudut; hanya empat; sudut terulang; cancel; banyak wajah; sampel tidak layak | US-004; D-14,D-23 | 8 | NOT RUN |
| TC-US-005 | Data kosong; lebih dari satu halaman; pencarian nama/ID; tidak ada hasil; filter | US-005; — | 5 | PASS |
| TC-US-006 | Edit valid; field wajib dihapus; ID duplikat; cancel; restart | US-006; D-14 | 5 | PASS |
| TC-US-007 | Konfirmasi/cancel; riwayat tetap; member nonaktif ditolak engine; audit | US-007; D-14 | 5/10 | NOT RUN |
| TC-US-008 | Wajah asli; gagal transaksi tanpa sukses; state shift; audit; tepat satu event | US-008; D-07,D-08 | 10 | NOT RUN |
| TC-US-009 | Foto cetak; foto layar; video layar; beberapa kamera/cahaya; verifikasi DB tidak bertambah | US-009; D-05,D-19 | 7/10 | NOT RUN |
| TC-US-010 | Identitas holdout; skor di bawah threshold; member nonaktif; jumlah row tetap | US-010; D-19 | 10 | NOT RUN |
| TC-US-011 | 59.999/60/60.001 detik; dua kamera bersamaan; perubahan setting; lintas terminal | US-011; D-07 | 10 | NOT RUN |
| TC-US-012 | Checkout sah; sebelum IN; dalam cooldown; sesudah OUT; shift malam | US-012; D-07,D-08 | 10 | NOT RUN |
| TC-US-013 | Bandingkan orang vs event; izin; libur; pergantian tanggal; member aktif/nonaktif | US-013; D-10,D-13 | 11 | NOT RUN |
| TC-US-014 | Commit event; rollback tidak menambah feed; feed saat halaman dibuka kembali | US-014; D-03 | 11 | NOT RUN |
| TC-US-015 | Valid; nama kosong; duplikat sesuai aturan; role ditolak | US-015; D-10,D-14 | 5 | PASS |
| TC-US-016 | Assign/reassign; group tidak ada; riwayat laporan; rollback | US-016; D-14 | 5 | PASS |
| TC-US-017 | Internal/USB nyata; permission ditolak; perangkat tidak ada; reconnect | US-017; D-02 | 6 | NOT RUN |
| TC-US-018 | Valid; URL salah; auth salah; putus stream; timeout; log tanpa password | US-018; D-02,D-17 | 6 | NOT RUN |
| TC-US-019 | Pagi; malam lintas tanggal; grace tidak valid; penugasan bertanggal | US-019; D-11,D-12 | 5 | PASS |
| TC-US-020 | 08:05; 08:10; 08:10:00.001; 08:11; zona waktu; shift malam | US-020; D-11,D-12 | 10 | NOT RUN |
| TC-US-021 | Tanggal berisi/kosong; awal/akhir hari; tanggal kerja malam; data sumber cocok | US-021; D-11,D-15 | 12 | NOT RUN |
| TC-US-022 | Group A/B; kombinasi filter; group dipindah; reset filter | US-022; D-15 | 12 | NOT RUN |
| TC-US-023 | Lebih satu halaman; tipe tanggal; Unicode; total/row cocok; tujuan tidak bisa ditulis | US-023; D-15 | 12 | NOT RUN |
| TC-US-024 | Buka/render; filter dan nilai benar; tabel panjang; page break; file kosong/tujuan gagal | US-024; D-15 | 12 | NOT RUN |
| TC-US-025 | Role yang diizinkan; username duplikat; field kosong; hash; akun baru login | US-025; D-09,D-16 | 4 | NOT RUN |
| TC-US-026 | Password lama ditolak; sementara valid; audit tanpa rahasia; izin service | US-026; D-09,D-16 | 4 | NOT RUN |
| TC-US-027 | Ubah .60 ke .65; input invalid; restart; skor terkendali yang berbeda hasilnya | US-027; D-19 | 9 | NOT RUN |
| TC-US-028 | Off ke on; asli/serangan; model gagal tanpa bypass; perubahan worker aktif | US-028; D-19 | 9 | NOT RUN |
| TC-US-029 | Actor/waktu/target; event PRD tambahan; aksi gagal; akses audit; rahasia tersanitasi | US-029; D-10,D-17 | 3/4/9/10/13 | PASS teknis Tahap 13; review pengguna tertunda |
| TC-US-030 | Valid; hak akses; DB gagal; ruang/path tidak dapat ditulis; manifest | US-030; D-18 | 13 | PASS teknis Tahap 13; review pengguna tertunda |
| TC-US-031 | Restore DB uji; bandingkan seluruh tabel/aset; file rusak; versi salah; proses terputus | US-031; D-18 | 13 | PASS teknis Tahap 13; review pengguna tertunda |
| TC-PRD-AUTH | Restart/session/token; password lama ditolak; 5 kegagalan dan batas waktu usulan; hash bukan plaintext | PRD-AUTH; D-16 | 4 | NOT RUN |
| TC-PRD-ROLE | Matriks UI + service, bukan hanya menu; group/shift/device/audit dipetakan | PRD-ROLE; D-09,D-10 | 4 | NOT RUN |
| TC-PRD-DASH | Fixture orang aktif/jadwal/izin; agregasi silang; grafik kosong | PRD-DASH; D-13 | 11 | NOT RUN |
| TC-PRD-MEMBER | Validasi tiap field; history utuh setelah soft delete; set lama tetap jika registrasi ulang gagal | PRD-MEMBER; D-14 | 5/8/10 | NOT RUN |
| TC-PRD-GROUP | Dua group; edit; delete ditolak bila dipakai; assign/reassign | PRD-GROUP; D-14 | 5 | PASS |
| TC-PRD-DEVICE | Setiap tipe nyata; dua stream; putus; buka/tutup; antrean terbatas | PRD-DEVICE; D-02,D-23 | 6 | NOT RUN |
| TC-PRD-EVENT | State transition table; race dua kamera; rollback; suara hanya setelah commit | PRD-EVENT; D-07,D-08 | 10 | NOT RUN |
| TC-PRD-SHIFT | Tanggal kerja malam; jam sama; OUT dini; batas grace | PRD-SHIFT; D-11,D-12 | 5/10 | NOT RUN |
| TC-PRD-REPORT | Setiap filter + kombinasi; rentang terbalik; data kosong; multi-page | PRD-REPORT; D-15 | 12 | NOT RUN |
| TC-PRD-USER | Create/read/edit/deactivate sesuai kebijakan; duplikat; last admin terlindung | PRD-USER; D-09,D-16 | 4 | NOT RUN |
| TC-PRD-CONFIG | Seed baru; nilai invalid; persistensi; konfigurasi diterapkan pada worker | PRD-CONFIG; D-19 | 9 | NOT RUN |
| TC-PRD-SCHEMA | Checklist kolom/tipe/relasi; migrasi kosong; CRUD repository; vector(512) | PRD-SCHEMA; D-11,D-13,D-14 | 3 | PASS |
| TC-PRD-ARCH | Inspeksi struktur dan dependensi; jalur data nyata; tidak mengganti stack | PRD-ARCH; D-01,D-05 | 2/3/7 | NOT RUN |
| TC-PRD-AUDIT | Cocokkan setiap event dan actor dengan transaksi sumber; log rahasia tidak bocor | PRD-AUDIT; D-17 | 3/4/9/10/13 | NOT RUN |
| TC-PRD-QUERY | Review repository; input berkarakter SQL tidak mengubah query; DDL hanya provisioning | PRD-QUERY; D-06 | 3 | PASS |
| TC-PRD-LOCATION | Identitas terminal/lokasi dan batas deployment diuji setelah definisi final | PRD-LOCATION; D-03,D-22 | 3/6/15 | NOT RUN |
| TC-PRD-OVERTIME | Review definisi durasi/rekap lembur sebelum menentukan AC tambahan | PRD-OVERTIME; D-22 | 5/10/12 | NOT RUN |
| TC-PRD-DETECT | Timer khusus tahap, model hangat/dingin dilaporkan; hardware tetap | PRD-DETECT; D-20 | 7/15 | NOT RUN |
| TC-PRD-RECOGNIZE | Definisikan cakupan timer embedding/pencarian; p50/p95/max dilaporkan | PRD-RECOGNIZE; D-20 | 7/15 | NOT RUN |
| TC-PRD-SAVE | Timer transaksi DB sampai commit; uji beban dan error | PRD-SAVE; D-20 | 10/15 | NOT RUN |
| TC-PRD-STARTUP | Proses diluncurkan sampai UI/engine siap; warm dan cold terpisah | PRD-STARTUP; D-20 | 14/15 | NOT RUN |
| TC-PRD-SPEED | Timer frame wajah layak sampai commit/feedback; distribusi hasil; dua batas dilaporkan | PRD-SPEED; D-20,D-21 | 15 | NOT RUN |
| TC-PRD-ACCURACY | Dataset enrollment/probe dipisah; genuine/unknown; confusion counts; FAR/FRR | PRD-ACCURACY; D-20,D-21 | 15 | NOT RUN |
| TC-PRD-LIVENESS | Foto/video per kamera/cahaya; attack rejection dan bona fide rejection terpisah | PRD-LIVENESS; D-05,D-20 | 7/15 | NOT RUN |
| TC-PRD-SEARCH | 50.000 embedding minimal bila 5 per member; exact baseline sebelum indeks approximate | PRD-SEARCH; D-14,D-20 | 3/7/15 | NOT RUN |
| TC-PRD-AVAILABILITY | Periode observasi; uptime terukur/durasi jadwal; planned/unplanned downtime eksplisit | PRD-AVAILABILITY; D-20 | 15 | NOT RUN |
| TC-PRD-DONE | Review seluruh bukti; bug terbuka; coverage report; UAT sign-off | PRD-DONE; D-20 | 15/16 | NOT RUN |
| TC-PRD-SCOPE | Review perubahan scope dan paket rilis | PRD-SCOPE; D-01,D-22 | 0/16 | NOT RUN |

## Gangguan yang diuji lintas modul

- DB terputus sebelum/saat commit: tidak ada data parsial, feedback sukses palsu, atau retry yang menggandakan event.
- Worker error/timeout dan penutupan aplikasi: sumber daya dilepas, UI tetap merespons, log dapat ditelusuri.
- Kamera permission ditolak/terlepas/RTSP putus: pesan jelas dan recovery terbatas; tidak menyimpan frame lama sebagai scan baru.
- Folder tidak dapat ditulis/file ekspor dibatalkan/backup rusak: error aman dan data sumber tetap konsisten.
- Perubahan tanggal/shift/zona waktu dan scan bersamaan: event terasosiasi dengan sesi yang tepat.
- Upgrade/migrasi gagal: gunakan DB uji dan bukti backup/restore; jangan menguji kegagalan pada database produksi.

Bukti SCHEMA/QUERY: [laporan Tahap 3](stage-03.md). User stories lengkap dan integrasi UI tetap belum lulus hanya dari pengujian repository.

Bukti Tahap 5: [laporan administrasi](stage-05.md). US-007/PRD-MEMBER/PRD-SHIFT masih belum PASS penuh: soft delete/riwayat tersimpan dan jadwal administratif diuji Tahap 5; registrasi wajah serta pengenalan/nonaktif/early leave end-to-end tetap Tahap 8/10.

Bukti Tahap 9: [laporan konfigurasi](stage-09.md), `tests/test_settings.py` dan `tests/test_settings_ui.py`. Mencakup persistensi/restart, .65 pada query nyata, liveness aktif/nonaktif/batas kelas, input invalid tanpa perubahan parsial, audit lama/baru/no-op, rollback, dua simpan bersamaan, stale form, penolakan role dan fokus saat session polling. US-028 attendance end-to-end tetap Tahap 10.

Bukti Tahap 10: [laporan absensi](stage-10.md), `tests/test_attendance.py` dan `tests/test_attendance_ui.py`. Tes mencakup 08:05/08:10/08:11, <60/=60/>60 detik, IN/OUT/BREAK, dua terminal dan dua kamera pada wajah yang sama, penahan continuous face lintas kamera, fresh policy dan expiry saat query/write, rollback audit, hari libur/izin, inactive/unknown/spoof, shift malam dan auto checkout catch-up/idempotensi. Model worker nyata menolak blank frame tanpa menambah attendance. UAT kamera/foto/video/audio dan benchmark belum dinyatakan PASS.

Bukti Tahap 11: [dashboard](stage-11.md), `tests/test_dashboard.py` dan `tests/test_dashboard_ui.py`. TC-US-013 mencakup statistik orang unik, late subset, akhir shift/izin/kalender, anggota aktif tanpa jadwal, konflik penugasan, IN historis setelah nonaktif, dua sesi tanpa menggandakan orang, grup historis, person-days bulanan, no data, future/rollback dan feed bounded. TC-US-014 mencakup commit dari AuthService/AttendanceService terminal lain tanpa refresh, fokus tanggal, filter berubah saat pemuatan, pergantian hari, error/recovery, revoke, navigation/logout/close saat worker aktif, camera stream/heartbeat serta demo lima anggota.

Bukti Tahap 12: [laporan dan ekspor](stage-12.md), `tests/test_reports.py`, `tests/test_report_exports.py`, `tests/test_reports_ui.py`. TC-US-021/022 menguji periode inklusif/preset, filter grup/anggota/shift/status, lima status, freeze hasil setelah commit baru, binding/expiry, shift malam dan inactive/historical group. TC-US-023/024 mencocokkan XLSX/PDF dengan snapshot, ekspor halaman kedua ke seluruh 65 baris, Unicode/nama panjang, typed dates/teks literal, no data, PDF banyak halaman/header/footer/ID lengkap dan baris tidak terpotong tanpa identitas. Pembatalan, write failure, expired/revoked, file lama, folder gagal, publication race serta fokus/logout/close diuji. Render workbook/PDF dan native ditinjau terpisah; tidak menggantikan uji Windows.

Bukti Tahap 13: [audit, backup dan restore](stage-13.md), tests/test_audit.py, tests/test_backup_codec.py, tests/test_backups.py dan tests/test_backups_ui.py. Uji schema test terpisah mencakup autentikasi/role, seluruh tabel/identity, foto/hash, enkripsi, password, expiry, versi, archive data-only, perubahan file setelah inspeksi, rollback constraint/cancel/crash, cadangan pengaman, lock lintas penulis, sesi dicabut dan registrasi ulang yang disengaja.

Tahap14: tests/test_packaging.py menguji pemisahan resource/data/config, path model, penolakan cross-compile/arsitektur, integritas dan pengecualian privat pada kit, console help serta source-probe aktual worker AI/frame kosong. 452 regresi/89,97% coverage dan 69 native macOS PASS. Fitur Windows executable/installer/offline/ACL/driver/upgrade/uninstall NOT RUN; gate belum lulus.
