"""
Database Manager Utama
Menggabungkan koneksi database dan setup
"""

import sqlite3
import logging
import time
import os
import asyncio
from pathlib import Path
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager utama untuk database operations"""
    
    _instance = None
    _instance_lock = asyncio.Lock()
    
    def __new__(cls, db_path: str = "shop.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = "shop.db"):
        if not self.initialized:
            self.db_path = Path(db_path)
            self.max_retries = 3
            self.timeout = 5
            self.initialized = True
    
    async def initialize(self) -> bool:
        """Inisialisasi database lengkap"""
        try:
            # Cek permission direktori
            db_dir = self.db_path.parent
            if not os.access(db_dir, os.W_OK):
                logger.error(f"Tidak ada write access ke: {db_dir}")
                return False
            
            # Setup database jika belum ada
            if not self.db_path.exists():
                if not await self.setup_database():
                    return False
            
            # Verifikasi database
            if not await self.verify_database():
                logger.error("Verifikasi database gagal")
                return False
            
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
    
    async def setup_database(self) -> bool:
        """Setup semua tabel database"""
        try:
            db_dir = self.db_path.parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Setup semua tabel
                    await self._create_cache_tables(cursor)
                    await self._create_user_tables(cursor)
                    await self._create_product_tables(cursor)
                    await self._create_system_tables(cursor)
                    await self._create_feature_tables(cursor)
                    
                    # Commit transaction
                    conn.commit()
                    logger.info("Database setup berhasil")
                    return True
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Error setup database: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error setup database: {e}")
            return False
    
    async def _create_cache_tables(self, cursor: sqlite3.Cursor):
        """Buat tabel untuk cache system"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def _create_user_tables(self, cursor: sqlite3.Cursor):
        """Buat tabel untuk user management"""
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                growid TEXT PRIMARY KEY,
                balance_wl INTEGER DEFAULT 0,
                balance_dl INTEGER DEFAULT 0,
                balance_bgl INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User Discord mapping
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_growid (
                discord_id TEXT PRIMARY KEY,
                growid TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (growid) REFERENCES users(growid) ON DELETE CASCADE
            )
        """)
        
        # User activity
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def _create_product_tables(self, cursor: sqlite3.Cursor):
        """Buat tabel untuk product management"""
        # Products
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Stock
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT NOT NULL,
                content TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'available',
                added_by TEXT NOT NULL,
                buyer_id TEXT,
                seller_id TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_code) REFERENCES products(code)
            )
        """)
        
        # Transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id TEXT NOT NULL,
                seller_id TEXT,
                product_code TEXT,
                quantity INTEGER NOT NULL,
                total_price INTEGER NOT NULL,
                transaction_type TEXT DEFAULT 'purchase',
                status TEXT DEFAULT 'pending',
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def _create_system_tables(self, cursor: sqlite3.Cursor):
        """Buat tabel untuk system management"""
        # Bot settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Admin logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Blacklist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                reason TEXT,
                added_by TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def _create_feature_tables(self, cursor: sqlite3.Cursor):
        """Buat tabel untuk fitur-fitur bot"""
        # Levels
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS levels (
                user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                level INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                total_xp INTEGER DEFAULT 0,
                messages INTEGER DEFAULT 0,
                last_message TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        
        # Level rewards
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS level_rewards (
                guild_id TEXT NOT NULL,
                level INTEGER NOT NULL,
                role_id TEXT NOT NULL,
                PRIMARY KEY (guild_id, level)
            )
        """)
        
        # Warnings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                moderator_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Giveaways
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                channel_id TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                winners_count INTEGER DEFAULT 1,
                end_time TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Worlds
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS worlds (
                world_name TEXT PRIMARY KEY,
                owner_name TEXT NOT NULL,
                bot_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
    
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
                
                logger.info(f"Database verification completed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
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

# Instance global untuk digunakan di seluruh aplikasi
db_manager = DatabaseManager()

# Fungsi backward compatibility
def get_connection(max_retries: int = 3, timeout: int = 5) -> sqlite3.Connection:
    """Fungsi backward compatibility untuk get_connection"""
    db_path = Path('shop.db')
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(str(db_path), timeout=timeout)
            conn.row_factory = sqlite3.Row
            
            # Konfigurasi database
            cursor = conn.cursor()
            cursor.execute("PRAGMA busy_timeout = 5000")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA foreign_keys = ON")
            
            return conn
            
        except sqlite3.Error as e:
            if attempt == max_retries - 1:
                logger.error(f"Gagal koneksi database setelah {max_retries} percobaan: {e}")
                raise
            logger.warning(f"Percobaan koneksi {attempt + 1} gagal: {e}")
            time.sleep(0.1 * (attempt + 1))

def setup_database():
    """Fungsi backward compatibility untuk setup_database"""
    import asyncio
    return asyncio.run(db_manager.setup_database())

def verify_database():
    """Fungsi backward compatibility untuk verify_database"""
    import asyncio
    return asyncio.run(db_manager.verify_database())
