# -*- coding: utf-8 -*-

"""
Модуль генератора паролей и оценки сложности.
"""

import secrets
import string
import re
from typing import Tuple

# Пытаемся импортировать zxcvbn (может быть установлен как zxcvbn или zxcvbn-python)
try:
    import zxcvbn
    # Проверяем, есть ли функция zxcvbn
    if hasattr(zxcvbn, 'zxcvbn'):
        ZXCVBN_AVAILABLE = True
    else:
        ZXCVBN_AVAILABLE = False
except ImportError:
    ZXCVBN_AVAILABLE = False

class PasswordGenerator:
    """Генератор паролей с настройками."""
    
    DEFAULT_LENGTH = 16
    DEFAULT_USE_UPPER = True
    DEFAULT_USE_LOWER = True
    DEFAULT_USE_DIGITS = True
    DEFAULT_USE_SYMBOLS = True
    DEFAULT_EXCLUDE_SIMILAR = False
    
    SIMILAR_CHARS = "il1Lo0O"
    
    @classmethod
    def generate(cls, length: int = DEFAULT_LENGTH,
                 use_upper: bool = DEFAULT_USE_UPPER,
                 use_lower: bool = DEFAULT_USE_LOWER,
                 use_digits: bool = DEFAULT_USE_DIGITS,
                 use_symbols: bool = DEFAULT_USE_SYMBOLS,
                 exclude_similar: bool = DEFAULT_EXCLUDE_SIMILAR) -> str:
        """
        Генерация пароля.
        """
        if length < 1:
            length = 1
        
        chars = ""
        if use_upper:
            chars += string.ascii_uppercase
        if use_lower:
            chars += string.ascii_lowercase
        if use_digits:
            chars += string.digits
        if use_symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?/~"
        
        if not chars:
            chars = string.ascii_lowercase
        
        if exclude_similar:
            for ch in cls.SIMILAR_CHARS:
                chars = chars.replace(ch, "")
        
        password = ''.join(secrets.choice(chars) for _ in range(length))
        return password
    
    @classmethod
    def check_strength(cls, password: str) -> Tuple[float, str, str]:
        """
        Оценка сложности пароля.
        Возвращает (score, feedback, label).
        score: 0-4 (0 - очень слабый, 4 - очень сильный)
        """
        if not password:
            return 0, "Пароль пуст", "Очень слабый"
        
        if ZXCVBN_AVAILABLE:
            try:
                # Правильный вызов функции zxcvbn
                result = zxcvbn.zxcvbn(password)
                score = result['score']  # 0-4
                feedback = result.get('feedback', {}).get('warning', '')
                if not feedback:
                    if score >= 3:
                        feedback = "Отличный пароль!"
                    elif score == 2:
                        feedback = "Неплохой, но можно улучшить"
                    else:
                        feedback = "Слабый пароль, используйте более сложный"
                labels = ["Очень слабый", "Слабый", "Средний", "Сильный", "Очень сильный"]
                return score, feedback, labels[score]
            except Exception:
                # Если что-то пошло не так с zxcvbn, используем fallback
                pass
        
        # Fallback: простая энтропия
        entropy = cls._estimate_entropy(password)
        if entropy < 30:
            score = 0
            label = "Очень слабый"
            feedback = "Слишком короткий или простой"
        elif entropy < 40:
            score = 1
            label = "Слабый"
            feedback = "Можно улучшить, добавив символы"
        elif entropy < 60:
            score = 2
            label = "Средний"
            feedback = "Неплохо, но можно сильнее"
        elif entropy < 80:
            score = 3
            label = "Сильный"
            feedback = "Хороший пароль"
        else:
            score = 4
            label = "Очень сильный"
            feedback = "Отличный пароль!"
        return score, feedback, label
    
    @classmethod
    def _estimate_entropy(cls, password: str) -> float:
        """Оценка энтропии (для случая без zxcvbn)."""
        length = len(password)
        char_set_size = 0
        if re.search(r'[a-z]', password):
            char_set_size += 26
        if re.search(r'[A-Z]', password):
            char_set_size += 26
        if re.search(r'[0-9]', password):
            char_set_size += 10
        if re.search(r'[^a-zA-Z0-9]', password):
            char_set_size += 32
        if char_set_size == 0:
            return 0
        return length * (char_set_size.bit_length())
