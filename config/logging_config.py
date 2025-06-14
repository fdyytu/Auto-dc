"""
Centralized Logging Configuration
Author: fdyytu
Created at: 2025-01-XX XX:XX:XX UTC

Konfigurasi logging terpusat untuk menghindari duplikasi dan konflik
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

class CentralizedLoggingManager:
    """Manager untuk sistem logging terpusat"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.log_dir = Path("logs")
            self.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            self.max_bytes = 10 * 1024 * 1024  # 10MB
            self.backup_count = 5
            self._setup_done = False
            CentralizedLoggingManager._initialized = True
    
    def setup_logging(self, level: int = logging.INFO) -> bool:
        """Setup konfigurasi logging terpusat"""
        if self._setup_done:
            return True
            
        try:
            # Buat folder logs jika belum ada
            self.log_dir.mkdir(exist_ok=True)
            
            # Reset semua handler yang ada untuk mencegah duplikasi
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Setup formatter
            formatter = logging.Formatter(self.log_format)
            
            # File handler dengan rotasi - HANYA SATU FILE LOG
            file_handler = RotatingFileHandler(
                self.log_dir / 'bot.log',
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(level)
            
            # Setup root logger
            root_logger.setLevel(level)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            
            # Disable propagation untuk logger khusus yang mungkin membuat duplikasi
            discord_logger = logging.getLogger('discord')
            discord_logger.propagate = True  # Biarkan propagate ke root logger
            
            self._setup_done = True
            logging.info("Sistem logging terpusat berhasil diinisialisasi")
            return True
            
        except Exception as e:
            print(f"Gagal setup logging terpusat: {e}")
            return False
    
    def get_logger(self, name: str) -> logging.Logger:
        """Ambil logger dengan nama tertentu"""
        if not self._setup_done:
            self.setup_logging()
        return logging.getLogger(name)
    
    def create_module_logger(self, module_name: str) -> logging.Logger:
        """Buat logger khusus untuk module"""
        if not self._setup_done:
            self.setup_logging()
        logger = logging.getLogger(f"bot.{module_name}")
        return logger

# Instance global singleton
logging_manager = CentralizedLoggingManager()

def get_logger(name: str) -> logging.Logger:
    """Helper function untuk mendapatkan logger"""
    return logging_manager.get_logger(name)

def setup_centralized_logging(level: int = logging.INFO) -> bool:
    """Helper function untuk setup logging"""
    return logging_manager.setup_logging(level)
