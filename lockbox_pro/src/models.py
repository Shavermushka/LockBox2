# -*- coding: utf-8 -*-

"""
Модуль моделей данных для записей паролей.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PasswordEntry:
    """Модель записи пароля."""
    id: Optional[int] = None
    title: str = ""
    username: str = ""
    password: str = ""
    url: str = ""
    notes: str = ""
    totp_secret: str = ""  # секрет для TOTP (если есть)
    created_at: str = ""   # ISO формат
    updated_at: str = ""   # ISO формат
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def update_timestamp(self):
        """Обновляет время изменения."""
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для экспорта."""
        return {
            "id": self.id,
            "title": self.title,
            "username": self.username,
            "password": self.password,
            "url": self.url,
            "notes": self.notes,
            "totp_secret": self.totp_secret,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PasswordEntry':
        """Создание из словаря."""
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            url=data.get("url", ""),
            notes=data.get("notes", ""),
            totp_secret=data.get("totp_secret", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )
