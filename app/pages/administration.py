"""Administrative forms. All data and mutations pass through authorized services."""
from pathlib import Path
from zoneinfo import ZoneInfo

from PyQt6 import sip
from PyQt6.QtCore import QDate, QTime, QTimer, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDateEdit, QFileDialog, QFormLayout, QGridLayout,
    QHBoxLayout, QLabel, QLayout, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QTimeEdit, QVBoxLayout, QWidget)

from app.widgets.cards import text_label


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    widget.horizontalHeader().setStretchLastSection(True)
    widget.setMinimumHeight(200)
    return widget


def fill_table(widget, rows):
    widget.blockSignals(True)
    widget.setRowCount(0)
    widget.setRowCount(len(rows))
    for index, values in enumerate(rows):
        for column, value in enumerate(values):
            widget.setItem(index, column, QTableWidgetItem(str(value)))
    widget.resizeColumnsToContents()
    widget.blockSignals(False)


def form_widget():
    widget = QWidget()
    form = QFormLayout(widget)
    form.setContentsMargins(0, 0, 0, 0)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
    return widget, form


def line(maximum):
    field = QLineEdit()
    field.setMaxLength(maximum)
    return field


def set_options(combo, options, *, placeholder=None):
    current = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    if placeholder:
        combo.addItem(placeholder, None)
    for title, value in options:
        combo.addItem(title, value)
    index = combo.findData(current)
    combo.setCurrentIndex(max(0, index))
    combo.blockSignals(False)


class AdminPage(QWidget):
    def __init__(self, controller, route, description):
        super().__init__()
        self.controller, self.route = controller, route
        self.service_name = "administration"
        self.selected = None
        self.rows = []
        self.pending = False
        self._reload_needed = False
        self.buttons = []
        self.body = QVBoxLayout(self)
        self.body.setSpacing(14)
        if description:
            self.body.addWidget(text_label(description))
        self.message = text_label("")
        self.body.addWidget(self.message)

    def button(self, text, callback, row=None):
        button = QPushButton(text)
        button.clicked.connect(callback)
        self.buttons.append(button)
        (row if row is not None else self.body).addWidget(button)
        return button

    def confirm(self, title, text, action):
        dialog = QMessageBox(QMessageBox.Icon.Question, title, text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self)
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        def done(result):
            if result == QMessageBox.StandardButton.Yes.value:
                action()
            dialog.deleteLater()
        dialog.finished.connect(done)
        dialog.open()

    def run(self, operation, success, *, loading=False):
        if self.pending:
            self._reload_needed |= loading
            return
        if not self.controller.login or self.controller._closing:
            return
        self.pending = True
        self.table.setEnabled(False)
        token = self.controller.login.token
        for button in self.buttons:
            button.setEnabled(False)
        if not loading:
            self.form_widget.setEnabled(False)
        def done(result):
            if sip.isdeleted(self):
                return
            self.pending = False
            if not self.controller.login or self.controller.login.token != token or self.controller._closing:
                return
            for button in self.buttons:
                button.setEnabled(True)
            self.table.setEnabled(True)
            self.form_widget.setEnabled(True)
            if result.error:
                self.message.setText(result.error)
                self.controller._handle_denial(result.error)
            else:
                self.message.setText("")
                success(result.value)
            self.controls()
            if self._reload_needed:
                self._reload_needed = False
                self.reload()
        def start():
            if sip.isdeleted(self) or self.controller._closing:
                return
            if not self.controller.login or self.controller.login.token != token:
                return
            if self.controller.jobs.tasks.busy:
                QTimer.singleShot(25, start)
                return
            self.controller.jobs.run(lambda: operation(getattr(self.controller, self.service_name), token), done, blocks_ui=False)
        start()

    def changed(self, result):
        self.clear_form()
        self.reload()

    def refresh(self):
        self.clear_form()
        self.reload()

    def controls(self):
        pass


