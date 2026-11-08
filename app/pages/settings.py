"""Settings form with explicit reload, conflict protection and no polling resets."""
from PyQt6 import sip
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout,
    QHBoxLayout, QPushButton, QSpinBox, QVBoxLayout, QWidget)

from app.widgets.cards import text_label
from app.settings.defaults import INDONESIAN_TIMEZONES


class SettingsPage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.pending = False
        self.saved = None
        body = QVBoxLayout(self)
        body.setSpacing(14)
        self.form_widget = QWidget()
        form = QGridLayout(self.form_widget)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(8)
        form.setColumnStretch(0, 1)
        form.setColumnStretch(1, 1)
        self.fields = {}
        timezone = QComboBox()
        for zone, label in INDONESIAN_TIMEZONES.items():
            timezone.addItem(label, zone)
        self.fields['timezone'] = timezone
        inputs = [('Zona waktu lokasi utama', timezone)]
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
            inputs.append((title, field))
        self.fields['duplicate_window'] = QSpinBox()
        self.fields['duplicate_window'].setRange(1, 86400)
        self.fields['duplicate_window'].setValue(60)
        inputs.append(('Jeda absensi berulang (detik)', self.fields['duplicate_window']))
        for index, (title, field) in enumerate(inputs):
            row, column = divmod(index, 2)
            label = text_label(title)
            label.setBuddy(field)
            form.addWidget(label, row * 2, column)
            form.addWidget(field, row * 2 + 1, column)
        checkbox_row = 2 * ((len(inputs) + 1) // 2)
        for column, (key, title) in enumerate((
                ('anti_spoof_enabled', 'Periksa keaslian wajah'),
                ('auto_checkout', 'Checkout otomatis'))):
            self.fields[key] = QCheckBox(title)
            form.addWidget(self.fields[key], checkbox_row, column)
        for key, field in self.fields.items():
            field.setAccessibleName(key)
        self.fields['anti_spoof_enabled'].setChecked(True)
        body.addWidget(self.form_widget)
        self.warning = text_label('Foto atau rekaman dapat lolos.')
        body.addWidget(self.warning)
        self.fields['anti_spoof_enabled'].toggled.connect(self.update_warning)
        self.update_warning()
        row = QHBoxLayout()
        self.save_button = QPushButton('Simpan pengaturan')
        self.reload_button = QPushButton('Refresh')
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
        self.warning.setVisible(not self.fields['anti_spoof_enabled'].isChecked())

    def controls(self):
        self.message.setVisible(bool(self.message.text()))
        self.form_widget.setEnabled(not self.pending and self.saved is not None)
        self.save_button.setEnabled(not self.pending and self.saved is not None)
        self.reload_button.setEnabled(not self.pending)

    def values(self):
        values = dict(self.saved or {})
        for key, field in self.fields.items():
            values[key] = (field.isChecked() if isinstance(field, QCheckBox) else
                field.currentData() if isinstance(field, QComboBox) else field.value())
        return values

    def display(self, values):
        self.saved = dict(values)
        for key, field in self.fields.items():
            value = values[key]
            if isinstance(field, QCheckBox):
                field.setChecked(value)
            elif isinstance(field, QComboBox):
                if key == 'timezone' and field.findData(value) == -1:
                    field.addItem(value, value)
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
                controller._handle_denial(result.error)
            else:
                self.display(result.value)
                self.message.setText('Pengaturan tersimpan.' if saving else '')
                if controller.apply_timezone(result.value['timezone']):
                    controller._open_shell()
                    controller.navigate('settings')
                    controller._message('Zona waktu lokasi utama diperbarui.')
                    return
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
