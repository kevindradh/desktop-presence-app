# Logo StarGate

StarGate memakai biru `#014AAD` sebagai warna primer. Simbol pada panel masuk, pembuatan Super Admin, ganti password, dan persiapan aplikasi memakai warna yang sama. Sidebar biru memakai simbol putih.

| Aset dalam `resources/branding/` | Penggunaan |
| --- | --- |
| `stargate.png` | PNG sumber untuk bentuk simbol pada panel terang |
| `stargate-white.png` | PNG putih asli untuk sidebar |
| `stargate-app.png` | Ikon 1024 × 1024 dengan alas putih dan sudut transparan |
| `stargate.ico` | Ikon Windows, termasuk executable dan installer |
| `stargate.icns` | Ikon aplikasi macOS |

Setelah mengganti PNG sumber atau warna primer, jalankan `.venv/bin/python scripts/prepare_brand_icons.py` untuk menghasilkan ulang ikon. Aplikasi yang dijalankan dari source memuat logo baru saat dibuka kembali. Untuk memperbarui ikon di Dock, taskbar, dan installer, build ulang paket pada sistem operasi tujuan.
