# -*- coding: utf-8 -*-

"""
Модуль экспорта/импорта данных в форматы JSON, CSV, XML.
"""

import json
import csv
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from .models import PasswordEntry
from .database import DatabaseManager
from .crypto import CryptoManager

logger = logging.getLogger(__name__)

class ExportImportManager:
    """Экспорт и импорт данных."""
    
    @staticmethod
    def export_json(entries: List[PasswordEntry], filepath: str, encrypt: bool = False, crypto: CryptoManager = None):
        """Экспорт в JSON."""
        data = [entry.to_dict() for entry in entries]
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if encrypt and crypto:
            encrypted = crypto.encrypt(json_str)
            with open(filepath, 'wb') as f:
                f.write(encrypted)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        logger.info(f"Экспорт JSON: {filepath}")
    
    @staticmethod
    def import_json(filepath: str, crypto: CryptoManager = None) -> List[PasswordEntry]:
        """Импорт из JSON."""
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Пытаемся расшифровать, если передан crypto
        if crypto:
            try:
                json_str = crypto.decrypt(content)
            except:
                # Возможно, файл не зашифрован
                json_str = content.decode('utf-8')
        else:
            json_str = content.decode('utf-8')
        
        data = json.loads(json_str)
        entries = [PasswordEntry.from_dict(item) for item in data]
        logger.info(f"Импорт JSON: {filepath}, записей: {len(entries)}")
        return entries
    
    @staticmethod
    def export_csv(entries: List[PasswordEntry], filepath: str):
        """Экспорт в CSV."""
        fieldnames = ['id', 'title', 'username', 'password', 'url', 'notes', 'totp_secret', 'created_at', 'updated_at']
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry.to_dict())
        logger.info(f"Экспорт CSV: {filepath}")
    
    @staticmethod
    def import_csv(filepath: str) -> List[PasswordEntry]:
        """Импорт из CSV."""
        entries = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = PasswordEntry.from_dict(row)
                entries.append(entry)
        logger.info(f"Импорт CSV: {filepath}, записей: {len(entries)}")
        return entries
    
    @staticmethod
    def export_xml(entries: List[PasswordEntry], filepath: str):
        """Экспорт в XML."""
        root = ET.Element("entries")
        for entry in entries:
            entry_elem = ET.SubElement(root, "entry")
            for key, value in entry.to_dict().items():
                if value is not None:
                    child = ET.SubElement(entry_elem, key)
                    child.text = str(value)
        
        # Форматируем XML
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        logger.info(f"Экспорт XML: {filepath}")
    
    @staticmethod
    def import_xml(filepath: str) -> List[PasswordEntry]:
        """Импорт из XML."""
        tree = ET.parse(filepath)
        root = tree.getroot()
        entries = []
        for entry_elem in root.findall('entry'):
            data = {}
            for child in entry_elem:
                data[child.tag] = child.text
            entry = PasswordEntry.from_dict(data)
            entries.append(entry)
        logger.info(f"Импорт XML: {filepath}, записей: {len(entries)}")
        return entries
