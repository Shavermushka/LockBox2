# -*- coding: utf-8 -*-

"""
Диалог ввода мастер-пароля.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon

from .password_generator import PasswordGenerator

class LoginDialog(QDialog):
    """Диалог для ввода или создания мастер-пароля."""
    
    def __init__(self, create_mode=False, parent=None):
        super().__init__(parent)
        self.create_mode = create_mode
        self.password = None
        self.setWindowTitle("Создание мастер-пароля" if create_mode else "Вход в LockBox Pro")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setup_ui()
        if create_mode:
            self.setup_create_mode()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        self.label = QLabel("Введите мастер-пароль:" if not self.create_mode else "Создайте мастер-пароль:")
        layout.addWidget(self.label)
        
        # Поле пароля
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Введите пароль")
        self.password_edit.returnPressed.connect(self.accept_login)
        layout.addWidget(self.password_edit)
        
        # Показать/скрыть пароль
        self.show_action = QAction("Показать", self)
        self.show_action.setCheckable(True)
        self.show_action.toggled.connect(self.toggle_password_visibility)
        self.password_edit.addAction(self.show_action, QLineEdit.ActionPosition.TrailingPosition)
        
        if self.create_mode:
            # Поле подтверждения
            self.confirm_label = QLabel("Подтвердите пароль:")
            layout.addWidget(self.confirm_label)
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_edit.setPlaceholderText("Повторите пароль")
            layout.addWidget(self.confirm_edit)
            
            # Индикатор сложности
            self.strength_label = QLabel("Сложность: ")
            layout.addWidget(self.strength_label)
            
            # Прогрессбар сложности
            self.strength_bar = QProgressBar()
            self.strength_bar.setRange(0, 4)
            self.strength_bar.setValue(0)
            layout.addWidget(self.strength_bar)
            
            # Генератор пароля
            gen_layout = QHBoxLayout()
            self.gen_btn = QPushButton("Сгенерировать пароль")
            self.gen_btn.clicked.connect(self.generate_password)
            gen_layout.addStretch()
            gen_layout.addWidget(self.gen_btn)
            layout.addLayout(gen_layout)
            
            # Подключение сигналов для оценки сложности
            self.password_edit.textChanged.connect(self.check_strength)
            self.confirm_edit.textChanged.connect(self.check_strength)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept_login)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
    
    def setup_create_mode(self):
        """Дополнительная настройка для режима создания."""
        self.label.setText("Создайте надёжный мастер-пароль (минимум 8 символов):")
    
    def toggle_password_visibility(self, checked):
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_action.setText("Скрыть")
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_action.setText("Показать")
        if self.create_mode and hasattr(self, 'confirm_edit'):
            self.confirm_edit.setEchoMode(self.password_edit.echoMode())
    
    def check_strength(self):
        if not self.create_mode:
            return
        password = self.password_edit.text()
        if len(password) < 8:
            self.strength_label.setText("Сложность: слишком короткий")
            self.strength_bar.setValue(0)
            return
        score, feedback, label = PasswordGenerator.check_strength(password)
        self.strength_bar.setValue(score + 1)  # 1-5
        self.strength_label.setText(f"Сложность: {label} — {feedback}")
    
    def generate_password(self):
        if not self.create_mode:
            return
        pwd = PasswordGenerator.generate(length=20, use_upper=True, use_lower=True,
                                         use_digits=True, use_symbols=True)
        self.password_edit.setText(pwd)
        self.confirm_edit.setText(pwd)
        self.check_strength()
    
    def accept_login(self):
        password = self.password_edit.text()
        
        if self.create_mode:
            # Проверка сложности и совпадения
            if len(password) < 8:
                QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 8 символов.")
                return
            if password != self.confirm_edit.text():
                QMessageBox.warning(self, "Ошибка", "Пароли не совпадают.")
                return
            # Проверка сложности (не слишком слабый)
            score, _, _ = PasswordGenerator.check_strength(password)
            if score < 2:
                reply = QMessageBox.question(
                    self,
                    "Слабый пароль",
                    "Ваш пароль оценивается как слабый. Продолжить?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
        
        self.password = password
        self.accept()
    
    def get_password(self) -> str:
        return self.password
