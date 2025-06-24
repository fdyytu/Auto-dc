"""
Hot Reload Manager
Menangani auto-reload file dan folder ketika ada perubahan
"""

import os
import sys
import asyncio
import logging
import importlib
from pathlib import Path
from typing import Set, Dict, Optional, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

from core.config import config_manager

logger = logging.getLogger(__name__)

class HotReloadHandler(FileSystemEventHandler):
    """Handler untuk menangani perubahan file"""
    
    def __init__(self, reload_manager):
        self.reload_manager = reload_manager
        self.pending_reloads: Set[str] = set()
        
    def on_modified(self, event):
        """Ketika file dimodifikasi"""
        if not event.is_directory:
            self._handle_file_change(event.src_path, "modified")
    
    def on_created(self, event):
        """Ketika file dibuat"""
        if not event.is_directory:
            self._handle_file_change(event.src_path, "created")
    
    def on_deleted(self, event):
        """Ketika file dihapus"""
        if not event.is_directory:
            self._handle_file_change(event.src_path, "deleted")
    
    def _handle_file_change(self, file_path: str, change_type: str):
        """Menangani perubahan file"""
        try:
            # Normalisasi path
            file_path = os.path.normpath(file_path)
            
            # Cek apakah file harus diabaikan
            if self._should_ignore_file(file_path):
                return
            
            # Log perubahan
            if self.reload_manager.config.get("hot_reload", {}).get("log_reloads", True):
                logger.info(f"File {change_type}: {file_path}")
            
            # Tambahkan ke pending reloads
            self.pending_reloads.add(file_path)
            
            # Schedule reload dengan delay
            if self.reload_manager.bot_loop:
                asyncio.run_coroutine_threadsafe(
                    self._schedule_reload(file_path),
                    self.reload_manager.bot_loop
                )
            else:
                logger.warning(f"No event loop available for reloading {file_path}")
            
        except Exception as e:
            logger.error(f"Error handling file change {file_path}: {e}")
    
    def _should_ignore_file(self, file_path: str) -> bool:
        """Cek apakah file harus diabaikan"""
        ignore_patterns = self.reload_manager.config.get("hot_reload", {}).get("ignore_patterns", [])
        
        for pattern in ignore_patterns:
            if pattern in file_path:
                return True
        
        # Cek ekstensi file
        watch_extensions = self.reload_manager.config.get("hot_reload", {}).get("watch_extensions", [".py"])
        if not any(file_path.endswith(ext) for ext in watch_extensions):
            return True
        
        return False
    
    async def _schedule_reload(self, file_path: str):
        """Schedule reload dengan delay"""
        try:
            delay = self.reload_manager.config.get("hot_reload", {}).get("reload_delay", 1.0)
            await asyncio.sleep(delay)
            
            if file_path in self.pending_reloads:
                await self.reload_manager.reload_file(file_path)
                self.pending_reloads.discard(file_path)
                
        except Exception as e:
            logger.error(f"Error scheduling reload for {file_path}: {e}")

