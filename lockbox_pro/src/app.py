# -*- coding: utf-8 -*-

"""
Модуль запуска приложения. Создаёт экземпляр QApplication,
проверяет наличие базы, запрашивает мастер-пароль и инициализирует главное окно.
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, QSettings

from .crypto import CryptoManager
from .database import DatabaseManager
from .login_dialog import LoginDialog
from .main_window import MainWindow
from .settings_dialog import SettingsManager

# Настройка логирования
LOG_DIR = Path.home() / ".lockbox_pro"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "lockbox.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LockBoxApp:
    """Главный класс приложения."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("LockBox Pro")
        self.app.setOrganizationName("LockBox")
        
        # Загрузка настроек
        self.settings = SettingsManager()
        
        # Путь к базе данных
        self.db_path = Path.home() / ".lockbox_pro" / "lockbox.db"
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Менеджеры
        self.crypto = None
        self.db = None
        self.main_window = None
        
        # Таймер блокировки
        self.lock_timer = QTimer()
        self.lock_timer.timeout.connect(self.lock_app)
        self.lock_timer.setSingleShot(True)
        self.reset_lock_timer()
    
    def reset_lock_timer(self):
        """Сброс таймера бездействия."""
        timeout = self.settings.get("lock_timeout", 300)  # секунды
        if timeout > 0:
            self.lock_timer.start(timeout * 1000)
        else:
            self.lock_timer.stop()
    
    def lock_app(self):
        """Блокировка приложения (закрытие окна, возврат к логину)."""
        logger.info("Автоматическая блокировка по бездействию")
        if self.main_window:
            self.main_window.hide()
            # Показываем диалог логина повторно
            self.show_login()
    
    def show_login(self):
        """Показывает диалог ввода мастер-пароля."""
        login_dialog = LoginDialog()
        if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
            master_password = login_dialog.get_password()
            if master_password:
                self.init_with_password(master_password)
        else:
            # Выход, если отмена
            sys.exit(0)
    
    def init_with_password(self, password):
        """Инициализация с мастер-паролем."""
        try:
            # Инициализируем крипто-менеджер
            self.crypto = CryptoManager(password)
            
            # Проверяем, существует ли база
            if self.db_path.exists():
                # Проверяем возможность расшифровки заголовка
                try:
                    self.db = DatabaseManager(str(self.db_path), self.crypto)
                    # Проверяем, что база не повреждена
                    self.db.get_all_entries()
                except Exception as e:
                    logger.error(f"Ошибка открытия базы: {e}")
                    QMessageBox.critical(None, "Ошибка", "Не удалось открыть базу данных. Возможно, неверный пароль или база повреждена.")
                    sys.exit(1)
            else:
                # Создаём новую базу
                self.db = DatabaseManager(str(self.db_path), self.crypto)
                self.db.init_db()
                logger.info("Создана новая база данных")
            
            # Открываем главное окно
            self.main_window = MainWindow(self.db, self.crypto, self.settings)
            self.main_window.show()
            
            # Соединяем сигнал сброса таймера
            self.main_window.activity_occurred.connect(self.reset_lock_timer)
            
            # Запускаем таймер
            self.reset_lock_timer()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            QMessageBox.critical(None, "Ошибка", f"Не удалось инициализировать приложение: {e}")
            sys.exit(1)
    
    def run(self):
        """Запуск приложения."""
        # При первом запуске проверяем, есть ли база
        if not self.db_path.exists():
            # Нет базы — предлагаем создать мастер-пароль
            reply = QMessageBox.question(
                None,
                "Новая база данных",
                "База данных не найдена. Создать новую базу с мастер-паролем?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # Показываем диалог создания мастер-пароля (используем LoginDialog в режиме создания)
                login_dialog = LoginDialog(create_mode=True)
                if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
                    password = login_dialog.get_password()
                    if password:
                        self.init_with_password(password)
                    else:
                        sys.exit(0)
                else:
                    sys.exit(0)
            else:
                sys.exit(0)
        else:
            # База существует — запрашиваем пароль
            self.show_login()
        
        # Запускаем цикл событий
        sys.exit(self.app.exec())

def main():
    """Точка входа."""
    app = LockBoxApp()
    app.run()

if __name__ == "__main__":
    main()
