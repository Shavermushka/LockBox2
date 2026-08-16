# -*- coding: utf-8 -*-

"""
Диалог добавления/редактирования записи пароля.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QTextEdit, QPushButton,
                             QCheckBox, QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt

from .models import PasswordEntry
from .password_generator import PasswordGenerator
from .totp import TOTPManager

class PasswordDialog(QDialog):
    """Диалог для добавления/редактирования записи."""
    
    def __init__(self, entry: PasswordEntry = None, parent=None):
        super().__init__(parent)
        self.entry = entry if entry else PasswordEntry()
        self.is_edit = entry is not None
        self.setWindowTitle("Редактирование записи" if self.is_edit else "Новая запись")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_entry()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title_edit = QLineEdit()
        form.addRow("Название:", self.title_edit)
        self.username_edit = QLineEdit()
        form.addRow("Логин:", self.username_edit)
        pwd_layout = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_layout.addWidget(self.password_edit)
        self.show_pwd_btn = QPushButton("👁")
        self.show_pwd_btn.setCheckable(True)
        self.show_pwd_btn.toggled.connect(self.toggle_password_visibility)
        self.show_pwd_btn.setFixedWidth(30)
        pwd_layout.addWidget(self.show_pwd_btn)
        self.gen_pwd_btn = QPushButton("Генератор")
        self.gen_pwd_btn.clicked.connect(self.show_generator)
        pwd_layout.addWidget(self.gen_pwd_btn)
        form.addRow("Пароль:", pwd_layout)
        self.url_edit = QLineEdit()
        form.addRow("URL:", self.url_edit)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        form.addRow("Заметки:", self.notes_edit)
        totp_layout = QHBoxLayout()
        self.totp_edit = QLineEdit()
        self.totp_edit.setPlaceholderText("Секрет TOTP (base32)")
        totp_layout.addWidget(self.totp_edit)
        self.totp_gen_btn = QPushButton("Сгенерировать секрет")
        self.totp_gen_btn.clicked.connect(self.generate_totp_secret)
        totp_layout.addWidget(self.totp_gen_btn)
        form.addRow("TOTP секрет:", totp_layout)
        if self.is_edit:
            self.created_label = QLabel(self.entry.created_at)
            form.addRow("Создано:", self.created_label)
            self.updated_label = QLabel(self.entry.updated_at)
            form.addRow("Изменено:", self.updated_label)
        layout.addLayout(form)
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.save_entry)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
    
    def toggle_password_visibility(self, checked):
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_pwd_btn.setText("🙈")
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_pwd_btn.setText("👁")
    
    def show_generator(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Генератор пароля")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        length_spin = QSpinBox()
        length_spin.setRange(4, 128)
        length_spin.setValue(16)
        form.addRow("Длина:", length_spin)
        use_upper = QCheckBox("Заглавные")
        use_upper.setChecked(True)
        form.addRow(use_upper)
        use_lower = QCheckBox("Строчные")
        use_lower.setChecked(True)
        form.addRow(use_lower)
        use_digits = QCheckBox("Цифры")
        use_digits.setChecked(True)
        form.addRow(use_digits)
        use_symbols = QCheckBox("Символы")
        use_symbols.setChecked(True)
        form.addRow(use_symbols)
        exclude_sim = QCheckBox("Исключить похожие")
        exclude_sim.setChecked(False)
        form.addRow(exclude_sim)
        layout.addLayout(form)
        result_label = QLabel("Сгенерированный пароль:")
        result_edit = QLineEdit()
        result_edit.setReadOnly(True)
        layout.addWidget(result_label)
        layout.addWidget(result_edit)
        gen_btn = QPushButton("Сгенерировать")
        def generate():
            pwd = PasswordGenerator.generate(
                length=length_spin.value(),
                use_upper=use_upper.isChecked(),
                use_lower=use_lower.isChecked(),
                use_digits=use_digits.isChecked(),
                use_symbols=use_symbols.isChecked(),
                exclude_similar=exclude_sim.isChecked()
            )
            result_edit.setText(pwd)
        gen_btn.clicked.connect(generate)
        use_btn = QPushButton("Использовать")
        def use_password():
            self.password_edit.setText(result_edit.text())
            dialog.accept()
        use_btn.clicked.connect(use_password)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(gen_btn)
        btn_layout.addWidget(use_btn)
        layout.addLayout(btn_layout)
        generate()
        dialog.exec()
    
    def generate_totp_secret(self):
        secret = TOTPManager.generate_secret()
        self.totp_edit.setText(secret)
        QMessageBox.information(self, "TOTP", f"Сгенерирован секрет: {secret}\nСохраните его в аутентификаторе.")
    
    def load_entry(self):
        if self.is_edit:
            self.title_edit.setText(self.entry.title)
            self.username_edit.setText(self.entry.username)
            self.password_edit.setText(self.entry.password)
            self.url_edit.setText(self.entry.url)
            self.notes_edit.setPlainText(self.entry.notes)
            self.totp_edit.setText(self.entry.totp_secret)
    
    def save_entry(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Название обязательно.")
            return
        self.entry.title = title
        self.entry.username = self.username_edit.text()
        self.entry.password = self.password_edit.text()
        self.entry.url = self.url_edit.text()
        self.entry.notes = self.notes_edit.toPlainText()
        self.entry.totp_secret = self.totp_edit.text()
        self.entry.update_timestamp()
        self.accept()
    
    def get_entry(self) -> PasswordEntry:
        return self.entry
