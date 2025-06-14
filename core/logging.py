"""
Logging Manager
Menangani setup dan konfigurasi logging untuk bot
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

class LoggingManager:
    """Manager untuk sistem logging bot"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.max_bytes = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self._setup_done = False
    
    def setup_logging(self, level: int = logging.INFO) -> bool:
        """Setup konfigurasi logging dengan proper handling"""
        try:
            if self._setup_done:
                return True
                
            # Buat folder logs jika belum ada
            self.log_dir.mkdir(exist_ok=True)
            
            # Reset handler yang ada untuk mencegah duplikasi
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Setup formatter
            formatter = logging.Formatter(self.log_format)
            
            # File handler dengan rotasi
            file_handler = RotatingFileHandler(
                self.log_dir / 'bot.log',
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            
            # Setup root logger
            root_logger.setLevel(level)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            
            self._setup_done = True
            logging.info("Sistem logging berhasil diinisialisasi")
            return True
            
        except Exception as e:
            print(f"Gagal setup logging: {e}")
            return False
    
    def get_logger(self, name: str) -> logging.Logger:
        """Ambil logger dengan nama tertentu"""
        return logging.getLogger(name)
    
    def create_module_logger(self, module_name: str) -> logging.Logger:
        """Buat logger khusus untuk module"""
        logger = logging.getLogger(f"bot.{module_name}")
        return logger

# Instance global
logging_manager = LoggingManager()
