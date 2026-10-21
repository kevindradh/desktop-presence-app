from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.widgets.cards import FeatureCard, text_label


class OverviewPage(QWidget):
    def __init__(self, navigate):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        hero = QFrame()
        hero.setObjectName("hero")
        content = QVBoxLayout(hero)
        content.setContentsMargins(30, 28, 30, 28)
        content.setSpacing(12)
        content.addWidget(text_label("STARGATE / KEHADIRAN", "eyebrow"))
        content.addWidget(text_label("Kehadiran yang lebih sederhana.", "heroTitle"))
        content.addWidget(text_label(
            "Satu tempat untuk mengelola anggota, mencatat kehadiran, "
            "dan meninjau laporan organisasi Anda.", "heroBody"))
        content.addSpacing(8)
        content.addWidget(text_label(
            "Pratinjau aplikasi · Modul operasional sedang disiapkan.", "heroNote"))
        layout.addWidget(hero)
        layout.addWidget(text_label("Ruang kerja Anda", "sectionTitle"))
        row = QHBoxLayout()
        row.setSpacing(16)
        specs = [
            ("01", "Anggota", "Pendaftaran wajah dan pengelolaan data anggota dalam satu ruang.",
             "Lihat anggota", "members"),
            ("02", "Kehadiran", "Check-in, check-out, serta aturan shift dan waktu istirahat.",
             "Lihat kehadiran", "attendance"),
            ("03", "Laporan", "Rekap kehadiran dengan filter serta ekspor Excel dan PDF.",
             "Lihat laporan", "reports"),
        ]
        for number, title, body, action, route in specs:
            row.addWidget(FeatureCard(number, title, body, action,
                                     lambda _checked=False, key=route: navigate(key)), 1)
        layout.addLayout(row, 1)
        footer = QFrame()
        footer.setObjectName("reviewCard")
        footer_row = QHBoxLayout(footer)
        footer_row.setContentsMargins(20, 18, 20, 18)
        footer_row.addWidget(text_label(
            "Mulai dengan pemeriksaan aplikasi\n"
            "Uji respons, pembatalan proses, dan penanganan kesalahan tanpa mengubah data.", "muted"), 1)
        button = QPushButton("Buka pemeriksaan")
        button.setProperty("variant", "primary")
        button.clicked.connect(lambda: navigate("diagnostics"))
        footer_row.addWidget(button)
        layout.addWidget(footer)


class PlaceholderPage(QWidget):
    def __init__(self, title, description):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        box = QFrame()
        box.setObjectName("featureCard")
        body = QVBoxLayout(box)
        body.setContentsMargins(36, 36, 36, 36)
        body.setSpacing(18)
        body.addWidget(text_label("SEGERA TERSEDIA", "eyebrow"))
        body.addWidget(text_label(title, "pageTitle"))
        body.addWidget(text_label(description, "muted"))
        body.addWidget(text_label(
            "Halaman ini masih berupa pratinjau. Data belum ditampilkan "
            "dan belum ada perubahan data yang dapat dilakukan.", "muted"))
        layout.addWidget(box)
        layout.addStretch()
