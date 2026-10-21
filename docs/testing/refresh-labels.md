# Label Refresh

Sesuai permintaan pengguna, tujuh tombol Muat ulang menjadi Refresh pada halaman Grup, Shift, Anggota, Perangkat, Kehadiran, Pengaturan, dan Pengguna. Termasuk tombol Pengaturan yang sebelumnya bernama Muat ulang dari database. Callback, hak akses, keadaan aktif/nonaktif, dan urutan keyboard tidak berubah.

Alasan: label lebih singkat dan seragam mengikuti pilihan pengguna. Arah, warna, tipografi dan dial tetap mengikuti tampilan sebelumnya; tidak ada aset, kontrol, atau efek baru.

Delivery Gate revisi teks: PASS, perubahan terbatas pada string label, tanpa klaim atau jargon tambahan di luar istilah yang diminta pengguna. PASS, Purpose-Gate dan konsistensi karena tujuh tombol menggunakan nama yang sama untuk tindakan refresh. Tema, layout dan fungsi mengikuti implementasi yang sudah diuji. Pemeriksaan sumber memastikan tidak ada label tombol Muat ulang yang tersisa, dan diff diperiksa tanpa galat whitespace. Tes fungsional tidak diulang untuk penggantian label saja.
