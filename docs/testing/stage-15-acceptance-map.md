# Peta bukti penerimaan Tahap 15

28 Oktober 2026. Peta ini mencakup seluruh31 user story dari [matriks kebutuhan](../requirements-traceability.md). Keberhasilan tes otomatis tidak otomatis berarti seluruh UAT wajah nyata selesai. Hasil run lengkap dan cakupan pengukurannya ada di [laporan Tahap15](stage-15.md).

| User story | Cakupan otomatis yang diperiksa | Modul tes | Batas yang tetap dicatat |
|---|---|---|---|
| US-001,002,025,026 | Login benar/salah, bootstrap, role, akun, reset, session, remember dan lockout | test_auth, test_session_ui, test_credentials, test_keychain_native | Login/dashboard Windows terbaru dikonfirmasi pengguna; seluruh aksi per role pada desktop customer belum diklik ulang |
| US-003,004,005,006,007 | Form/pencarian/pagination, simpan/edit/nonaktif, audit/riwayat, lima pose dan registrasi ulang atomik, kegagalan/cancel | test_administration, test_administration_ui, test_enrollment, test_enrollment_capture, test_enrollment_ui, test_auto_capture | Capture lima sudut wajah nyata dan pengenalan ulang memerlukan pengujian peserta; fixture sintetis tidak menggantikannya |
| US-008,009,010,011,012,020,028 | Gate identitas/liveness, unknown, IN/OUT/istirahat, cooldown, toleransi batas, malam, anti-spoof, commit/audit dan feedback | test_attendance, test_attendance_ui, test_attendance_presentation, test_ai_engine, test_ai_models, test_inference | Serangan cetak/replay, suara dan alur wajah nyata belum diukur pada putaran Windows ini |
| US-013,014 | Hitungan dashboard, izin/absent, tanggal shift, polling tanpa kehilangan fokus, grafik dan feed setelah commit | test_dashboard, test_dashboard_ui, test_dashboard_chart_layout | Dashboard native terlihat setelah login; ini tidak menyatakan seluruh AC sudah diuji manual pada AMD |
| US-015,016,019 | Grup, relasi anggota/grup, shift, penugasan dan histori | test_administration, test_administration_validation, test_administration_ui | Alur administrasi diuji teknis; perubahan pada data uji tetap terpisah dari data operasional |
| US-017,018 | CRUD/validasi perangkat, worker kamera, timeout/retry, secret RTSP, error dan shutdown | test_devices, test_devices_ui, test_devices_validation, test_cameras | FaceTime indeks0 nyata lulus; USB kedua/cabut fisik dan RTSP positif tertunda |
| US-021,022,023,024 | Filter/snapshot, seluruh halaman, group historis, XLSX/PDF, Unicode, cancel, penolakan publikasi parsial | test_reports, test_reports_ui, test_report_exports | Pembaca Excel/PDF pada perangkat customer tetap belum diuji pada putaran ini |
| US-027 | Settings numerik, role, perubahan threshold dan invalidasi policy scan lama | test_settings, test_settings_ui, test_attendance | Pengukuran akurasi menggunakan threshold yang dipilih tetap terpisah |
| US-029,030,031 | Audit lintas fungsi dan izin, enkripsi backup, validasi/retensi, restore atomik, rollback, biometrik dilewati sesuai kebijakan | test_audit, test_backup_codec, test_backups, test_backups_ui, test_private_files | Restore memakai schema/folder uji; tidak memulihkan data operasional untuk tes |

Kebutuhan PRD tambahan tentang latency,10.000 anggota, akurasi, liveness, availability, soak dan dukungan hardware diperiksa terpisah. Coverage kode tidak menggantikan pengukuran tersebut. Peta ini tidak menandai31 user story sebagai PASS penuh.
