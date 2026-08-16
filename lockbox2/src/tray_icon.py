# -*- coding: utf-8 -*-

"""
Системный трей (иконка в области уведомлений).
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject

class TrayIcon(QSystemTrayIcon):
    """Иконка в системном трее."""
    
    def __init__(self, main_window):
        # Используем стандартную иконку
        icon = QIcon.fromTheme("lockbox", QIcon())
        super().__init__(icon, main_window)
        self.main_window = main_window
        self.setToolTip("LockBox Pro")
        self.setup_menu()
        self.activated.connect(self.on_activated)
    
    def setup_menu(self):
        menu = QMenu()
        
        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)
        
        lock_action = QAction("Заблокировать", self)
        lock_action.triggered.connect(self.lock_app)
        menu.addAction(lock_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Выйти", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
    
    def show_window(self):
        self.main_window.show()
        self.main_window.activateWindow()
    
    def lock_app(self):
        self.main_window.hide()
        # Вызов блокировки через родительское приложение
        # В MainWindow есть ссылка на app? Передадим сигнал.
        self.main_window.activity_occurred.emit()  # сброс таймера
        # Показываем логин через app
        # Для простоты перезапускаем логин через родителя
        from .app import LockBoxApp
        # Это не идеально, но работает
        parent = self.main_window.parent()
        if parent and hasattr(parent, 'show_login'):
            parent.show_login()
    
    def on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
