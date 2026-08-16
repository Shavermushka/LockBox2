# -*- coding: utf-8 -*-

"""
Модуль настроек приложения.
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QSpinBox, QPushButton, QFileDialog,
                             QCheckBox, QGroupBox, QFormLayout)
from PyQt6.QtCore import QSettings, Qt

class SettingsManager:
    """Управление настройками через QSettings."""
    
    def __init__(self):
        self.settings = QSettings("LockBox", "LockBox Pro")
    
    def get(self, key: str, default=None):
        return self.settings.value(key, default)
    
    def set(self, key: str, value):
        self.settings.setValue(key, value)
    
    def sync(self):
        self.settings.sync()

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
        
        # Группа темы
        theme_group = QGroupBox("Тема оформления")
        theme_layout = QFormLayout(theme_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        theme_layout.addRow("Тема:", self.theme_combo)
        layout.addWidget(theme_group)
        
        # Группа блокировки
        lock_group = QGroupBox("Автоматическая блокировка")
        lock_layout = QFormLayout(lock_group)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 3600)
        self.timeout_spin.setSuffix(" сек")
        self.timeout_spin.setToolTip("0 - отключить")
        lock_layout.addRow("Таймаут бездействия:", self.timeout_spin)
        layout.addWidget(lock_group)
        
        # Группа резервирования
        backup_group = QGroupBox("Резервное копирование")
        backup_layout = QFormLayout(backup_group)
        self.backup_check = QCheckBox("Создавать резервные копии при изменении")
        self.backup_check.setChecked(True)
        backup_layout.addRow(self.backup_check)
        layout.addWidget(backup_group)
        
        # Кнопки
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
        theme = self.settings.get("theme", "light")
        self.theme_combo.setCurrentIndex(0 if theme == "light" else 1)
        
        timeout = self.settings.get("lock_timeout", 300)
        self.timeout_spin.setValue(int(timeout))
        
        backup = self.settings.get("backup_enabled", True)
        self.backup_check.setChecked(backup in (True, "true", 1))
    
    def save_settings(self):
        theme = "light" if self.theme_combo.currentIndex() == 0 else "dark"
        self.settings.set("theme", theme)
        self.settings.set("lock_timeout", self.timeout_spin.value())
        self.settings.set("backup_enabled", self.backup_check.isChecked())
        self.settings.sync()
        self.accept()
