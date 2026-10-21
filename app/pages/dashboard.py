"""Visible-only, single-flight polling. Never recreates forms or takes focus."""
from dataclasses import dataclass

from PyQt6.QtCore import QDate, QTimer
from PyQt6.QtWidgets import QCheckBox, QDateEdit, QFrame, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from app.pages.administration import fill_table, table
from app.services.attendance import EVENTS
from app.services.auth import AuthError
from app.services.database import DatabaseUnavailable, DataValidationError
from app.services.tasks import TaskController
from app.widgets.attendance_chart import AttendanceChart
from app.widgets.cards import text_label


@dataclass(frozen=True)
class DashboardResult:
    data: object = None
    error: str = ''
    denied: bool = False


class DashboardPage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.setObjectName('attendanceDashboard')
        self.controller = controller
        self.snapshot = None
        self.generation = 0
        self.again = False
        self.tasks = TaskController(controller.reporter, self)
        self.tasks.succeeded.connect(self.loaded)
        self.tasks.settled.connect(self.settled)
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.refresh)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        row = QHBoxLayout()
        row.addWidget(text_label('Tanggal kerja'))
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat('dd/MM/yyyy')
        self.date.setDate(QDate.currentDate())
        self.date.setAccessibleName('Tanggal kerja dashboard')
        row.addWidget(self.date)
        self.today = QCheckBox('Ikuti hari ini')
        self.today.setChecked(True)
        row.addWidget(self.today)
        row.addStretch()
        layout.addLayout(row)
        summary = QFrame()
        summary.setObjectName('dashboardSummary')
        summary_body = QVBoxLayout(summary)
        summary_body.setContentsMargins(22, 20, 22, 20)
        summary_body.setSpacing(18)
        attendance = QVBoxLayout()
        attendance.addWidget(text_label('Hadir', 'sectionTitle'))
        present = text_label('...', 'dashboardTotal')
        present.setAccessibleName('Jumlah anggota hadir')
        attendance.addWidget(present)
        summary_body.addLayout(attendance)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        self.counters = {'present': present}
        for i, (key, title, description) in enumerate((
                ('late', 'Terlambat', 'Bagian dari jumlah Hadir.'),
                ('pending', 'Belum masuk', 'Anggota terjadwal yang belum check-in sebelum shift berakhir.'),
                ('absent', 'Tidak hadir', 'Anggota terjadwal yang belum check-in setelah shift berakhir (Absent).'),
                ('on_leave', 'Izin', 'Anggota terjadwal yang belum check-in dan memiliki catatan izin.'),
                ('registered', 'Anggota aktif', 'Jumlah anggota yang aktif saat ini, terlepas dari tanggal yang dipilih.'))):
            title_label = text_label(title, 'muted')
            title_label.setToolTip(description)
            value = text_label('...', 'cardTitle')
            value.setAccessibleName('Jumlah '+title.lower())
            value.setToolTip(description)
            self.counters[key] = value
            grid.addWidget(title_label, 0, i)
            grid.addWidget(value, 1, i)
            grid.setColumnStretch(i, 1)
        summary_body.addLayout(grid)
        layout.addWidget(summary)
        self.status = text_label('Memuat ringkasan kehadiran...', 'muted')
        layout.addWidget(self.status)
        self.warning = text_label('')
        self.warning.hide()
        layout.addWidget(self.warning)
        layout.addWidget(text_label('Aktivitas terbaru', 'sectionTitle'))
        layout.addWidget(text_label('Maksimal 20 catatan pada tanggal kerja yang dipilih.', 'muted'))
        self.feed_empty = text_label('Belum ada aktivitas pada tanggal kerja ini.', 'muted')
        self.feed_empty.hide()
        layout.addWidget(self.feed_empty)
        self.feed = table(['Waktu', 'Nama', 'ID anggota', 'Aktivitas', 'Shift', 'Perangkat', 'Sumber'])
        self.feed.setMinimumHeight(220)
        layout.addWidget(self.feed)
        layout.addWidget(text_label('Pola kehadiran', 'sectionTitle'))
        layout.addWidget(text_label('Hijau menunjukkan Hadir. Jingga menunjukkan Terlambat, yang termasuk dalam Hadir.', 'muted'))
        charts = QGridLayout()
        self.charts = {}
        for i, (key, title, description) in enumerate((
                ('shifts', 'Per shift', 'Maksimal 12 shift dengan kehadiran terbanyak.'),
                ('groups', 'Per grup', 'Maksimal 12 grup dengan kehadiran terbanyak.'),
                ('daily', '30 hari terakhir', 'Jumlah anggota hadir setiap tanggal kerja.'),
                ('monthly', '12 bulan terakhir', 'Total hari hadir anggota setiap bulan.'))):
            card = QFrame()
            card.setObjectName('featureCard')
            body = QVBoxLayout(card)
            body.setContentsMargins(18, 16, 18, 16)
            body.addWidget(text_label(title, 'sectionTitle'))
            body.addWidget(text_label(description, 'muted'))
            chart = AttendanceChart(trend=key in ('daily', 'monthly'))
            chart.set_rows((), empty_text='Menunggu data kehadiran...')
            self.charts[key] = chart
            body.addWidget(chart)
            charts.addWidget(card, i//2, i%2)
        layout.addLayout(charts)
        self.date.dateChanged.connect(self.date_changed)
        self.today.toggled.connect(self.follow_changed)

    @property
    def busy(self):
        return self.tasks.busy

    @property
    def pending(self):
        return self.busy

    def date_changed(self):
        self.today.blockSignals(True)
        self.today.setChecked(False)
        self.today.blockSignals(False)
        self.generation += 1
        self.clear()
        self.reload()

    def follow_changed(self):
        self.generation += 1
        self.reload()

    def reload(self):
        if self.busy:
            self.again = True
        else:
            self.refresh()

    def refresh(self):
        c = self.controller
        if not self.isVisible() or c._closing or not c.login or c.stack.currentWidget() is not c.shell:
            return
        if self.today.isChecked():
            day = c.dashboard_service.clock().astimezone(c.dashboard_service.zone).date()
            wanted = QDate(day.year, day.month, day.day)
            if self.date.date() != wanted:
                self.date.blockSignals(True)
                self.date.setDate(wanted)
                self.date.blockSignals(False)
                self.generation += 1
                self.clear()
        if self.busy:
            return
        day = self.date.date().toPyDate()
        if self.snapshot is None:
            self.status.setText('Memuat ringkasan kehadiran...')
        token, generation = c.login.token, self.generation
        self.request = (token, generation, day)
        def work(context):
            try:
                return DashboardResult(c.dashboard_service.load(token, day))
            except AuthError as error:
                return DashboardResult(error=str(error), denied=True)
            except (DatabaseUnavailable, DataValidationError) as error:
                return DashboardResult(error=str(error))
        self.tasks.start(work)

    def loaded(self, result):
        c = self.controller
        token, generation, day = self.request
        if not c.login or c.login.token != token or self.generation != generation or not self.isVisible() or c._closing:
            return
        if result.error:
            self.status.setText('Data belum diperbarui. '+result.error)
            if self.snapshot is None:
                for chart in self.charts.values():
                    chart.set_rows((), empty_text='Data kehadiran belum tersedia.')
            if result.denied:
                self.clear()
                c._handle_denial(result.error)
            return
        data = result.data
        old = self.snapshot
        self.snapshot = data
        for key, value in self.counters.items():
            value.setText(str(getattr(data, key)))
        self.status.setText('Diperbarui otomatis • '+data.updated.astimezone(c.dashboard_service.zone).strftime('%d/%m/%Y %H:%M:%S')+
                            ' • Zona '+str(c.dashboard_service.zone))
        self.warning.setText(f'Periksa penugasan: {data.conflicts} anggota memiliki jadwal bertumpang tindih. Anggota tersebut belum dihitung dalam Izin, Tidak hadir, atau Belum masuk.' if data.conflicts else '')
        self.warning.setVisible(bool(data.conflicts))
        self.feed_empty.setVisible(not data.activity)
        if old is None or old.activity != data.activity:
            scroll = self.feed.verticalScrollBar().value()
            fill_table(self.feed, [(entry.timestamp.astimezone(c.dashboard_service.zone).strftime('%d/%m %H:%M:%S'),
                entry.name, entry.code, EVENTS[entry.event], entry.shift, entry.device,
                'Otomatis' if entry.automatic else 'Scan') for entry in data.activity])
            self.feed.verticalScrollBar().setValue(scroll)
        for key, chart in self.charts.items():
            chart.set_rows(getattr(data, key))

    def clear(self):
        self.snapshot = None
        for value in self.counters.values():
            value.setText('...')
        self.status.setText('Memuat ringkasan kehadiran...')
        self.feed_empty.hide()
        self.feed.setRowCount(0)
        for chart in self.charts.values():
            chart.set_rows((), empty_text='Menunggu data kehadiran...')
        self.warning.hide()

    def settled(self):
        if self.again:
            self.again = False
            self.refresh()

    def on_leave(self):
        self.generation += 1
        self.again = False
        self.timer.stop()
        self.tasks.cancel()

    def hideEvent(self, event):
        self.on_leave()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.timer.start()
        self.reload()
