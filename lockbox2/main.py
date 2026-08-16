#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Точка входа в приложение LockBox Pro.
"""

import sys
import os
from pathlib import Path

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app import main

if __name__ == "__main__":
    main()
