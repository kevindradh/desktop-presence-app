"""Settings form with explicit reload, conflict protection and no polling resets."""
from PyQt6 import sip
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
    QHBoxLayout, QPushButton, QSpinBox, QVBoxLayout, QWidget)

from app.widgets.cards import text_label


class SettingsPage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.pending = False
        self.saved = None
        body = QVBoxLayout(self)
        body.setSpacing(14)
        body.addWidget(text_label('Pengaturan berlaku untuk pemeriksaan baru. Pemeriksaan yang sedang berjalan tetap memakai nilai saat dimulai.'))
        self.form_widget = QWidget()
        form = QFormLayout(self.form_widget)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.fields = {}
        for key, title, minimum, maximum, decimals, initial in (
            ('similarity_threshold', 'Ambang kecocokan wajah', 0, 1, 2, .60),
            ('recognition_timeout', 'Batas waktu pemeriksaan (detik)', .01, 300, 2, 3),
            ('anti_spoof_threshold', 'Ambang keaslian wajah', 0, 1, 2, .85),
        ):
            field = QDoubleSpinBox()
            field.setDecimals(decimals)
            field.setRange(minimum, maximum)
            field.setSingleStep(.01 if maximum == 1 else .1)
            field.setValue(initial)
            self.fields[key] = field
            form.addRow(title, field)
        for key, title, label in (
            ('max_face_size', 'Ukuran wajah maksimum', 'Auto'),
            ('check_in_start', 'Awal check-in', 'Shift'),
        ):
            field = QComboBox()
            field.addItem(label, label)
            self.fields[key] = field
            form.addRow(title, field)
        self.fields['duplicate_window'] = QSpinBox()
        self.fields['duplicate_window'].setRange(1, 86400)
        self.fields['duplicate_window'].setValue(60)
        form.addRow('Jeda absensi berulang (detik)', self.fields['duplicate_window'])
        for key, title in (('anti_spoof_enabled', 'Periksa keaslian wajah (anti-spoof)'),
                           ('auto_checkout', 'Checkout otomatis')):
            self.fields[key] = QCheckBox(title)
            form.addRow(self.fields[key])
        for key, field in self.fields.items():
            field.setAccessibleName(key)
        self.fields['anti_spoof_enabled'].setChecked(True)
        body.addWidget(self.form_widget)
        self.warning = text_label('')
        body.addWidget(self.warning)
        self.fields['anti_spoof_enabled'].toggled.connect(self.update_warning)
        self.update_warning()
        body.addWidget(text_label('Registrasi lima sudut tetap memeriksa keaslian dengan ambang 0,85. Aturan jeda absensi, awal shift dan checkout otomatis digunakan setelah modul absensi Tahap 10 tersedia.'))
        row = QHBoxLayout()
        self.save_button = QPushButton('Simpan pengaturan')
        self.reload_button = QPushButton('Muat ulang dari database')
        self.save_button.clicked.connect(self.save)
        self.reload_button.clicked.connect(self.reload)
        row.addWidget(self.save_button)
        row.addWidget(self.reload_button)
        body.addLayout(row)
        self.message = text_label('')
        body.addWidget(self.message)
        body.addStretch()
        self.controls()

    def update_warning(self):
        self.warning.setText('Anti-spoof aktif: pemeriksaan wajah harus lolos keaslian.' if
            self.fields['anti_spoof_enabled'].isChecked() else
            'Anti-spoof NONAKTIF: foto atau replay tidak diperiksa keasliannya pada uji wajah tersimpan dan pengenalan berikutnya.')

    def controls(self):
        self.form_widget.setEnabled(not self.pending and self.saved is not None)
        self.save_button.setEnabled(not self.pending and self.saved is not None)
        self.reload_button.setEnabled(not self.pending)

    def values(self):
        values = {}
        for key, field in self.fields.items():
            values[key] = (field.isChecked() if isinstance(field, QCheckBox) else
                field.currentData() if isinstance(field, QComboBox) else field.value())
        return values

    def display(self, values):
        self.saved = dict(values)
        for key, value in values.items():
            field = self.fields[key]
            if isinstance(field, QCheckBox):
                field.setChecked(value)
            elif isinstance(field, QComboBox):
                field.setCurrentIndex(field.findData(value))
            else:
                field.setValue(value)
        self.controls()

    def run(self, operation, *, saving=False):
        controller = self.controller
        if self.pending or not controller.login or controller._closing:
            return
        token = controller.login.token
        self.pending = True
        self.controls()
        def done(result):
            if sip.isdeleted(self):
                return
            self.pending = False
            if not controller.login or controller.login.token != token or controller._closing:
                return
            if result.error:
                self.message.setText(result.error)
                controller._handle_denial(result.error)
            else:
                self.display(result.value)
                self.message.setText('Pengaturan tersimpan. Pemeriksaan baru akan memakai nilai ini.' if saving else 'Pengaturan dimuat dari database.')
            self.controls()
        def start():
            if sip.isdeleted(self) or controller._closing or not controller.login or controller.login.token != token:
                return
            if controller.jobs.tasks.busy:
                QTimer.singleShot(25, start)
                return
            controller.jobs.run(lambda: operation(controller.settings_service, token), done, blocks_ui=False)
        start()

    def reload(self):
        self.run(lambda service, token: service.load(token))

    def save(self):
        values, expected = self.values(), self.saved
        if expected is not None:
            self.run(lambda service, token: service.save(token, values, expected), saving=True)
