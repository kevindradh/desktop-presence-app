"""Explicit audit filtering; no automatic reload while editing."""
from datetime import datetime, time, timedelta
import json
from zoneinfo import ZoneInfo
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QDateEdit, QFormLayout, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget
from app.pages.administration import table, fill_table
from app.services.audit import AuditFilter
from app.widgets.cards import text_label


class AuditPage(QWidget):
    def __init__(self, controller):
        super().__init__(); self.controller=controller; self.pending=False; self.offset=0; self.more=False
        self.zone=ZoneInfo(controller.config.timezone)
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        layout.addWidget(text_label('Aktivitas penting tersimpan sebagai jejak audit. Rentang tanggal inklusif; detail tidak memuat kata sandi atau data wajah.','muted'))
        self.start=QDateEdit(); self.end=QDateEdit()
        today=QDate.currentDate()
        for field in (self.start,self.end):
            field.setCalendarPopup(True); field.setDate(today); field.setDisplayFormat('dd/MM/yyyy'); field.setKeyboardTracking(False)
        self.action=QLineEdit(); self.action.setMaxLength(80); self.action.setPlaceholderText('Contoh: auth.login; kosong = semua')
        self.actor=QLineEdit(); self.actor.setMaxLength(80); self.actor.setPlaceholderText('Username persis; kosong = semua')
        form=QFormLayout()
        for name,field in (('Dari',self.start),('Sampai',self.end),('Kode aktivitas',self.action),('Username',self.actor)): form.addRow(name,field)
        layout.addLayout(form)
        self.load_button=QPushButton('Tampilkan audit'); self.load_button.clicked.connect(lambda:self.load(0)); layout.addWidget(self.load_button)
        self.message=text_label('Pilih filter, lalu tampilkan audit.'); layout.addWidget(self.message)
        self.table=table(('ID','Waktu','Pelaku','Aktivitas','Entitas','ID entitas','Detail')); layout.addWidget(self.table)
        row=QHBoxLayout(); self.previous=QPushButton('Sebelumnya'); self.next=QPushButton('Berikutnya')
        self.previous.clicked.connect(lambda:self.load(max(0,self.offset-100))); self.next.clicked.connect(lambda:self.load(self.offset+100))
        row.addWidget(self.previous); row.addWidget(self.next); layout.addLayout(row)
        self.previous.setEnabled(False); self.next.setEnabled(False)
        for field in (self.start,self.end):field.dateChanged.connect(self.changed)
        self.action.textChanged.connect(self.changed); self.actor.textChanged.connect(self.changed)
        self.generation=0

    @property
    def busy(self):return self.pending

    def changed(self):
        self.generation+=1; self.table.setRowCount(0); self.previous.setEnabled(False); self.next.setEnabled(False)
        self.message.setText('Filter berubah. Tampilkan audit kembali.')

    def load(self,offset):
        c=self.controller
        if self.pending or not c.login:return
        start=datetime.combine(self.start.date().toPyDate(),time.min,self.zone)
        end=datetime.combine(self.end.date().toPyDate()+timedelta(days=1),time.min,self.zone)
        filters=AuditFilter(start,end,self.action.text().strip(),self.actor.text().strip(),offset)
        generation=self.generation; token=c.login.token
        self.pending=True; self.load_button.setEnabled(False); self.next.setEnabled(False); self.previous.setEnabled(False)
        def done(result):
            self.pending=False; self.load_button.setEnabled(True)
            if not c.login or c.login.token!=token or generation!=self.generation:return
            if result.error:c._handle_denial(result.error); return
            rows,more=result.value; self.offset=offset; self.more=more
            fill_table(self.table,[(rid,stamp.astimezone(self.zone).strftime('%d/%m/%Y %H:%M:%S'),actor,action,entity,eid or '-',json.dumps(details,ensure_ascii=False)) for rid,stamp,actor,action,entity,eid,details in rows])
            self.message.setText(f'{len(rows)} aktivitas ditampilkan; urutan terbaru. Mulai baris {offset+1}.')
            self.previous.setEnabled(offset>0); self.next.setEnabled(more)
        if not c.jobs.run(lambda:c.audit_service.read(token,filters),done,blocks_ui=True):
            self.pending=False; self.load_button.setEnabled(True)

    def reload(self):pass
    def on_leave(self):self.generation+=1
