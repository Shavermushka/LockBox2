# -*- coding: utf-8 -*-

"""
Модуль криптографии. Обеспечивает шифрование/дешифрование данных
с использованием мастер-пароля и PBKDF2.
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

SALT_SIZE = 16
ITERATIONS = 100000

class CryptoManager:
    """Управление шифрованием на основе мастер-пароля."""
    
    def __init__(self, master_password: str, salt: bytes = None):
        """
        Инициализация.
        :param master_password: мастер-пароль (строка)
        :param salt: соль (bytes) — если None, генерируется новая
        """
        self.master_password = master_password.encode('utf-8')
        self.salt = salt if salt is not None else os.urandom(SALT_SIZE)
        self.key = self._derive_key(self.master_password, self.salt)
        self.fernet = Fernet(base64.urlsafe_b64encode(self.key))
    
    @staticmethod
    def _derive_key(password: bytes, salt: bytes) -> bytes:
        """Получение ключа из пароля и соли через PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password)
    
    def encrypt(self, data: str) -> bytes:
        """Шифрование строки."""
        if not data:
            return b''
        return self.fernet.encrypt(data.encode('utf-8'))
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Дешифрование байтов в строку."""
        if not encrypted_data:
            return ''
        return self.fernet.decrypt(encrypted_data).decode('utf-8')
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        """Шифрование байтов."""
        if not data:
            return b''
        return self.fernet.encrypt(data)
    
    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """Дешифрование байтов."""
        if not encrypted_data:
            return b''
        return self.fernet.decrypt(encrypted_data)
    
    def get_salt(self) -> bytes:
        """Возвращает соль (для сохранения)."""
        return self.salt
    
    @staticmethod
    def verify_password(master_password: str, stored_salt: bytes, stored_hash: bytes) -> bool:
        """
        Проверка пароля по соли и хешу.
        Используется для аутентификации при входе.
        """
        key = CryptoManager._derive_key(master_password.encode('utf-8'), stored_salt)
        # Для проверки используем хеш ключа (или можно зашифровать/расшифровать тестовую строку)
        # Простой способ: хешируем ключ и сравниваем
        test_hash = hashlib.sha256(key).digest()
        return test_hash == stored_hash
    
    @staticmethod
    def hash_key(key: bytes) -> bytes:
        """Хеш ключа для хранения."""
        return hashlib.sha256(key).digest()
