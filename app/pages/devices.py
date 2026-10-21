"""Device setup and explicit preview. RTSP secrets are never restored to fields."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QVBoxLayout)

from app.models.entities import DeviceType
from app.pages.administration import AdminPage, fill_table, form_widget, line, set_options, table
from app.services.cameras import FINAL, STATE_TEXT
from app.services.database import DataValidationError
from app.services.devices import RESOLUTIONS
from app.widgets.cards import text_label


class DevicesPage(AdminPage):
    def __init__(self, controller):
        super().__init__(controller, "devices", "Tambahkan webcam atau IP camera, lalu jalankan pratinjau. Kamera baru dibuka saat Anda memilih Uji koneksi atau Mulai pratinjau.")
        self.service_name = "devices_service"
        self.manager = controller.cameras
        self.cards = {}
        self.table = table(["Perangkat", "Jenis", "Sumber", "Resolusi", "FPS", "Lokasi"])
        self.table.setSelectionMode(self.table.SelectionMode.ExtendedSelection)
        self.table.itemSelectionChanged.connect(self.select)
        self.body.addWidget(self.table)
        self.form_widget, form = form_widget()
        self.name = line(160)
        self.kind, self.resolution, self.location = QComboBox(), QComboBox(), QComboBox()
        for kind, title in ((DeviceType.INTERNAL, "Webcam bawaan"), (DeviceType.USB, "Webcam USB"), (DeviceType.RTSP, "IP camera (RTSP)")):
            self.kind.addItem(title, kind.value)
        for resolution in RESOLUTIONS:
            self.resolution.addItem(resolution, resolution)
        self.resolution.setCurrentIndex(1)
        self.camera_index, self.fps = QSpinBox(), QSpinBox()
        self.camera_index.setRange(0,15)
        self.fps.setRange(1,60)
        self.fps.setValue(30)
        self.rtsp = line(4096)
        self.rtsp.setEchoMode(QLineEdit.EchoMode.Password)
        self.rtsp.setAccessibleName("Sumber RTSP")
        self.show_source = QCheckBox("Tampilkan sumber yang sedang diketik")
        self.show_source.toggled.connect(lambda checked: self.rtsp.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))
        form.addRow("Nama perangkat *", self.name)
        form.addRow("Jenis *", self.kind)
        form.addRow("Nomor kamera lokal", self.camera_index)
        form.addRow("Sumber RTSP", self.rtsp)
        form.addRow(self.show_source)
        form.addRow("Resolusi", self.resolution)
        form.addRow("FPS", self.fps)
        form.addRow("Lokasi *", self.location)
        form.addRow(text_label("Nomor webcam dapat berubah saat perangkat disambungkan ulang. Sumber RTSP tersimpan tetap dirahasiakan; isi kembali hanya untuk menggantinya."))
        self.body.addWidget(self.form_widget)
        row = QHBoxLayout()
        self.new_button = self.button("Form perangkat baru", self.clear_form, row)
        self.save_button = self.button("Simpan perangkat", self.save, row)
        self.delete_button = self.button("Hapus perangkat", self.delete, row)
        self.refresh_button = self.button("Refresh", self.refresh, row)
        self.body.addLayout(row)
        row = QHBoxLayout()
        self.test_button = self.button("Uji koneksi", lambda: self.start_preview(test=True), row)
        self.preview_button = self.button("Mulai pratinjau terpilih", self.start_preview, row)
        self.stop_button = self.button("Hentikan semua", self.stop_previews, row)
        self.body.addLayout(row)
        self.body.addWidget(text_label(f"Maksimal {controller.config.camera_max_streams} kamera bersamaan. Untuk memilih beberapa perangkat, gunakan Cmd/Ctrl sambil memilih baris. Pratinjau berhenti saat berpindah halaman atau keluar akun."))
        self.preview_grid = QGridLayout()
        self.body.addLayout(self.preview_grid)
        self.body.addStretch()
        for widget in (self.name, self.rtsp):
            widget.textChanged.connect(self.controls)
        self.kind.currentIndexChanged.connect(self.kind_changed)
        self.location.currentIndexChanged.connect(self.controls)
        self.manager.changed.connect(self.camera_changed)
        self.manager.frame_ready.connect(self.show_frame)
        self.clear_form()

    def kind_changed(self):
        self.rtsp.clear()
        self.show_source.setChecked(False)
        self.controls()

    def controls(self):
        rtsp = self.kind.currentData() == DeviceType.RTSP.value
        self.rtsp.setEnabled(rtsp)
        self.show_source.setEnabled(rtsp)
        self.camera_index.setEnabled(not rtsp)
        preserved = bool(self.selected and self.selected.kind == DeviceType.RTSP and self.selected.has_source)
        valid = bool(self.name.text().strip() and self.location.currentData() and (not rtsp or self.rtsp.text() or preserved))
        self.save_button.setEnabled(not self.pending and valid)
        self.delete_button.setEnabled(not self.pending and self.selected is not None)
        selected = self.table.selectionModel().selectedRows()
        self.preview_button.setEnabled(not self.pending and bool(selected))
        self.test_button.setEnabled(not self.pending and len(selected) == 1)
        self.stop_button.setEnabled(self.manager.busy)
        self.rtsp.setPlaceholderText("Tersimpan; isi hanya untuk mengganti" if preserved else "rtsp://alamat-kamera:554/stream")

    def clear_form(self):
        self.selected = None
        self.table.clearSelection()
        self.name.clear()
        self.rtsp.clear()
        self.show_source.setChecked(False)
        self.kind.setCurrentIndex(0)
        self.camera_index.setValue(0)
        self.resolution.setCurrentIndex(1)
        self.fps.setValue(30)
        self.location.setCurrentIndex(0)
        self.controls()

    def select(self):
        index = self.table.currentRow()
        if not self.table.selectedItems() or not 0 <= index < len(self.rows):
            self.controls()
            return
        self.selected = row = self.rows[index]
        self.name.setText(row.name)
        self.kind.setCurrentIndex(self.kind.findData(row.kind.value))
        self.camera_index.setValue(row.camera_index or 0)
        self.resolution.setCurrentIndex(self.resolution.findData(row.resolution))
        self.fps.setValue(row.fps)
        self.location.setCurrentIndex(max(0,self.location.findData(row.location_id)))
        self.rtsp.clear()
        self.show_source.setChecked(False)
        self.controls()

    def reload(self):
        def display(result):
            self.rows = result.devices
            fill_table(self.table, [(d.name, {DeviceType.INTERNAL:"Bawaan", DeviceType.USB:"USB", DeviceType.RTSP:"RTSP"}[d.kind],
                d.rtsp_display + "…" if d.kind == DeviceType.RTSP else f"Kamera {d.camera_index}",
                d.resolution, d.fps, d.location_name) for d in self.rows])
            set_options(self.location, [(location.name,location.id) for location in result.locations], placeholder="Pilih lokasi")
            self.message.setText(f"{len(self.rows)} perangkat" if self.rows else "Belum ada perangkat. Tambahkan melalui formulir.")
        self.run(lambda service,token: service.list(token), display, loading=True)

    def refresh(self):
        self.stop_previews()
        super().refresh()

    def save(self):
        selected = self.selected
        if selected:
            self.manager.stop(selected.id)
        arguments = (self.name.text(), self.kind.currentData(), self.resolution.currentData(), self.fps.value(), self.location.currentData())
        options = dict(camera_index=self.camera_index.value(), rtsp_source=self.rtsp.text() or None,
            device_id=selected.id if selected else None, revision=selected.revision if selected else None)
        self.rtsp.clear()
        self.run(lambda service,token: service.save(token,*arguments,**options), self.changed)

    def delete(self):
        selected = self.selected
        if not selected:
            return
        def remove():
            self.manager.stop(selected.id)
            self.run(lambda service,token: service.delete(token,selected.id,selected.revision),self.changed)
        self.confirm("Hapus perangkat", f'Hapus “{selected.name}”? Perangkat dengan riwayat kehadiran tetap dilindungi.', remove)

    def start_preview(self, checked=False, *, test=False):
        device_ids = [self.rows[index.row()].id for index in self.table.selectionModel().selectedRows()]
        def start(specs):
            if not self.isVisible():
                return
            for device_id in tuple(self.cards):
                node = self.manager.nodes.get(device_id)
                if node is None or node.state in FINAL:
                    frame, unused_image, unused_status = self.cards.pop(device_id)
                    self.preview_grid.removeWidget(frame)
                    frame.deleteLater()
            for spec in specs:
                if spec.device_id not in self.cards:
                    frame = QFrame()
                    frame.setObjectName("featureCard")
                    body = QVBoxLayout(frame)
                    body.addWidget(text_label(spec.name,"sectionTitle"))
                    image = QLabel("Menghubungkan…")
                    image.setWordWrap(True)
                    image.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    image.setMinimumSize(240,160)
                    image.setMaximumHeight(280)
                    status = text_label("")
                    body.addWidget(image)
                    body.addWidget(status)
                    position = len(self.cards)
                    self.preview_grid.addWidget(frame,position//2,position%2)
                    self.cards[spec.device_id] = (frame,image,status)
            try:
                self.manager.start_many(specs,test=test)
            except DataValidationError as error:
                self.message.setText(str(error))
            self.controls()
        self.run(lambda service,token: service.sources(token,device_ids),start,loading=True)

    def camera_changed(self, device_id):
        if device_id in self.cards:
            node = self.manager.nodes[device_id]
            frame,image,status = self.cards[device_id]
            width,height = node.actual_size
            suffix = f" • {width}×{height} • {node.frames} frame diterima" if width else ""
            state_text = STATE_TEXT[node.state]
            if node.state == "failed" and node.spec.kind != DeviceType.RTSP.value:
                state_text = "Kamera lokal terputus atau tidak tersedia. Periksa perangkat dan nomor kamera, lalu mulai kembali secara manual."
            status.setText(state_text+suffix)
            if node.state != "streaming":
                image.setPixmap(QPixmap())
                image.setText(state_text)
        self.controls()

    def show_frame(self, device_id, frame):
        if device_id not in self.cards:
            return
        image = self.cards[device_id][1]
        if frame.isNull():
            image.setPixmap(QPixmap())
            image.setText("Menunggu frame baru…")
        elif self.isVisible():
            image.setPixmap(QPixmap.fromImage(frame).scaled(image.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

    def stop_previews(self):
        self.manager.stop_all()
        for unused,image,unused_status in self.cards.values():
            image.setPixmap(QPixmap())
            image.setText("Pratinjau dihentikan")
        self.controls()

    def on_leave(self):
        self.rtsp.clear()
        self.show_source.setChecked(False)
        self.stop_previews()