class HotReloadManager:
    """Manager untuk hot reload functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = config_manager.load_config()
        self.observer: Optional[Observer] = None
        self.handler: Optional[HotReloadHandler] = None
        self.enabled = False
        self.watched_modules: Dict[str, float] = {}  # module_name -> last_reload_time
        self.bot_loop = None
        
    async def start(self):
        """Mulai hot reload monitoring"""
        try:
            if not self.config.get("hot_reload", {}).get("enabled", False):
                logger.info("Hot reload disabled in config")
                return False
            
            if self.enabled:
                logger.warning("Hot reload sudah aktif")
                return True
            
            # Setup file watcher
            self.handler = HotReloadHandler(self)
            self.observer = Observer()
            
            # Watch directories
            watch_dirs = self.config.get("hot_reload", {}).get("watch_directories", [])
            project_root = Path(__file__).parent.parent
            
            for watch_dir in watch_dirs:
                dir_path = project_root / watch_dir
                if dir_path.exists():
                    self.observer.schedule(self.handler, str(dir_path), recursive=True)
                    logger.info(f"Watching directory: {dir_path}")
                else:
                    logger.warning(f"Directory tidak ditemukan: {dir_path}")
            
            # Start observer
            self.observer.start()
            self.enabled = True
            
            # Store current event loop
            try:
                self.bot_loop = asyncio.get_running_loop()
            except RuntimeError:
                self.bot_loop = None
            
            logger.info("Hot reload manager started")
            return True
            
        except Exception as e:
            logger.error(f"Gagal start hot reload: {e}")
            return False
    
    async def stop(self):
        """Stop hot reload monitoring"""
        try:
            if not self.enabled:
                return
            
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            
            self.handler = None
            self.enabled = False
            
            logger.info("Hot reload manager stopped")
            
        except Exception as e:
            logger.error(f"Error stopping hot reload: {e}")
    
    async def reload_file(self, file_path: str):
        """Reload file yang berubah"""
        try:
            # Konversi path ke module name
            module_name = self._path_to_module(file_path)
            if not module_name:
                return
            
            # Cek apakah ini adalah cog
            if module_name.startswith("cogs."):
                await self._reload_cog(module_name)
            else:
                await self._reload_module(module_name)
                
        except Exception as e:
            logger.error(f"Error reloading file {file_path}: {e}")
    
    def _path_to_module(self, file_path: str) -> Optional[str]:
        """Konversi file path ke module name"""
        try:
            # Normalisasi path
            file_path = os.path.normpath(file_path)
            project_root = Path(__file__).parent.parent
            
            # Buat relative path
            try:
                rel_path = Path(file_path).relative_to(project_root)
            except ValueError:
                return None
            
            # Konversi ke module name
            if rel_path.suffix != ".py":
                return None
            
            # Hapus .py extension dan konversi path separator ke dot
            module_parts = rel_path.with_suffix("").parts
            
            # Skip __init__.py files
            if module_parts[-1] == "__init__":
                return None
            
            module_name = ".".join(module_parts)
            return module_name
            
        except Exception as e:
            logger.error(f"Error converting path to module {file_path}: {e}")
            return None
    
    async def _reload_cog(self, cog_name: str):
        """Reload specific cog"""
        try:
            if not self.config.get("hot_reload", {}).get("auto_reload_cogs", True):
                logger.info(f"Auto reload cogs disabled, skipping {cog_name}")
                return
            
            # Cek apakah cog sudah dimuat
            if cog_name in [ext for ext in self.bot.extensions]:
                # Reload cog
                await self.bot.reload_extension(cog_name)
                logger.info(f"✓ Reloaded cog: {cog_name}")
            else:
                # Load cog baru
                await self.bot.load_extension(cog_name)
                logger.info(f"✓ Loaded new cog: {cog_name}")
                
        except Exception as e:
            logger.error(f"✗ Failed to reload cog {cog_name}: {e}")
    
    async def _reload_module(self, module_name: str):
        """Reload module biasa"""
        try:
            # Cek apakah module sudah dimuat
            if module_name in sys.modules:
                # Reload module
                importlib.reload(sys.modules[module_name])
                logger.info(f"✓ Reloaded module: {module_name}")
            else:
                # Import module baru
                importlib.import_module(module_name)
                logger.info(f"✓ Imported new module: {module_name}")
                
        except Exception as e:
            logger.error(f"✗ Failed to reload module {module_name}: {e}")
    
    async def reload_all_cogs(self):
        """Reload semua cogs"""
        try:
            extensions = list(self.bot.extensions.keys())
            reloaded = 0
            failed = 0
            
            for ext in extensions:
                try:
                    await self.bot.reload_extension(ext)
                    logger.info(f"✓ Reloaded: {ext}")
                    reloaded += 1
                except Exception as e:
                    logger.error(f"✗ Failed to reload {ext}: {e}")
                    failed += 1
            
            logger.info(f"Reload complete: {reloaded} success, {failed} failed")
            return reloaded, failed
            
        except Exception as e:
            logger.error(f"Error reloading all cogs: {e}")
            return 0, 0
    
    def is_enabled(self) -> bool:
        """Cek apakah hot reload aktif"""
        return self.enabled
    
    def get_status(self) -> Dict:
        """Get status hot reload"""
        return {
            "enabled": self.enabled,
            "watching": len(self.config.get("hot_reload", {}).get("watch_directories", [])),
            "loaded_extensions": len(self.bot.extensions),
            "config": self.config.get("hot_reload", {})
        }
