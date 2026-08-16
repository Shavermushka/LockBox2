# -*- coding: utf-8 -*-

"""
Модуль работы с SQLite базой данных.
Все данные хранятся в зашифрованном виде.
"""

import sqlite3
import base64
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import PasswordEntry
from .crypto import CryptoManager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Управление базой данных."""
    
    def __init__(self, db_path: str, crypto: CryptoManager):
        self.db_path = db_path
        self.crypto = crypto
        self.conn = None
        self._init_connection()
    
    def _init_connection(self):
        """Создание соединения с БД."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # Включаем поддержку внешних ключей
        self.conn.execute("PRAGMA foreign_keys = ON;")
    
    def init_db(self):
        """Создание таблиц, если их нет."""
        cursor = self.conn.cursor()
        # Таблица записей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                username TEXT,
                password TEXT,
                url TEXT,
                notes TEXT,
                totp_secret TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Таблица метаданных (для хранения соли и хеша пароля)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self.conn.commit()
        logger.info("База данных инициализирована")
    
    def _encrypt_field(self, value: str) -> str:
        """Шифрование поля (возвращает base64-строку)."""
        if not value:
            return ""
        encrypted = self.crypto.encrypt(value)
        return base64.b64encode(encrypted).decode('ascii')
    
    def _decrypt_field(self, encrypted_b64: str) -> str:
        """Дешифрование поля из base64-строки."""
        if not encrypted_b64:
            return ""
        encrypted = base64.b64decode(encrypted_b64.encode('ascii'))
        return self.crypto.decrypt(encrypted)
    
    def _encrypt_entry(self, entry: PasswordEntry) -> Dict[str, Any]:
        """Шифрование всех полей записи (кроме id, created_at, updated_at)."""
        return {
            "title": self._encrypt_field(entry.title),
            "username": self._encrypt_field(entry.username),
            "password": self._encrypt_field(entry.password),
            "url": self._encrypt_field(entry.url),
            "notes": self._encrypt_field(entry.notes),
            "totp_secret": self._encrypt_field(entry.totp_secret),
            "created_at": entry.created_at,
            "updated_at": entry.updated_at
        }
    
    def _decrypt_entry(self, row: sqlite3.Row) -> PasswordEntry:
        """Дешифрование записи из строки БД."""
        return PasswordEntry(
            id=row['id'],
            title=self._decrypt_field(row['title']),
            username=self._decrypt_field(row['username']),
            password=self._decrypt_field(row['password']),
            url=self._decrypt_field(row['url']),
            notes=self._decrypt_field(row['notes']),
            totp_secret=self._decrypt_field(row['totp_secret']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def add_entry(self, entry: PasswordEntry) -> int:
        """Добавление новой записи. Возвращает ID."""
        encrypted = self._encrypt_entry(entry)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO entries (title, username, password, url, notes, totp_secret, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            encrypted['title'], encrypted['username'], encrypted['password'],
            encrypted['url'], encrypted['notes'], encrypted['totp_secret'],
            encrypted['created_at'], encrypted['updated_at']
        ))
        self.conn.commit()
        entry_id = cursor.lastrowid
        logger.info(f"Добавлена запись ID={entry_id}")
        self._backup_db()
        return entry_id
    
    def update_entry(self, entry: PasswordEntry):
        """Обновление записи."""
        encrypted = self._encrypt_entry(entry)
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE entries
            SET title=?, username=?, password=?, url=?, notes=?, totp_secret=?, updated_at=?
            WHERE id=?
        """, (
            encrypted['title'], encrypted['username'], encrypted['password'],
            encrypted['url'], encrypted['notes'], encrypted['totp_secret'],
            encrypted['updated_at'], entry.id
        ))
        self.conn.commit()
        logger.info(f"Обновлена запись ID={entry.id}")
        self._backup_db()
    
    def delete_entry(self, entry_id: int):
        """Удаление записи."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM entries WHERE id=?", (entry_id,))
        self.conn.commit()
        logger.info(f"Удалена запись ID={entry_id}")
        self._backup_db()
    
    def get_all_entries(self) -> List[PasswordEntry]:
        """Получение всех записей."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entries ORDER BY title COLLATE NOCASE")
        rows = cursor.fetchall()
        return [self._decrypt_entry(row) for row in rows]
    
    def get_entry_by_id(self, entry_id: int) -> Optional[PasswordEntry]:
        """Получение записи по ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entries WHERE id=?", (entry_id,))
        row = cursor.fetchone()
        if row:
            return self._decrypt_entry(row)
        return None
    
    def search_entries(self, query: str) -> List[PasswordEntry]:
        """
        Поиск записей по названию, логину, URL.
        Поиск осуществляется после дешифрования (все записи загружаются).
        """
        all_entries = self.get_all_entries()
        query_lower = query.lower()
        results = []
        for entry in all_entries:
            if (query_lower in entry.title.lower() or
                query_lower in entry.username.lower() or
                query_lower in entry.url.lower()):
                results.append(entry)
        return results
    
    def save_metadata(self, key: str, value: str):
        """Сохранение метаданных."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()
    
    def get_metadata(self, key: str) -> Optional[str]:
        """Получение метаданных."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key=?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else None
    
    def change_master_password(self, new_crypto: CryptoManager):
        """
        Смена мастер-пароля: перешифрование всех записей.
        """
        entries = self.get_all_entries()
        # Сохраняем старый крипто-менеджер
        old_crypto = self.crypto
        self.crypto = new_crypto
        
        # Перешифровываем все записи
        for entry in entries:
            encrypted = self._encrypt_entry(entry)
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE entries
                SET title=?, username=?, password=?, url=?, notes=?, totp_secret=?
                WHERE id=?
            """, (
                encrypted['title'], encrypted['username'], encrypted['password'],
                encrypted['url'], encrypted['notes'], encrypted['totp_secret'],
                entry.id
            ))
        self.conn.commit()
        logger.info("Мастер-пароль изменён, все данные перешифрованы")
        self._backup_db()
    
    def _backup_db(self):
        """Создание резервной копии базы."""
        backup_dir = Path(self.db_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"lockbox_backup_{timestamp}.db"
        # Копируем файл
        import shutil
        shutil.copy2(self.db_path, backup_file)
        logger.info(f"Создана резервная копия: {backup_file}")
        # Оставляем только последние 10 копий
        backups = sorted(backup_dir.glob("lockbox_backup_*.db"))
        if len(backups) > 10:
            for old in backups[:-10]:
                old.unlink()
    
    def close(self):
        """Закрытие соединения."""
        if self.conn:
            self.conn.close()
