"""User management view; callbacks invoke the service authorization boundary."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from app.models.entities import Role
from app.widgets.cards import text_label


class UsersPage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.rows = []
        self.selected_id = None
        body = QVBoxLayout(self)
        body.setSpacing(14)
        body.addWidget(text_label("Pengguna", "pageTitle"))
        body.addWidget(text_label("Buat akun, ubah peran, atau nonaktifkan akses. Riwayat akun tetap disimpan."))
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Username", "Nama lengkap", "Peran", "Status"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._select)
        body.addWidget(self.table)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.username, self.fullname, self.password = QLineEdit(), QLineEdit(), QLineEdit()
        self.username.setMaxLength(80)
        self.fullname.setMaxLength(200)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("12–72 byte UTF-8; hanya untuk akun baru")
        self.role = QComboBox()
        for role in Role:
            self.role.addItem(role.value.replace("_", " ").title(), role.value)
        self.active = QCheckBox("Akun aktif")
        self.active.setChecked(True)
        form.addRow("Username", self.username)
        form.addRow("Nama lengkap", self.fullname)
        form.addRow("Peran", self.role)
        form.addRow("Password awal", self.password)
        form.addRow("Status", self.active)
        body.addLayout(form)
        buttons = QHBoxLayout()
        self.new_button = QPushButton("Form akun baru")
        self.save_button = QPushButton("Simpan pengguna")
        self.refresh_button = QPushButton("Muat ulang")
        self.reset_button = QPushButton("Reset password")
        for button in (self.new_button, self.save_button, self.refresh_button, self.reset_button):
            buttons.addWidget(button)
        body.addLayout(buttons)
        self.message = text_label("")
        body.addWidget(self.message)
        body.addStretch()
        self.new_button.clicked.connect(self.clear_form)
        self.save_button.clicked.connect(self.save)
        self.refresh_button.clicked.connect(controller.refresh_users)
        self.reset_button.clicked.connect(self.reset)
        self.clear_form()

    def clear_form(self):
        self.table.clearSelection()
        self.selected_id = None
        self.username.clear()
        self.fullname.clear()
        self.password.clear()
        self.password.setEnabled(True)
        self.active.setChecked(True)
        self.active.setEnabled(False)
        self.role.setCurrentIndex(self.role.findData(Role.VIEWER.value))
        self.reset_button.setEnabled(False)
        self.message.setText("Pengguna dapat mengganti password sendiri melalui menu Ganti password.")

    def _select(self):
        index = self.table.currentRow()
        if index < 0 or index >= len(self.rows) or not self.table.selectedItems():
            return
        user = self.rows[index]
        self.selected_id = user.id
        self.username.setText(user.username)
        self.fullname.setText(user.fullname)
        self.role.setCurrentIndex(self.role.findData(user.role.value))
        self.active.setChecked(user.is_active)
        self.active.setEnabled(True)
        self.password.clear()
        self.password.setEnabled(False)
        self.reset_button.setEnabled(user.id != self.controller.login.principal.id)
        self.message.setText("Hapus akses dengan menonaktifkan akun, kemudian simpan.")

    def display(self, rows):
        self.rows = rows
        self.table.setRowCount(0)
        self.table.setRowCount(len(rows))
        for index, user in enumerate(rows):
            for col, value in enumerate((user.username, user.fullname,
                user.role.value.replace("_", " "), "Aktif" if user.is_active else "Nonaktif")):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(index, col, item)
        self.table.resizeColumnsToContents()
        self.clear_form()

    def save(self):
        arguments = (self.username.text(), self.fullname.text(), self.role.currentData())
        if self.selected_id is None:
            password = self.password.text()
            self.password.clear()
            self.controller.create_user(*arguments, password)
        else:
            self.controller.update_user(self.selected_id, *arguments, self.active.isChecked())

    def reset(self):
        if self.selected_id is not None:
            self.controller.reset_user(self.selected_id)
