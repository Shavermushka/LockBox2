# -*- coding: utf-8 -*-

"""
Модуль запуска приложения. Поддерживает несколько баз данных:
- При запуске открывается последняя использованная база (или предлагается создать/открыть).
- В главном окне есть меню «Файл» для создания/открытия других баз.
- При переключении базы приложение перезапускает сессию с новой базой.
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt6.QtCore import QTimer

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
        
        # Менеджеры
        self.crypto = None
        self.db = None
        self.main_window = None
        self.current_db_path = None
        
        # Таймер блокировки
        self.lock_timer = QTimer()
        self.lock_timer.timeout.connect(self.lock_app)
        self.lock_timer.setSingleShot(True)
        self.reset_lock_timer()
    
    def reset_lock_timer(self):
        """Сброс таймера бездействия."""
        timeout = self.settings.get("lock_timeout", 300)
        try:
            timeout = int(timeout)
        except (ValueError, TypeError):
            timeout = 300
        
        if timeout > 0:
            self.lock_timer.start(timeout * 1000)
        else:
            self.lock_timer.stop()
    
    def lock_app(self):
        """Блокировка приложения (закрытие окна, возврат к логину)."""
        logger.info("Автоматическая блокировка по бездействию")
        if self.main_window:
            self.main_window.hide()
            self.show_login()
    
    def show_login(self, db_path=None):
        """
        Показывает диалог ввода мастер-пароля для указанной базы.
        Если db_path не указан, используется текущий путь.
        """
        if db_path is None:
            db_path = self.current_db_path
        
        if not db_path:
            self.select_or_create_db()
            return
        
        login_dialog = LoginDialog()
        if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
            master_password = login_dialog.get_password()
            if master_password:
                self.init_with_password(master_password, db_path)
        else:
            sys.exit(0)
    
    def select_or_create_db(self):
        """Предлагает создать новую базу или открыть существующую."""
        reply = QMessageBox.question(
            None,
            "Выбор базы данных",
            "База данных не выбрана. Создать новую или открыть существующую?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.create_new_db()
        else:
            self.open_existing_db()
    
    def create_new_db(self):
        """Создание новой базы данных."""
        filepath, _ = QFileDialog.getSaveFileName(
            None,
            "Создать новую базу данных",
            str(Path.home() / "Documents" / "lockbox.db"),
            "Базы данных (*.db);;Все файлы (*)"
        )
        if not filepath:
            return
        
        if Path(filepath).exists():
            reply = QMessageBox.question(
                None,
                "Файл существует",
                f"Файл {filepath} уже существует. Перезаписать?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return self.create_new_db()
        
        login_dialog = LoginDialog(create_mode=True)
        if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
            return
        password = login_dialog.get_password()
        if not password:
            return
        
        try:
            self.init_with_password(password, filepath, is_new=True)
            self.settings.set_last_db_path(filepath)
            self.settings.sync()
            logger.info(f"Создана новая база: {filepath}")
        except Exception as e:
            logger.error(f"Ошибка создания базы: {e}", exc_info=True)
            QMessageBox.critical(None, "Ошибка", f"Не удалось создать базу: {e}")
            sys.exit(1)
    
    def open_existing_db(self):
        """Открыть существующую базу данных."""
        filepath, _ = QFileDialog.getOpenFileName(
            None,
            "Открыть базу данных",
            str(Path.home()),
            "Базы данных (*.db);;Все файлы (*)"
        )
        if not filepath:
            return
        
        if not Path(filepath).exists():
            QMessageBox.critical(None, "Ошибка", f"Файл {filepath} не найден.")
            return self.open_existing_db()
        
        self.show_login(filepath)
    
    def init_with_password(self, password, db_path, is_new=False):
        """Инициализация с мастер-паролем для указанной базы."""
        try:
            self.crypto = CryptoManager(password)
            self.current_db_path = db_path
            
            if is_new or not Path(db_path).exists():
                self.db = DatabaseManager(str(db_path), self.crypto)
                self.db.init_db()
                logger.info(f"Создана новая база: {db_path}")
            else:
                self.db = DatabaseManager(str(db_path), self.crypto)
                try:
                    self.db.get_all_entries()
                except Exception as e:
                    logger.error(f"Ошибка открытия базы: {e}", exc_info=True)
                    QMessageBox.critical(
                        None,
                        "Ошибка",
                        f"Не удалось открыть базу данных.\n"
                        f"Путь: {db_path}\n"
                        f"Причина: {str(e) if str(e) else 'неизвестная ошибка'}\n\n"
                        "Возможно, неверный пароль или база повреждена."
                    )
                    self.settings.set_last_db_path("")
                    self.settings.sync()
                    self.select_or_create_db()
                    return
            
            if self.main_window:
                self.main_window.close()
                self.main_window = None
            
            self.main_window = MainWindow(self.db, self.crypto, self.settings)
            self.main_window.show()
            self.main_window.activity_occurred.connect(self.reset_lock_timer)
            self.main_window.new_db_requested.connect(self.create_new_db)
            self.main_window.open_db_requested.connect(self.open_existing_db)
            
            self.settings.set_last_db_path(db_path)
            self.settings.sync()
            self.reset_lock_timer()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}", exc_info=True)
            QMessageBox.critical(None, "Ошибка", f"Не удалось инициализировать приложение: {e}")
            sys.exit(1)
    
    def run(self):
        """Запуск приложения."""
        last_db = self.settings.get_last_db_path()
        if last_db and Path(last_db).exists():
            self.show_login(last_db)
        else:
            self.select_or_create_db()
        
        sys.exit(self.app.exec())

def main():
    app = LockBoxApp()
    app.run()

if __name__ == "__main__":
    main()
