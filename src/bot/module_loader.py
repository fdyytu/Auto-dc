"""
Module Loader untuk Discord Bot
Memuat modul sesuai urutan yang ditentukan dalam ANALISIS_URUTAN_PEMUATAN.md
"""

import os
import sys
import asyncio
import logging
import importlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class ModuleLoader:
    """Class untuk memuat modul bot sesuai urutan yang benar"""
    
    def __init__(self, bot):
        self.bot = bot
        self.loaded_modules = []
        self.failed_modules = []
        
        # Urutan pemuatan sesuai ANALISIS_URUTAN_PEMUATAN.md
        self.loading_order = [
            'utils',      # Foundational utilities
            'services',   # Business logic
            'ext',        # Extensions
            'handlers',   # Command processing
            'ui',         # User interface
            'cogs'        # Discord cogs (terakhir)
        ]
    
    async def load_all_modules(self) -> bool:
        """
        Memuat semua modul sesuai urutan yang benar
        Returns: True jika semua modul berhasil dimuat, False jika ada yang gagal
        """
        logger.info("🚀 Memulai pemuatan modul bot...")
        
        success_count = 0
        total_count = 0
        
        for module_type in self.loading_order:
            logger.info(f"📂 Memuat modul {module_type}...")
            
            if module_type == 'cogs':
                # Khusus untuk cogs, gunakan discord.py extension system
                loaded, failed = await self._load_cogs()
            else:
                # Untuk modul lain, import secara normal
                loaded, failed = await self._load_module_type(module_type)
            
            success_count += loaded
            total_count += loaded + failed
            
            if failed > 0:
                logger.warning(f"⚠️  {failed} modul {module_type} gagal dimuat")
            else:
                logger.info(f"✅ Semua modul {module_type} berhasil dimuat")
        
        # Summary
        logger.info(f"📊 Ringkasan pemuatan: {success_count}/{total_count} modul berhasil dimuat")
        
        if self.failed_modules:
            logger.error("❌ Modul yang gagal dimuat:")
            for module, error in self.failed_modules:
                logger.error(f"   - {module}: {error}")
        
        return len(self.failed_modules) == 0
    
    async def _load_module_type(self, module_type: str) -> Tuple[int, int]:
        """
        Memuat semua modul dari tipe tertentu
        Returns: (loaded_count, failed_count)
        """
        module_path = Path(f"src/{module_type}")
        
        if not module_path.exists():
            logger.warning(f"📁 Direktori {module_path} tidak ditemukan")
            return 0, 0
        
        loaded = 0
        failed = 0
        
        # Scan semua file Python di direktori
        for py_file in module_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            # Convert path ke module name
            relative_path = py_file.relative_to(Path("."))
            module_name = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]  # Remove .py
            
            try:
                # Import module
                importlib.import_module(module_name)
                logger.debug(f"   ✓ {module_name}")
                loaded += 1
                self.loaded_modules.append(module_name)
                
            except Exception as e:
                logger.error(f"   ✗ {module_name}: {str(e)}")
                failed += 1
                self.failed_modules.append((module_name, str(e)))
        
        return loaded, failed
    
    async def _load_cogs(self) -> Tuple[int, int]:
        """
        Memuat semua cogs dari direktori src/cogs
        Returns: (loaded_count, failed_count)
        """
        cogs_path = Path("src/cogs")
        
        if not cogs_path.exists():
            logger.error("📁 Direktori src/cogs tidak ditemukan!")
            return 0, 0
        
        # Auto-discover semua cogs
        cog_files = self._discover_cogs(cogs_path)
        
        loaded = 0
        failed = 0
        
        for cog_module in cog_files:
            try:
                await self.bot.load_extension(cog_module)
                logger.info(f"   ✓ {cog_module}")
                loaded += 1
                self.loaded_modules.append(cog_module)
                
            except Exception as e:
                logger.error(f"   ✗ {cog_module}: {str(e)}")
                logger.error(f"      Detail error: {str(e)}", exc_info=True)
                failed += 1
                self.failed_modules.append((cog_module, str(e)))
        
        return loaded, failed
    
    def _discover_cogs(self, cogs_path: Path) -> List[str]:
        """
        Auto-discovery semua file cogs yang valid dengan urutan prioritas
        Returns: List of module names
        """
        cog_modules = []
        
        # Urutan prioritas loading cogs (livestock dulu, baru buttons)
        priority_order = [
            'live_stock.py',    # Harus dimuat pertama
            'live_buttons.py',  # Dimuat setelah live_stock
        ]
        
        # Load priority cogs first
        for priority_file in priority_order:
            py_file = cogs_path / priority_file
            if py_file.exists() and self._validate_cog_file(py_file):
                module_name = f"src.cogs.{py_file.stem}"
                cog_modules.append(module_name)
                logger.info(f"🔍 Priority cog ditemukan: {module_name}")
        
        # Load remaining cogs
        for py_file in cogs_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            # Skip file backup atau temporary
            if py_file.name.startswith('.') or py_file.name.endswith('.bak'):
                continue
            
            # Skip priority files yang sudah dimuat
            if py_file.name in priority_order:
                continue
                
            # Skip admin sub-cogs yang dimuat oleh admin.py
            admin_sub_cogs = ['admin_base.py', 'admin_balance.py', 'admin_store.py', 'admin_system.py', 'admin_transaction.py']
            if py_file.name in admin_sub_cogs:
                logger.debug(f"⏭️  Skipping admin sub-cog: {py_file.name} (loaded by admin.py)")
                continue
            
            # Convert ke module name
            module_name = f"src.cogs.{py_file.stem}"
            
            # Validasi apakah file memiliki setup function
            if self._validate_cog_file(py_file):
                cog_modules.append(module_name)
                logger.debug(f"🔍 Ditemukan cog: {module_name}")
            else:
                logger.warning(f"⚠️  File {py_file.name} tidak memiliki setup function yang valid")
        
        return cog_modules  # Tidak di-sort agar urutan prioritas tetap terjaga
    
    def _validate_cog_file(self, file_path: Path) -> bool:
        """
        Validasi apakah file cog memiliki setup function
        Returns: True jika valid, False jika tidak
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip file yang hanya berisi utility functions (tidak ada setup function)
            if file_path.name == 'utils.py' and 'def setup(' not in content and 'async def setup(' not in content:
                logger.debug(f"⏭️  Skipping utility file: {file_path.name}")
                return False
                
            # Cek apakah ada async def setup atau def setup
            has_setup = ('async def setup(' in content or 'def setup(' in content)
            has_cog_class = ('commands.Cog' in content or 'class ' in content and 'Cog' in content)
            
            # File valid jika memiliki setup function atau class Cog
            return has_setup or has_cog_class
                   
        except Exception as e:
            logger.error(f"Error validating {file_path}: {e}")
            return False
    
    def get_loaded_modules(self) -> List[str]:
        """Dapatkan list modul yang berhasil dimuat"""
        return self.loaded_modules.copy()
    
    def get_failed_modules(self) -> List[Tuple[str, str]]:
        """Dapatkan list modul yang gagal dimuat beserta error"""
        return self.failed_modules.copy()
    
    async def reload_module(self, module_name: str) -> bool:
        """
        Reload modul tertentu
        Returns: True jika berhasil, False jika gagal
        """
        try:
            if module_name.startswith('src.cogs.'):
                # Reload cog
                await self.bot.reload_extension(module_name)
            else:
                # Reload regular module
                importlib.reload(importlib.import_module(module_name))
            
            logger.info(f"🔄 Berhasil reload {module_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Gagal reload {module_name}: {e}")
            return False
    
    async def unload_all_cogs(self):
        """Unload semua cogs yang dimuat"""
        logger.info("🔄 Unloading semua cogs...")
        
        for module in self.loaded_modules:
            if module.startswith('src.cogs.'):
                try:
                    await self.bot.unload_extension(module)
                    logger.debug(f"   ✓ Unloaded {module}")
                except Exception as e:
                    logger.error(f"   ✗ Failed to unload {module}: {e}")
