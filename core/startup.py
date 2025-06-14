"""
Startup Manager
Menangani prosedur startup dan dependency checking
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class StartupManager:
    """Manager untuk prosedur startup bot"""
    
    def __init__(self):
        self.required_packages = {
            'discord.py': 'discord',
            'aiohttp': 'aiohttp',
            'sqlite3': 'sqlite3',
            'asyncio': 'asyncio'
        }
        self.optional_packages = {
            'PyNaCl': 'nacl'  # Untuk voice support
        }
        self.required_dirs = ['logs', 'ext', 'utils', 'cogs', 'data', 'temp', 'backups']
    
    def check_dependencies(self) -> bool:
        """Cek apakah semua dependency yang diperlukan terinstall"""
        missing = []
        
        for package, import_name in self.required_packages.items():
            try:
                __import__(import_name)
                logger.debug(f"✓ {package} tersedia")
            except ImportError:
                missing.append(package)
                logger.error(f"✗ {package} tidak ditemukan")
        
        # Cek optional packages
        for package, import_name in self.optional_packages.items():
            try:
                __import__(import_name)
                logger.info(f"✓ {package} tersedia (opsional)")
            except ImportError:
                logger.warning(f"⚠ {package} tidak ditemukan (opsional)")
        
        if missing:
            logger.critical(f"Package yang hilang: {', '.join(missing)}")
            logger.critical("Install dengan: pip install " + ' '.join(missing))
            return False
        
        logger.info("Semua dependency tersedia")
        return True
    
    def setup_project_structure(self) -> bool:
        """Buat struktur direktori dan file yang diperlukan"""
        try:
            for directory in self.required_dirs:
                dir_path = Path(directory)
                dir_path.mkdir(exist_ok=True)
                
                # Buat __init__.py untuk Python packages
                init_file = dir_path / '__init__.py'
                if not init_file.exists():
                    init_file.touch()
                
                logger.debug(f"✓ Direktori {directory} siap")
            
            logger.info("Struktur project berhasil disiapkan")
            return True
            
        except Exception as e:
            logger.error(f"Gagal setup struktur project: {e}")
            return False
    
    def check_permissions(self) -> bool:
        """Cek permission untuk direktori yang diperlukan"""
        try:
            current_dir = Path.cwd()
            
            # Cek write permission
            if not os.access(current_dir, os.W_OK):
                logger.error(f"Tidak ada write permission untuk: {current_dir}")
                return False
            
            # Cek read permission
            if not os.access(current_dir, os.R_OK):
                logger.error(f"Tidak ada read permission untuk: {current_dir}")
                return False
            
            logger.info("Permission check berhasil")
            return True
            
        except Exception as e:
            logger.error(f"Error saat cek permission: {e}")
            return False
    
    def run_startup_checks(self) -> bool:
        """Jalankan semua startup checks"""
        logger.info("Memulai startup checks...")
        
        checks = [
            ("Permission Check", self.check_permissions),
            ("Dependency Check", self.check_dependencies),
            ("Project Structure", self.setup_project_structure)
        ]
        
        for check_name, check_func in checks:
            logger.info(f"Menjalankan {check_name}...")
            if not check_func():
                logger.critical(f"{check_name} gagal!")
                return False
        
        logger.info("Semua startup checks berhasil")
        return True

# Instance global
startup_manager = StartupManager()
