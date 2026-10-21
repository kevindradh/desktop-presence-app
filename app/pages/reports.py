"""Explicit report snapshots, local pagination and cancellable worker exports."""
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (QComboBox,QDateEdit,QFileDialog,QFormLayout,QHBoxLayout,QLineEdit,
    QProgressBar,QPushButton,QVBoxLayout,QWidget)

from app.exports.attendance import HEADERS,display_row,export_report,metadata
from app.pages.administration import fill_table,table
from app.services.auth import AuthError
from app.services.database import DataValidationError,DatabaseUnavailable
from app.services.reports import ReportFilter,STATUS,period_range
from app.services.tasks import TaskController
from app.widgets.cards import text_label


@dataclass(frozen=True)
class ReportResult:
    value: object=None
    error: str=''


class ReportsPage(QWidget):
    PAGE_SIZE=50

    def __init__(self,controller):
        super().__init__()
        self.controller=controller
        self.snapshot=None
        self.offset=0
        self.generation=0
        self.exporting=False
        self.tasks=TaskController(controller.reporter,self)
        self.tasks.succeeded.connect(self.completed)
        self.tasks.settled.connect(self.controls)
        self.tasks.cancelled.connect(self.cancelled)
        layout=QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(text_label('Laporan berdasarkan tanggal kerja. Ekspor memuat seluruh hasil filter yang sudah ditampilkan, termasuk halaman berikutnya.','muted'))
        self.period=QComboBox()
        for label,key in (('Harian','DAILY'),('Mingguan (Senin sampai Minggu)','WEEKLY'),('Bulanan','MONTHLY'),('Rentang khusus','CUSTOM')):
            self.period.addItem(label,key)
        self.start=QDateEdit();self.end=QDateEdit()
        today=controller.reports_service.clock().astimezone(controller.reports_service.zone).date()
        for field in (self.start,self.end):
            field.setCalendarPopup(True);field.setDisplayFormat('dd/MM/yyyy');field.setKeyboardTracking(False)
            field.setDate(QDate(today.year,today.month,today.day))
        self.group=QComboBox();self.group.addItem('Semua grup',None)
        self.shift=QComboBox();self.shift.addItem('Semua shift',None)
        self.member=QLineEdit();self.member.setMaxLength(200);self.member.setPlaceholderText('Cari ID atau nama anggota')
        self.status_filter=QComboBox();self.status_filter.addItem('Semua status','ALL')
        self.status_filter.addItem('Hadir (termasuk terlambat)','ATTENDED')
        for key,label in STATUS.items():self.status_filter.addItem(label,key)
        forms=QHBoxLayout()
        for entries in ((('Periode',self.period),('Dari',self.start),('Sampai',self.end),('Anggota',self.member)),
                        (('Grup',self.group),('Shift',self.shift),('Status',self.status_filter))):
            form=QFormLayout()
            for label,field in entries:form.addRow(label,field)
            forms.addLayout(form,1)
        layout.addLayout(forms)
        buttons=QHBoxLayout()
        self.load_button=QPushButton('Tampilkan laporan');self.load_button.setProperty('variant','primary')
        self.xlsx_button=QPushButton('Ekspor Excel');self.pdf_button=QPushButton('Ekspor PDF');self.cancel_button=QPushButton('Batalkan proses')
        for button in (self.load_button,self.xlsx_button,self.pdf_button,self.cancel_button):buttons.addWidget(button)
        layout.addLayout(buttons)
        self.message=text_label('Pilih filter, lalu tampilkan laporan.');layout.addWidget(self.message)
        self.summary=text_label('','muted');layout.addWidget(self.summary)
        self.progress=QProgressBar();self.progress.setRange(0,100);self.progress.setValue(0);layout.addWidget(self.progress)
        self.tasks.progress.connect(self.progress.setValue)
        self.table=table(HEADERS);layout.addWidget(self.table)
        pages=QHBoxLayout()
        self.previous=QPushButton('Sebelumnya');self.next=QPushButton('Berikutnya');self.page_label=text_label('Belum ada laporan')
        pages.addWidget(self.previous);pages.addWidget(self.page_label,1);pages.addWidget(self.next);layout.addLayout(pages)
        self.load_button.clicked.connect(self.load)
        self.xlsx_button.clicked.connect(lambda:self.export('xlsx'))
        self.pdf_button.clicked.connect(lambda:self.export('pdf'))
        self.cancel_button.clicked.connect(self.tasks.cancel)
        self.previous.clicked.connect(lambda:self.move(-self.PAGE_SIZE));self.next.clicked.connect(lambda:self.move(self.PAGE_SIZE))
        self.period.currentIndexChanged.connect(self.period_changed)
        self.start.dateChanged.connect(self.period_changed)
        self.end.dateChanged.connect(self.changed)
        for combo in (self.group,self.shift,self.status_filter):combo.currentIndexChanged.connect(self.changed)
        self.member.textChanged.connect(self.changed)
        self.end.setEnabled(False)
        self.controls()

    @property
    def busy(self):return self.tasks.busy

    @property
    def pending(self):return self.busy

    def controls(self):
        ready=self.snapshot is not None and not self.busy
        self.load_button.setEnabled(not self.busy)
        self.xlsx_button.setEnabled(ready);self.pdf_button.setEnabled(ready)
        self.cancel_button.setEnabled(self.busy)
        self.previous.setEnabled(ready and self.offset>0)
        self.next.setEnabled(ready and self.offset+self.PAGE_SIZE<len(self.snapshot.rows))
        for field in (self.period,self.start,self.group,self.shift,self.member,self.status_filter):
            field.setEnabled(not (self.exporting and self.busy))
        self.end.setEnabled(self.period.currentData()=='CUSTOM' and not (self.exporting and self.busy))

    def changed(self):
        self.generation+=1
        self.snapshot=None
        self.table.setRowCount(0);self.summary.clear();self.page_label.setText('Filter berubah. Tampilkan laporan kembali.')
        self.message.setText('Filter berubah. Tampilkan laporan kembali sebelum ekspor.')
        if self.busy:self.tasks.cancel()
        self.controls()

    def period_changed(self):
        if self.period.currentData()!='CUSTOM':
            start,end=period_range(self.period.currentData(),self.start.date().toPyDate())
            for field,value in ((self.start,start),(self.end,end)):
                field.blockSignals(True);field.setDate(QDate(value.year,value.month,value.day));field.blockSignals(False)
        self.changed()

    def filters(self):
        return ReportFilter(self.start.date().toPyDate(),self.end.date().toPyDate(),self.group.currentData(),
                            self.member.text(),self.shift.currentData(),self.status_filter.currentData())

    def run(self,operation,callback,*,exporting=False):
        c=self.controller
        if self.busy or c._closing or not c.login:return
        self.exporting=exporting
        self.request=(c.login.token,self.generation,callback)
        token=c.login.token
        self.progress.setValue(0)
        def work(context):
            try:return ReportResult(operation(token,context))
            except (AuthError,DataValidationError,DatabaseUnavailable) as error:return ReportResult(error=str(error))
        self.tasks.start(work)
        self.controls()

    def completed(self,result):
        token,generation,callback=self.request
        c=self.controller
        if not c.login or c.login.token!=token or generation!=self.generation or c._closing:return
        if result.error:
            c._handle_denial(result.error)
        else:callback(result.value)

    def reload(self):
        # Navigation loads filter options once; it never silently changes a report.
        if self.group.count()>1 or self.busy:return
        def loaded(options):
            for combo,rows in zip((self.group,self.shift),options):
                combo.blockSignals(True)
                for key,label in rows:combo.addItem(label,key)
                combo.blockSignals(False)
        self.run(lambda token,context:self.controller.reports_service.options(token),loaded)

    def load(self):
        filters=self.filters()
        def loaded(snapshot):
            self.snapshot=snapshot;self.offset=0
            self.message.setText('Laporan ditampilkan. Ekspor menggunakan seluruh hasil ini sampai laporan dimuat ulang.')
            self.summary.setText('\n'.join(metadata(snapshot)))
            self.render()
        self.run(lambda token,context:self.controller.reports_service.build(token,filters,context),loaded)

    def render(self):
        if self.snapshot is None:return
        total=len(self.snapshot.rows)
        fill_table(self.table,[display_row(row,self.snapshot.zone) for row in self.snapshot.rows[self.offset:self.offset+self.PAGE_SIZE]])
        for col in range(self.table.columnCount()):self.table.setColumnWidth(col,min(260,max(110,self.table.columnWidth(col))))
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):self.table.item(row,col).setToolTip(self.table.item(row,col).text())
        self.page_label.setText(f'{self.offset+1 if total else 0}–{min(self.offset+self.PAGE_SIZE,total)} dari {total} baris')
        self.controls()

    def move(self,amount):
        if self.snapshot is None or self.busy:return
        self.offset=max(0,min(self.offset+amount,max(0,len(self.snapshot.rows)-1)))
        self.render()

    def export(self,kind):
        if self.snapshot is None or self.busy:return
        path,_=QFileDialog.getSaveFileName(self,'Simpan laporan',f'StarGate-{self.snapshot.filters.start}-{self.snapshot.filters.end}.{kind}',
                                        'Excel (*.xlsx)' if kind=='xlsx' else 'PDF (*.pdf)')
        if not path:return
        if not Path(path).suffix:path+='.'+kind
        key=self.snapshot.id
        overwrite=Path(path).exists()  # Native save dialog confirms overwrite first.
        def saved(result):
            self.message.setText(f'Ekspor selesai: {result.rows} baris. File: {Path(result.path).name}')
            self.message.setToolTip(result.path)
        self.run(lambda token,context:export_report(self.controller.reports_service,token,key,path,kind,context,overwrite=overwrite),saved,exporting=True)

    def cancelled(self):
        self.message.setText('Ekspor dibatalkan. File akhir tidak dibuat.' if self.exporting else 'Pemuatan laporan dibatalkan.')

    def on_leave(self):
        self.generation+=1
        self.tasks.cancel()

    def hideEvent(self,event):
        self.on_leave()
        super().hideEvent(event)

    def showEvent(self,event):
        super().showEvent(event)
        self.reload()
