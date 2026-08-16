# -*- coding: utf-8 -*-

"""
Модуль настроек приложения.
Добавлены методы для сохранения/загрузки пути к последней базе.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QSpinBox, QPushButton, QCheckBox, QGroupBox, QFormLayout)
from PyQt6.QtCore import QSettings

class SettingsManager:
    """Управление настройками через QSettings."""
    
    def __init__(self):
        self.settings = QSettings("LockBox", "LockBox Pro")
        self.settings.setValue("theme", "dark")  # всегда тёмная
    
    def get(self, key: str, default=None):
        return self.settings.value(key, default)
    
    def set(self, key: str, value):
        self.settings.setValue(key, value)
    
    def sync(self):
        self.settings.sync()
    
    def get_last_db_path(self):
        return self.get("last_db_path", "")
    
    def set_last_db_path(self, path: str):
        self.set("last_db_path", path)
        self.sync()

class SettingsDialog(QDialog):
    """Диалог настроек."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = SettingsManager()
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        lock_group = QGroupBox("Автоматическая блокировка")
        lock_layout = QFormLayout(lock_group)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 3600)
        self.timeout_spin.setSuffix(" сек")
        self.timeout_spin.setToolTip("0 - отключить")
        lock_layout.addRow("Таймаут бездействия:", self.timeout_spin)
        layout.addWidget(lock_group)
        
        backup_group = QGroupBox("Резервное копирование")
        backup_layout = QFormLayout(backup_group)
        self.backup_check = QCheckBox("Создавать резервные копии при изменении")
        self.backup_check.setChecked(True)
        backup_layout.addRow(self.backup_check)
        layout.addWidget(backup_group)
        
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
    
    def load_settings(self):
        timeout = self.settings.get("lock_timeout", 300)
        try:
            timeout = int(timeout)
        except (ValueError, TypeError):
            timeout = 300
        self.timeout_spin.setValue(timeout)
        backup = self.settings.get("backup_enabled", True)
        self.backup_check.setChecked(backup in (True, "true", 1))
    
    def save_settings(self):
        self.settings.set("lock_timeout", self.timeout_spin.value())
        self.settings.set("backup_enabled", self.backup_check.isChecked())
        self.settings.sync()
        self.accept()
