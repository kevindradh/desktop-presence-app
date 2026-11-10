from PyQt6.QtGui import QColor, QFontDatabase, QPalette

from app.settings.colors import BORDER, MUTED, PRIMARY, TEXT, TINT, TITLE, WORKSPACE
from app.settings.paths import runtime_paths


STYLESHEET = f"""
QWidget {{ font-size: 13px; color: {TEXT}; }}
QMainWindow, QWidget#workspace {{ background: {WORKSPACE}; }}
QFrame#sidebar {{ background: {PRIMARY}; border: none; }}
QFrame#sidebar QLabel {{ color: #F0F6FF; }}
QLabel#brand {{ font-size: 25px; font-weight: 700; letter-spacing: 1px; }}
QLabel#brandHint {{ color: #DFEBFC; font-size: 11px; }}
QListWidget#navigation {{ background: transparent; border: 0; outline: 0; }}
QListWidget#navigation::item {{ color: #E3EDFC; padding: 11px 15px; margin: 2px 0; border-radius: 7px; }}
QListWidget#navigation::item:selected {{ background: #003171; color: white; font-weight: 600; }}
QListWidget#navigation::item:hover {{ background: #003E91; color: white; }}
QFrame#sidebarFooter {{ background: #003E91; border-radius: 8px; }}
QLabel[kind="muted"] {{ color: {MUTED}; line-height: 1.5; }}
QLabel[kind="eyebrow"] {{ color: {PRIMARY}; font-size: 11px; font-weight: 700; letter-spacing: 1px; }}
QLabel[kind="pageTitle"] {{ color: {TITLE}; font-size: 25px; font-weight: 650; }}
QLabel[kind="sectionTitle"] {{ font-size: 17px; font-weight: 650; }}
QLabel[kind="cardTitle"] {{ font-size: 20px; font-weight: 650; }}
QFrame#hero {{ background: {TINT}; border: 1px solid {BORDER}; border-radius: 13px; }}
QLabel[kind="heroTitle"] {{ font-size: 32px; font-weight: 700; color: {TITLE}; }}
QLabel[kind="heroBody"] {{ color: {MUTED}; font-size: 14px; }}
QLabel[kind="heroNote"] {{ color: {MUTED}; font-size: 12px; }}
QFrame#featureCard {{ background: white; border: 1px solid #DFE7F2; border-radius: 11px; }}
QWidget#attendanceDashboard QDateEdit:focus {{ border: 2px solid {PRIMARY}; padding: 7px 9px; }}
QTabWidget#memberTabs::pane {{ border: 1px solid {BORDER}; background: white; border-radius: 6px; }}
QTabBar#memberTabBar::tab {{ background: white; color: {TITLE}; border: 2px solid transparent; padding: 9px 16px; }}
QTabBar#memberTabBar::tab:selected {{ background: {PRIMARY}; color: white; }}
QTabBar#memberTabBar::tab:focus {{ border-color: #558FD9; }}
QFrame#reviewCard {{ background: {TINT}; border-radius: 9px; }}
QFrame#errorBanner {{ background: #fff0e8; border: 1px solid #eed3bd; border-radius: 8px; }}
QPushButton {{ padding: 10px 16px; border: 1px solid {BORDER}; border-radius: 6px; background: #fff; color: {TITLE}; font-weight: 600; }}
QPushButton:hover {{ background: {TINT}; }}
QPushButton:focus {{ border: 2px solid #558FD9; padding: 9px 15px; }}
QPushButton[variant="primary"] {{ background: {PRIMARY}; color: white; border-color: {PRIMARY}; }}
QPushButton[variant="primary"]:hover {{ background: #003E91; }}
QPushButton[variant="primary"]:focus {{ border-color: #8DB9F2; }}
QPushButton:disabled {{ background: #EBEFF5; color: #8492A5; border-color: #DFE7F2; }}
QLineEdit, QComboBox, QAbstractSpinBox {{ background: #fff; border: 1px solid {BORDER}; border-radius: 6px; padding: 8px 10px; min-height: 20px; }}
QLineEdit:focus, QComboBox:focus {{ border-color: #558FD9; }}
QLineEdit:disabled {{ background: #EBEFF5; color: {MUTED}; }}
QCheckBox::indicator {{ width: 18px; height: 18px; background: #fff; border: 1px solid #8197B4; border-radius: 3px; }}
QCheckBox::indicator:checked {{ background: {PRIMARY}; border-color: {PRIMARY}; image: url("__CHECKBOX_CHECK__"); }}
QCheckBox::indicator:disabled {{ background: #EBEFF5; }}
QCheckBox::indicator:checked:disabled {{ background: #60738E; border-color: #60738E; }}
QTableWidget {{ background: #fff; border: 1px solid {BORDER}; gridline-color: #DFE7F2; selection-background-color: {PRIMARY}; selection-color: #fff; }}
QHeaderView::section {{ background: {TINT}; padding: 8px; border: 0; border-bottom: 1px solid {BORDER}; font-weight: 600; }}
QProgressBar {{ border: 1px solid {BORDER}; background: {WORKSPACE}; border-radius: 7px; height: 22px; text-align: center; }}
QProgressBar::chunk {{ background: #8DB9F2; border-radius: 6px; }}
QScrollArea {{ background: transparent; border: 0; }}
QStatusBar {{ background: {WORKSPACE}; color: {MUTED}; font-size: 11px; }}
"""


def apply_theme(application):
    # Explicit palette keeps the light workspace legible under macOS dark mode.
    palette = QPalette()
    for role, color in ((QPalette.ColorRole.Window, WORKSPACE),
                        (QPalette.ColorRole.WindowText, TEXT),
                        (QPalette.ColorRole.Base, "#ffffff"),
                        (QPalette.ColorRole.Text, TEXT),
                        (QPalette.ColorRole.Button, "#ffffff"),
                        (QPalette.ColorRole.ButtonText, TEXT),
                        (QPalette.ColorRole.Highlight, PRIMARY),
                        (QPalette.ColorRole.Link, PRIMARY),
                        (QPalette.ColorRole.HighlightedText, "#ffffff")):
        palette.setColor(role, QColor(color))
    application.setPalette(palette)
    application.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont))
    check_icon = runtime_paths().resources / 'resources/icons/checkbox-check.svg'
    application.setStyleSheet(STYLESHEET.replace('__CHECKBOX_CHECK__', check_icon.as_posix()))
