"""
Database Connection Manager
Menangani koneksi dan operasi database dasar
"""

import sqlite3
import logging
import time
import os
import asyncio
from pathlib import Path
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager untuk koneksi dan operasi database"""
    
    def __init__(self, db_path: str = "shop.db"):
        self.db_path = Path(db_path)
        self.max_retries = 3
        self.timeout = 5
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Inisialisasi database"""
        try:
            if self._initialized:
                return True
                
            # Cek permission direktori
            db_dir = self.db_path.parent
            if not os.access(db_dir, os.W_OK):
                logger.error(f"Tidak ada write access ke: {db_dir}")
                return False
            
            # Setup database jika belum ada
            if not self.db_path.exists():
                from src.database.migrations import setup_database
                if not await setup_database():
                    return False
            
            # Verifikasi database
            if not await self.verify_database():
                logger.error("Verifikasi database gagal")
                return False
            
            self._initialized = True
            logger.info("Database berhasil diinisialisasi")
            return True
            
        except Exception as e:
            logger.error(f"Gagal inisialisasi database: {e}")
            return False
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager untuk koneksi database"""
        conn = None
        for attempt in range(self.max_retries):
            try:
                conn = sqlite3.connect(str(self.db_path), timeout=self.timeout)
                conn.row_factory = sqlite3.Row
                
                # Konfigurasi database
                cursor = conn.cursor()
                cursor.execute("PRAGMA busy_timeout = 5000")
                cursor.execute("PRAGMA journal_mode = WAL")
                cursor.execute("PRAGMA synchronous = NORMAL")
                cursor.execute("PRAGMA foreign_keys = ON")
                
                yield conn
                break
                
            except sqlite3.Error as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Gagal koneksi database setelah {self.max_retries} percobaan: {e}")
                    raise
                logger.warning(f"Percobaan koneksi {attempt + 1} gagal: {e}")
                await asyncio.sleep(0.1 * (attempt + 1))
            finally:
                if conn:
                    conn.close()
    
    async def execute_query(self, query: str, params: tuple = ()) -> Optional[List[sqlite3.Row]]:
        """Eksekusi query SELECT"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error eksekusi query: {e}")
            return None
    
    async def execute_update(self, query: str, params: tuple = ()) -> bool:
        """Eksekusi query INSERT/UPDATE/DELETE"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error eksekusi update: {e}")
            return False
    
    async def verify_database(self) -> bool:
        """Verifikasi integritas database"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Cek integritas
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result and result[0] != 'ok':
                    logger.error("Database integrity check gagal")
                    return False
                
                # Cleanup expired cache
                cursor.execute("DELETE FROM cache WHERE expires_at < strftime('%s', 'now')")
                conn.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error verifikasi database: {e}")
            return False
    
    async def close(self):
        """Cleanup database connections"""
        try:
            # Vacuum database untuk optimasi
            async with self.get_connection() as conn:
                conn.execute("VACUUM")
            logger.info("Database cleanup selesai")
        except Exception as e:
            logger.error(f"Error saat cleanup database: {e}")
