# -*- coding: utf-8 -*-

"""
Главное окно приложения.
"""

import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QLineEdit, QLabel, QMessageBox, QHeaderView,
                             QMenu, QToolBar, QStatusBar, QFileDialog,
                             QApplication, QStyle)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSettings
from PyQt6.QtGui import QAction, QIcon, QColor

from .database import DatabaseManager
from .crypto import CryptoManager
from .models import PasswordEntry
from .password_dialog import PasswordDialog
from .settings_dialog import SettingsDialog
from .export_import import ExportImportManager
from .totp import TOTPManager
from .tray_icon import TrayIcon
from .password_generator import PasswordGenerator

class MainWindow(QMainWindow):
    """Главное окно."""
    
    activity_occurred = pyqtSignal()
    
    def __init__(self, db: DatabaseManager, crypto: CryptoManager, settings):
        super().__init__()
        self.db = db
        self.crypto = crypto
        self.settings = settings
        self.entries = []
        self.tray = None
        self.setup_ui()
        self.load_entries()
        self.setup_tray()
        self.apply_theme()
    
    def setup_ui(self):
        self.setWindowTitle("LockBox Pro")
        self.setGeometry(100, 100, 900, 600)
        
        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Верхняя панель: поиск + кнопки
        top_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск...")
        self.search_edit.textChanged.connect(self.search)
        top_layout.addWidget(self.search_edit)
        
        self.btn_add = QPushButton("➕ Добавить")
        self.btn_add.clicked.connect(self.add_entry)
        top_layout.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("✏️ Редактировать")
        self.btn_edit.clicked.connect(self.edit_entry)
        top_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("🗑️ Удалить")
        self.btn_delete.clicked.connect(self.delete_entry)
        top_layout.addWidget(self.btn_delete)
        
        self.btn_export = QPushButton("📤 Экспорт")
        self.btn_export.clicked.connect(self.export_data)
        top_layout.addWidget(self.btn_export)
        
        self.btn_import = QPushButton("📥 Импорт")
        self.btn_import.clicked.connect(self.import_data)
        top_layout.addWidget(self.btn_import)
        
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setFixedWidth(30)
        self.btn_settings.clicked.connect(self.open_settings)
        top_layout.addWidget(self.btn_settings)
        
        layout.addLayout(top_layout)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Название", "Логин", "Пароль", "URL", "TOTP", "Изменено"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemDoubleClicked.connect(self.edit_entry)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table)
        
        # Статусбар
        self.statusBar().showMessage("Готово")
        
        # Тулбар для TOTP
        self.totp_timer = QTimer()
        self.totp_timer.timeout.connect(self.update_totp_display)
        self.totp_timer.start(1000)  # обновление каждую секунду
    
    def setup_tray(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = TrayIcon(self)
            self.tray.show()
    
    def apply_theme(self):
        theme = self.settings.get("theme", "light")
        style_path = os.path.join(os.path.dirname(__file__), "resources", "styles", f"{theme}.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            # Базовые стили
            if theme == "dark":
                self.setStyleSheet("""
                    QMainWindow { background: #2b2b2b; color: #eee; }
                    QTableWidget { background: #3c3c3c; color: #eee; gridline-color: #555; }
                    QHeaderView::section { background: #2b2b2b; color: #eee; }
                    QLineEdit, QPushButton { background: #3c3c3c; color: #eee; border: 1px solid #555; }
                """)
            else:
                self.setStyleSheet("")
    
    def load_entries(self):
        try:
            self.entries = self.db.get_all_entries()
            self.display_entries(self.entries)
            self.statusBar().showMessage(f"Записей: {len(self.entries)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить записи: {e}")
    
    def display_entries(self, entries):
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.title))
            self.table.setItem(row, 1, QTableWidgetItem(entry.username))
            self.table.setItem(row, 2, QTableWidgetItem("•" * min(len(entry.password), 8)))
            self.table.setItem(row, 3, QTableWidgetItem(entry.url))
            
            # TOTP код
            totp_item = QTableWidgetItem("")
            if entry.totp_secret:
                try:
                    code = TOTPManager.get_code(entry.totp_secret)
                    totp_item.setText(code)
                except:
                    pass
            self.table.setItem(row, 4, totp_item)
            
            self.table.setItem(row, 5, QTableWidgetItem(entry.updated_at[:16]))
    
    def search(self):
        query = self.search_edit.text().strip()
        if query:
            filtered = self.db.search_entries(query)
            self.display_entries(filtered)
        else:
            self.display_entries(self.entries)
    
    def add_entry(self):
        dialog = PasswordDialog()
        if dialog.exec() == PasswordDialog.DialogCode.Accepted:
            entry = dialog.get_entry()
            try:
                self.db.add_entry(entry)
                self.load_entries()
                self.statusBar().showMessage("Запись добавлена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {e}")
    
    def edit_entry(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Информация", "Выберите запись для редактирования.")
            return
        entry_id = self.entries[row].id
        entry = self.db.get_entry_by_id(entry_id)
        if not entry:
            QMessageBox.critical(self, "Ошибка", "Запись не найдена.")
            return
        dialog = PasswordDialog(entry)
        if dialog.exec() == PasswordDialog.DialogCode.Accepted:
            updated = dialog.get_entry()
            try:
                self.db.update_entry(updated)
                self.load_entries()
                self.statusBar().showMessage("Запись обновлена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись: {e}")
    
    def delete_entry(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Информация", "Выберите запись для удаления.")
            return
        entry = self.entries[row]
        reply = QMessageBox.question(self, "Подтверждение",
                                     f"Удалить запись '{entry.title}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_entry(entry.id)
                self.load_entries()
                self.statusBar().showMessage("Запись удалена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись: {e}")
    
    def show_context_menu(self, pos):
        row = self.table.currentRow()
        if row < 0:
            return
        entry = self.entries[row]
        menu = QMenu()
        copy_user = menu.addAction("Копировать логин")
        copy_pass = menu.addAction("Копировать пароль")
        copy_totp = menu.addAction("Копировать TOTP код")
        menu.addSeparator()
        edit_act = menu.addAction("Редактировать")
        delete_act = menu.addAction("Удалить")
        
        action = menu.exec(self.table.mapToGlobal(pos))
        if action == copy_user:
            QApplication.clipboard().setText(entry.username)
            self.statusBar().showMessage("Логин скопирован")
        elif action == copy_pass:
            QApplication.clipboard().setText(entry.password)
            self.statusBar().showMessage("Пароль скопирован")
        elif action == copy_totp:
            if entry.totp_secret:
                code = TOTPManager.get_code(entry.totp_secret)
                QApplication.clipboard().setText(code)
                self.statusBar().showMessage("TOTP код скопирован")
            else:
                QMessageBox.information(self, "Информация", "TOTP не настроен")
        elif action == edit_act:
            self.edit_entry()
        elif action == delete_act:
            self.delete_entry()
    
    def update_totp_display(self):
        """Обновление TOTP кодов в таблице."""
        for row, entry in enumerate(self.entries):
            if entry.totp_secret:
                try:
                    code = TOTPManager.get_code(entry.totp_secret)
                    self.table.item(row, 4).setText(code)
                except:
                    pass
    
    def export_data(self):
        format_choice = QMessageBox.question(
            self, "Экспорт", "Экспортировать в JSON? (Нажмите No для CSV, Cancel для XML)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        if format_choice == QMessageBox.StandardButton.Cancel:
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить экспорт",
            "",
            "JSON (*.json);;CSV (*.csv);;XML (*.xml)"
        )
        if not filepath:
            return
        
        try:
            entries = self.db.get_all_entries()
            if format_choice == QMessageBox.StandardButton.Yes:
                ExportImportManager.export_json(entries, filepath)
            elif format_choice == QMessageBox.StandardButton.No:
                ExportImportManager.export_csv(entries, filepath)
            else:
                ExportImportManager.export_xml(entries, filepath)
            self.statusBar().showMessage(f"Экспорт завершён: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать: {e}")
    
    def import_data(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл для импорта",
            "",
            "JSON (*.json);;CSV (*.csv);;XML (*.xml)"
        )
        if not filepath:
            return
        
        try:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.json':
                entries = ExportImportManager.import_json(filepath)
            elif ext == '.csv':
                entries = ExportImportManager.import_csv(filepath)
            elif ext == '.xml':
                entries = ExportImportManager.import_xml(filepath)
            else:
                QMessageBox.warning(self, "Ошибка", "Неподдерживаемый формат")
                return
            
            # Добавляем записи в базу
            for entry in entries:
                # Генерируем новые ID
                entry.id = None
                entry.created_at = None
                entry.updated_at = None
                self.db.add_entry(entry)
            
            self.load_entries()
            self.statusBar().showMessage(f"Импортировано {len(entries)} записей")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать: {e}")
    
    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self.apply_theme()
            # Обновляем таймер блокировки (сигнал от родительского приложения)
            self.activity_occurred.emit()
    
    def closeEvent(self, event):
        """При закрытии скрываем в трей, если он есть."""
        if self.tray and self.tray.isVisible():
            self.hide()
            event.ignore()
        else:
            if self.tray:
                self.tray.hide()
            event.accept()
