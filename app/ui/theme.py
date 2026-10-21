from PyQt6.QtGui import QColor, QFontDatabase, QPalette


STYLESHEET = """
QWidget { font-size: 13px; color: #243a33; }
QMainWindow, QWidget#workspace { background: #f5f7f4; }
QFrame#sidebar { background: #142d25; border: none; }
QFrame#sidebar QLabel { color: #e6eee8; }
QLabel#brand { font-size: 25px; font-weight: 700; letter-spacing: 1px; }
QLabel#brandHint { color: #9bb6a7; font-size: 11px; }
QListWidget#navigation { background: transparent; border: 0; outline: 0; }
QListWidget#navigation::item { color: #b6c9be; padding: 11px 15px; margin: 2px 0; border-radius: 7px; }
QListWidget#navigation::item:selected { background: #2c4b3e; color: white; font-weight: 600; }
QListWidget#navigation::item:hover { background: #213d31; color: white; }
QFrame#sidebarFooter { background: #203e32; border-radius: 8px; }
QLabel[kind="muted"] { color: #60736b; line-height: 1.5; }
QLabel[kind="eyebrow"] { color: #4e7862; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
QLabel[kind="pageTitle"] { color: #213e31; font-size: 25px; font-weight: 650; }
QLabel[kind="sectionTitle"] { font-size: 17px; font-weight: 650; }
QLabel[kind="cardTitle"] { font-size: 20px; font-weight: 650; }
QFrame#hero { background: #e6eee1; border: 1px solid #d5e1cf; border-radius: 13px; }
QLabel[kind="heroTitle"] { font-size: 32px; font-weight: 700; color: #24482f; }
QLabel[kind="heroBody"] { color: #4a6650; font-size: 14px; }
QLabel[kind="heroNote"] { color: #4a6650; font-size: 12px; }
QFrame#featureCard { background: white; border: 1px solid #e0e7df; border-radius: 11px; }
QWidget#attendanceDashboard QDateEdit:focus { border: 2px solid #2d6240; padding: 7px 9px; }
QFrame#reviewCard { background: #edf1eb; border-radius: 9px; }
QFrame#errorBanner { background: #fff0e8; border: 1px solid #eed3bd; border-radius: 8px; }
QPushButton { padding: 10px 16px; border: 1px solid #d3ded4; border-radius: 6px; background: #fff; color: #34503f; font-weight: 600; }
QPushButton:hover { background: #eaf0e7; }
QPushButton:focus { border: 2px solid #649372; padding: 9px 15px; }
QPushButton[variant="primary"] { background: #2d6240; color: white; border-color: #2d6240; }
QPushButton[variant="primary"]:hover { background: #245236; }
QPushButton:disabled { background: #edf0eb; color: #9aa79e; border-color: #e1e6df; }
QLineEdit, QComboBox, QAbstractSpinBox { background: #fff; border: 1px solid #cbd9ce; border-radius: 6px; padding: 8px 10px; min-height: 20px; }
QLineEdit:focus, QComboBox:focus { border-color: #649372; }
QLineEdit:disabled { background: #edf0eb; color: #7b8e80; }
QCheckBox::indicator { width: 18px; height: 18px; background: #fff; border: 1px solid #8ba693; border-radius: 3px; }
QCheckBox::indicator:checked { background: #2d6240; border-color: #2d6240; }
QTableWidget { background: #fff; border: 1px solid #d3ded4; gridline-color: #e0e7df; selection-background-color: #2d6240; selection-color: #fff; }
QHeaderView::section { background: #edf1eb; padding: 8px; border: 0; border-bottom: 1px solid #d3ded4; font-weight: 600; }
QProgressBar { border: 1px solid #dbe5db; background: #f0f4ee; border-radius: 7px; height: 22px; text-align: center; }
QProgressBar::chunk { background: #78a879; border-radius: 6px; }
QScrollArea { background: transparent; border: 0; }
QStatusBar { background: #f5f7f4; color: #728176; font-size: 11px; }
"""


def apply_theme(application):
    # Explicit palette keeps the light workspace legible under macOS dark mode.
    palette = QPalette()
    for role, color in ((QPalette.ColorRole.Window, "#f5f7f4"),
                        (QPalette.ColorRole.WindowText, "#243a33"),
                        (QPalette.ColorRole.Base, "#ffffff"),
                        (QPalette.ColorRole.Text, "#243a33"),
                        (QPalette.ColorRole.Button, "#ffffff"),
                        (QPalette.ColorRole.ButtonText, "#243a33"),
                        (QPalette.ColorRole.Highlight, "#2d6240"),
                        (QPalette.ColorRole.HighlightedText, "#ffffff")):
        palette.setColor(role, QColor(color))
    application.setPalette(palette)
    application.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont))
    application.setStyleSheet(STYLESHEET)
