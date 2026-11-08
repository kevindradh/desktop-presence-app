# Logo StarGate

PNG logo tersimpan di `resources/branding/`. Logo hijau dipakai di panel masuk, pembuatan Super Admin, ganti password, dan persiapan aplikasi. Logo putih dipakai langsung pada sidebar gelap.

| Aset dalam `resources/branding/` | Penggunaan |
| --- | --- |
| `stargate.png` | PNG hijau asli untuk panel terang |
| `stargate-white.png` | PNG putih asli untuk sidebar |
| `stargate-app.png` | Ikon 1024 × 1024 dengan alas putih dan sudut transparan |
| `stargate.ico` | Ikon Windows, termasuk executable dan installer |
| `stargate.icns` | Ikon aplikasi macOS |

Setelah mengganti PNG hijau, jalankan `.venv/bin/python scripts/prepare_brand_icons.py` untuk menghasilkan ulang ikon. Aplikasi yang dijalankan dari source memuat logo baru saat dibuka kembali. Untuk memperbarui ikon di Dock, taskbar, dan installer, build ulang paket pada sistem operasi tujuan.