class GroupsPage(AdminPage):
    def __init__(self, controller):
        super().__init__(controller, "groups", "Kelola grup anggota. Grup yang digunakan tetap dipertahankan untuk menjaga riwayat.")
        self.table = table(["Nama grup", "Deskripsi", "Anggota"])
        self.table.itemSelectionChanged.connect(self.select)
        self.body.addWidget(self.table)
        self.form_widget, form = form_widget()
        self.name, self.description = line(160), line(2000)
        form.addRow("Nama grup *", self.name)
        form.addRow("Deskripsi", self.description)
        self.body.addWidget(self.form_widget)
        buttons = QHBoxLayout()
        self.new_button = self.button("Form grup baru", self.clear_form, buttons)
        self.save_button = self.button("Simpan grup", self.save, buttons)
        self.delete_button = self.button("Hapus grup", self.delete, buttons)
        self.refresh_button = self.button("Muat ulang", self.refresh, buttons)
        self.body.addLayout(buttons)
        self.body.addStretch()
        self.name.textChanged.connect(self.controls)
        self.clear_form()

    def controls(self):
        self.save_button.setEnabled(not self.pending and bool(self.name.text().strip()))
        self.delete_button.setEnabled(not self.pending and self.selected is not None)

    def clear_form(self):
        self.selected = None
        self.table.clearSelection()
        self.name.clear()
        self.description.clear()
        self.controls()

    def select(self):
        index = self.table.currentRow()
        if not self.table.selectedItems() or not 0 <= index < len(self.rows):
            return
        self.selected = self.rows[index]
        self.name.setText(self.selected.name)
        self.description.setText(self.selected.description)
        self.controls()

    def reload(self):
        def display(rows):
            self.rows = rows
            fill_table(self.table, [(r.name, r.description, r.member_count) for r in rows])
            self.message.setText(f"{len(rows)} grup" if rows else "Belum ada grup. Buat grup pertama melalui formulir.")
        self.run(lambda service, token: service.groups(token), display, loading=True)

    def save(self):
        selected, name, description = self.selected, self.name.text(), self.description.text()
        self.run(lambda service, token: service.save_group(token, name, description,
            group_id=selected.id if selected else None, revision=selected.revision if selected else None), self.changed)

    def delete(self):
        selected = self.selected
        if selected:
            self.confirm("Hapus grup", f'Hapus grup “{selected.name}”? Grup yang masih digunakan tidak dapat dihapus.',
                lambda: self.run(lambda service, token: service.delete_group(token, selected.id, selected.revision), self.changed))


