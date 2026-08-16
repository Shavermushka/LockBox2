# -*- coding: utf-8 -*-

"""
Модуль для работы с TOTP (двухфакторные коды).
"""

import pyotp
import time
from typing import Optional

class TOTPManager:
    """Генерация и проверка TOTP кодов."""
    
    @staticmethod
    def generate_secret() -> str:
        """Генерация секрета для TOTP."""
        return pyotp.random_base32()
    
    @staticmethod
    def get_code(secret: str) -> str:
        """Получение текущего TOTP кода."""
        if not secret:
            return ""
        totp = pyotp.TOTP(secret)
        return totp.now()
    
    @staticmethod
    def get_remaining_time(secret: str) -> int:
        """Время до смены кода (в секундах)."""
        if not secret:
            return 0
        totp = pyotp.TOTP(secret)
        return totp.interval - (int(time.time()) % totp.interval)
    
    @staticmethod
    def verify(secret: str, code: str) -> bool:
        """Проверка кода."""
        if not secret or not code:
            return False
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    
    @staticmethod
    def get_otp_auth_url(secret: str, label: str = "LockBox") -> str:
        """Получение URL для настройки аутентификатора."""
        if not secret:
            return ""
        return pyotp.totp.TOTP(secret).provisioning_uri(label)