class ShiftsPage(AdminPage):
    def __init__(self, controller):
        super().__init__(controller, "shifts", "Shift malam berakhir pada hari berikutnya. Penugasan anggota dilakukan dari detail anggota.")
        self.table = table(["Nama shift", "Mulai", "Selesai", "Toleransi", "Rentang"])
        self.table.itemSelectionChanged.connect(self.select)
        self.body.addWidget(self.table)
        self.form_widget, form = form_widget()
        self.name = line(120)
        self.start, self.end = QTimeEdit(QTime(8, 0)), QTimeEdit(QTime(17, 0))
        self.start.setDisplayFormat("HH:mm")
        self.end.setDisplayFormat("HH:mm")
        self.grace = QSpinBox()
        self.grace.setRange(0, 1439)
        self.grace.setSuffix(" menit")
        self.grace.setValue(10)
        form.addRow("Nama shift *", self.name)
        form.addRow("Jam mulai *", self.start)
        form.addRow("Jam selesai *", self.end)
        form.addRow("Toleransi terlambat", self.grace)
        self.note = text_label("")
        form.addRow(self.note)
        self.body.addWidget(self.form_widget)
        buttons = QHBoxLayout()
        self.new_button = self.button("Form shift baru", self.clear_form, buttons)
        self.save_button = self.button("Simpan shift", self.save, buttons)
        self.delete_button = self.button("Hapus shift", self.delete, buttons)
        self.refresh_button = self.button("Muat ulang", self.refresh, buttons)
        self.body.addLayout(buttons)
        self.body.addWidget(text_label("Pulang sebelum jam selesai akan diperiksa saat pencatatan kehadiran tersedia. Jadwal yang sudah digunakan tidak diubah agar riwayat tetap akurat."))
        self.body.addStretch()
        self.name.textChanged.connect(self.controls)
        self.start.timeChanged.connect(self.controls)
        self.end.timeChanged.connect(self.controls)
        self.grace.valueChanged.connect(self.controls)
        self.clear_form()

    def controls(self):
        begin, end = self.start.time(), self.end.time()
        duration = (begin.secsTo(end) // 60) % 1440
        valid = bool(self.name.text().strip()) and duration > 0 and self.grace.value() < duration
        self.save_button.setEnabled(not self.pending and valid)
        self.delete_button.setEnabled(not self.pending and self.selected is not None)
        self.note.setText("Selesai hari berikutnya" if end < begin else "Selesai pada hari yang sama")

    def clear_form(self):
        self.selected = None
        self.table.clearSelection()
        self.name.clear()
        self.start.setTime(QTime(8, 0))
        self.end.setTime(QTime(17, 0))
        self.grace.setValue(10)
        self.controls()

    def select(self):
        index = self.table.currentRow()
        if not self.table.selectedItems() or not 0 <= index < len(self.rows):
            return
        self.selected = row = self.rows[index]
        self.name.setText(row.name)
        self.start.setTime(QTime(row.start.hour, row.start.minute))
        self.end.setTime(QTime(row.end.hour, row.end.minute))
        self.grace.setValue(row.grace)
        self.controls()

    def reload(self):
        def display(rows):
            self.rows = rows
            fill_table(self.table, [(r.name, r.start.strftime("%H:%M"), r.end.strftime("%H:%M"),
                f"{r.grace} menit", "Lintas hari" if r.overnight else "Hari yang sama") for r in rows])
            self.message.setText(f"{len(rows)} shift" if rows else "Belum ada shift.")
        self.run(lambda service, token: service.shifts(token), display, loading=True)

    def save(self):
        selected = self.selected
        arguments = (self.name.text(), self.start.time().toPyTime(), self.end.time().toPyTime(), self.grace.value())
        self.run(lambda service, token: service.save_shift(token, *arguments,
            shift_id=selected.id if selected else None, revision=selected.revision if selected else None), self.changed)

    def delete(self):
        selected = self.selected
        if selected:
            self.confirm("Hapus shift", f'Hapus shift “{selected.name}”? Penugasan dan riwayat yang sudah ada dilindungi.',
                lambda: self.run(lambda service, token: service.delete_shift(token, selected.id, selected.revision), self.changed))


class MembersPage(AdminPage):
    def __init__(self, controller):
        super().__init__(controller, "members", "")
        filters = QHBoxLayout()
        self.search = line(200)
        self.search.setPlaceholderText("Cari nama atau ID anggota")
        self.group_filter, self.status_filter, self.page_size = QComboBox(), QComboBox(), QComboBox()
        self.group_filter.setMinimumWidth(150)
        self.status_filter.setMinimumWidth(120)
        self.page_size.setMinimumWidth(145)
        self.status_filter.addItem("Aktif", True)
        self.status_filter.addItem("Nonaktif", False)
        self.status_filter.addItem("Semua status", None)
        for count in (10, 25, 50):
            self.page_size.addItem(f"{count} per halaman", count)
        for widget in (self.search, self.group_filter, self.status_filter, self.page_size):
            filters.addWidget(widget)
        self.body.addLayout(filters)
        self.table = table(["ID anggota", "Nama lengkap", "Grup", "Status"])
        self.table.itemSelectionChanged.connect(self.select)
        self.body.addWidget(self.table)
        pagination = QHBoxLayout()
        self.previous_button = self.button("Sebelumnya", lambda: self.turn(-1), pagination)
        self.page_label = text_label("Belum ada data")
        pagination.addWidget(self.page_label, 1)
        self.next_button = self.button("Berikutnya", lambda: self.turn(1), pagination)
        self.refresh_button = self.button("Muat ulang", self.refresh, pagination)
        self.body.addLayout(pagination)
        self.offset = self.total = 0
        self.limit = 10
        self.photo_source = None
        self.detail = None
        self.form_widget = QWidget()
        form = QGridLayout(self.form_widget)
        form.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(3, 1)
        self.code, self.name, self.email, self.phone, self.position = line(64), line(200), line(254), line(40), line(160)
        self.group = QComboBox()
        self.photo = text_label("")
        self.preview = QLabel()
        self.preview.setFixedSize(100, 100)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_button = QPushButton("Pilih foto PNG/JPEG")
        self.photo_button.clicked.connect(self.choose_photo)
        self.buttons.append(self.photo_button)
        fields = (("ID anggota *", self.code), ("Nama lengkap *", self.name),
                  ("Grup *", self.group), ("Jabatan", self.position),
                  ("Email", self.email), ("Telepon", self.phone))
        for index, (title, field) in enumerate(fields):
            label = text_label(title, wrap=False)
            label.setBuddy(field)
            column = (index % 2)*2
            form.addWidget(label, index//2, column)
            form.addWidget(field, index//2, column+1)
        photo_area = QWidget()
        photo_area.setMinimumHeight(self.preview.height())
        photo_row = QHBoxLayout(photo_area)
        photo_row.setContentsMargins(0, 0, 0, 0)
        photo_row.setSpacing(16)
        photo_row.addWidget(self.preview)
        photo_controls = QVBoxLayout()
        photo_controls.addWidget(self.photo)
        photo_controls.addWidget(self.photo_button, alignment=Qt.AlignmentFlag.AlignLeft)
        photo_row.addLayout(photo_controls, 1)
        form.addWidget(text_label("Foto *", wrap=False), 3, 0, alignment=Qt.AlignmentFlag.AlignTop)
        form.addWidget(photo_area, 3, 1, 1, 3)
        tab_fields = [field for _, field in fields]+[self.photo_button]
        for previous, current in zip(tab_fields, tab_fields[1:]):
            QWidget.setTabOrder(previous, current)
        self.body.addWidget(self.form_widget)
        buttons = QHBoxLayout()
        self.new_button = self.button("Form registrasi baru", self.clear_form, buttons)
        self.save_button = self.button("Simpan perubahan", self.save, buttons)
        self.deactivate_button = self.button("Nonaktifkan anggota", self.deactivate, buttons)
        self.capture_button = self.button("Capture lima sudut", self.capture, buttons)
        self.verify_button = self.button('Uji wajah tersimpan',self.verify_face,buttons)
        self.body.addLayout(buttons)
        self._build_assignments()
        self.history = table(["Waktu", "Event", "Status", "Tanggal kerja", "Grup", "Shift", "Pulang awal", "Sumber"])
        self.history_label = text_label("Pilih anggota untuk melihat riwayat yang sudah tersimpan.")
        self.body.addWidget(self.history_label)
        self.body.addWidget(self.history)
        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.setInterval(300)
        self.debounce.timeout.connect(self.filter_changed)
        self.search.textChanged.connect(lambda: self.debounce.start())
        for combo in (self.group_filter, self.status_filter, self.page_size):
            combo.currentIndexChanged.connect(self.filter_changed)
        for field in (self.code, self.name):
            field.textChanged.connect(self.controls)
        self.group.currentIndexChanged.connect(self.controls)
        self.clear_form()

    def _build_assignments(self):
        self.assignment_table = table(["Shift", "Mulai berlaku", "Akhir berlaku"])
        self.assignment_table.setMinimumHeight(140)
        self.body.addWidget(text_label("Penugasan shift", "sectionTitle"))
        self.body.addWidget(self.assignment_table)
        self.assignment_widget, form = form_widget()
        self.shift = QComboBox()
        self.starts, self.ends, self.end_existing_date = (QDateEdit(QDate.currentDate()) for _ in range(3))
        for field in (self.starts, self.ends, self.end_existing_date):
            field.setCalendarPopup(True)
            field.setDisplayFormat("dd/MM/yyyy")
        self.unlimited = QCheckBox("Tanpa tanggal akhir")
        self.unlimited.setChecked(True)
        self.unlimited.toggled.connect(lambda checked: self.ends.setEnabled(not checked))
        self.ends.setEnabled(False)
        form.addRow("Shift", self.shift)
        form.addRow("Tanggal mulai", self.starts)
        form.addRow("Tanggal akhir", self.ends)
        form.addRow(self.unlimited)
        self.assign_button = QPushButton("Tetapkan shift")
        self.assign_button.clicked.connect(self.assign)
        form.addRow(self.assign_button)
        self.existing_assignment = QComboBox()
        self.end_assignment_button = QPushButton("Akhiri penugasan")
        self.end_assignment_button.clicked.connect(self.end_assignment)
        self.shift.currentIndexChanged.connect(self.controls)
        self.existing_assignment.currentIndexChanged.connect(self.controls)
        form.addRow("Penugasan yang diakhiri", self.existing_assignment)
        form.addRow("Tanggal akhir berlaku", self.end_existing_date)
        form.addRow(self.end_assignment_button)
        self.buttons.extend((self.assign_button, self.end_assignment_button))
        self.body.addWidget(self.assignment_widget)

    def controls(self):
        valid = bool(self.code.text().strip() and self.name.text().strip() and self.group.currentData())
        self.save_button.setEnabled(not self.pending and self.selected is not None and valid)
        self.deactivate_button.setEnabled(not self.pending and self.selected is not None and self.selected.active)
        self.capture_button.setEnabled(not self.pending and valid and (self.selected is None or self.selected.active))
        self.capture_button.setText('Registrasi ulang wajah' if self.selected else 'Capture lima sudut')
        self.verify_button.setEnabled(not self.pending and bool(self.selected and self.selected.active and self.detail and self.detail.has_embeddings))
        self.photo_button.setEnabled(not self.pending and self.selected is not None and self.selected.active)
        self.previous_button.setEnabled(not self.pending and self.offset > 0)
        self.next_button.setEnabled(not self.pending and self.offset + self.limit < self.total)
        can_assign = bool(self.detail and self.detail.can_assign and self.selected and self.selected.active)
        self.assignment_widget.setVisible(bool(self.detail and self.detail.can_assign))
        self.assign_button.setEnabled(not self.pending and can_assign and self.shift.currentData() is not None)
        self.end_assignment_button.setEnabled(not self.pending and can_assign and self.existing_assignment.currentData() is not None)

    def clear_form(self):
        self.selected = self.detail = None
        self.photo_source = None
        self.table.clearSelection()
        for field in (self.code, self.name, self.email, self.phone, self.position):
            field.clear()
        self.group.setCurrentIndex(0)
        self.photo.clear()
        self.photo.hide()
        self.preview.clear()
        fill_table(self.assignment_table, [])
        fill_table(self.history, [])
        self.existing_assignment.clear()
        self.history_label.setText("Pilih anggota untuk melihat riwayat yang sudah tersimpan.")
        self.controls()

    def filter_changed(self):
        self.offset = 0
        self.reload()

    def turn(self, direction):
        self.offset = max(0, self.offset + direction * self.limit)
        self.reload()

    def reload(self):
        self.debounce.stop()
        arguments = dict(search=self.search.text(), group_id=self.group_filter.currentData(),
                         active=self.status_filter.currentData(), offset=self.offset,
                         limit=self.page_size.currentData())
        def display(result):
            self.rows = result.rows
            self.total, self.offset, self.limit = result.total, result.offset, result.limit
            fill_table(self.table, [(r.code, r.name, r.group_name, "Aktif" if r.active else "Nonaktif") for r in result.rows])
            options = [(g.name, g.id) for g in result.groups]
            set_options(self.group_filter, options, placeholder="Semua grup")
            set_options(self.group, options, placeholder="Pilih grup")
            end = self.offset + len(result.rows)
            self.page_label.setText(f"{self.offset + 1 if result.total else 0}–{end} dari {result.total} anggota")
            self.message.setText("Tidak ada anggota sesuai filter." if not result.rows else "")
            if result.cleanup_pending:
                self.message.setText('Data tersimpan, tetapi pembersihan foto lama tertunda. Periksa akses folder data; pembersihan dicoba lagi saat daftar dimuat.')
        self.run(lambda service, token: service.members(token, **arguments), display, loading=True)

    def select(self):
        index = self.table.currentRow()
        if not self.table.selectedItems() or not 0 <= index < len(self.rows):
            return
        record_id = self.rows[index].id
        self.run(lambda service, token: service.member(token, record_id), self.show_detail, loading=True)

    def show_detail(self, result):
        self.detail = result
        self.selected = row = result.member
        self.photo_source = None
        for field, value in ((self.code, row.code), (self.name, row.name), (self.email, row.email),
                             (self.phone, row.phone), (self.position, row.position)):
            field.setText(value)
        self.group.setCurrentIndex(max(0, self.group.findData(row.group_id)))
        self.photo.setText(Path(row.photo).name)
        self.photo.show()
        self.preview.clear()
        base = self.controller.config.resource_root if row.photo.startswith('resources/samples/') else self.controller.config.root
        path = (Path(base) / row.photo).resolve()
        if path.is_relative_to(Path(base).resolve()) and path.is_file():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.preview.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                                     Qt.TransformationMode.SmoothTransformation))
        fill_table(self.assignment_table, [(a.shift_name, a.starts.isoformat(), a.ends.isoformat() if a.ends else "Tanpa akhir") for a in result.assignments])
        set_options(self.shift, [(s.name, s.id) for s in result.shifts], placeholder="Pilih shift")
        set_options(self.existing_assignment, [(f"{a.shift_name} • {a.starts.isoformat()}", a.id) for a in result.assignments], placeholder="Pilih penugasan")
        fill_table(self.history, [(a.timestamp.astimezone(ZoneInfo(self.controller.config.timezone)).strftime("%d/%m/%Y %H:%M"), a.event, a.status,
            a.work_date.isoformat(), a.group_name, a.shift_name, "Ya" if a.early else "Tidak", "Otomatis" if a.automatic else "Scan") for a in result.history])
        self.history_label.setText(f"Riwayat tersimpan: {result.history_total} event (maksimal 50 terbaru ditampilkan)." if result.history_total
            else "Belum ada riwayat. Gunakan halaman Kehadiran untuk memulai absensi.")
        self.controls()

    def choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih foto anggota", "", "Gambar (*.png *.jpg *.jpeg)")
        if path:
            self.photo_source = path
            self.photo.setText(Path(path).name)
            self.photo.show()

    def save(self):
        selected = self.selected
        if selected is None:
            return
        arguments = (selected.id, selected.revision, self.code.text(), self.name.text(), self.group.currentData())
        optional = dict(email=self.email.text(), phone=self.phone.text(), position=self.position.text(), photo_source=self.photo_source)
        self.run(lambda service, token: service.update_member(token, *arguments, **optional), self.changed)

    def deactivate(self):
        selected = self.selected
        if selected:
            self.confirm("Nonaktifkan anggota", f'Nonaktifkan “{selected.name}” dan hapus foto profil serta embedding wajahnya? Riwayat kehadiran tetap disimpan. Menggunakan wajah lagi memerlukan registrasi baru.',
                lambda: self.run(lambda service, token: service.deactivate_member(token, selected.id, selected.revision), self.changed))

    def capture(self,checked=False,*,verification=False):
        selected=self.selected
        fields=dict(code=self.code.text(),name=self.name.text(),group_id=self.group.currentData(),
            email=self.email.text(),phone=self.phone.text(),position=self.position.text())
        def start(binding):
            if self.isVisible():
                self.controller.open_enrollment(binding,fields,self)
            else:
                self.controller.enrollment_service.cancel(binding)
        self.run(lambda service,token:self.controller.enrollment_service.begin(token,
            member_id=selected.id if selected else None,revision=selected.revision if selected else None,
            fields=None if verification else fields,purpose='verification' if verification else 'enrollment'),start,loading=True)

    def verify_face(self):
        if self.selected and self.detail and self.detail.has_embeddings:
            self.capture(verification=True)

    def on_leave(self):
        self.controller.stop_enrollment()

    def refresh_detail(self, result=None):
        if self.selected:
            record_id = self.selected.id
            self.run(lambda service, token: service.member(token, record_id), self.show_detail, loading=True)

    def assign(self):
        if not self.selected or self.shift.currentData() is None:
            return
        arguments = (self.selected.id, self.selected.revision, self.shift.currentData(),
            self.starts.date().toPyDate(), None if self.unlimited.isChecked() else self.ends.date().toPyDate())
        self.run(lambda service, token: service.assign_shift(token, *arguments), self.refresh_detail)

    def end_assignment(self):
        if not self.selected or self.existing_assignment.currentData() is None:
            return
        arguments = (self.selected.id, self.selected.revision, self.existing_assignment.currentData(), self.end_existing_date.date().toPyDate())
        self.run(lambda service, token: service.end_assignment(token, *arguments), self.refresh_detail)
