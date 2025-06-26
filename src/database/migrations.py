"""
Database Migrations
Menangani setup dan migrasi database
"""

import sqlite3
import logging
import asyncio
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

async def setup_database() -> bool:
    """Setup semua tabel database"""
    try:
        db_path = Path('shop.db')
        db_dir = db_path.parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Setup semua tabel
        tables = [
            _create_cache_tables,
            _create_user_tables,
            _create_product_tables,
            _create_system_tables,
            _create_feature_tables
        ]
        
        for table_func in tables:
            await table_func(cursor)
        
        # Commit transaction
        conn.commit()
        conn.close()
        
        logger.info("Database setup berhasil")
        return True
        
    except Exception as e:
        logger.error(f"Error setup database: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

async def _create_cache_tables(cursor: sqlite3.Cursor):
    """Buat tabel untuk cache system"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

async def _create_user_tables(cursor: sqlite3.Cursor):
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

async def _create_product_tables(cursor: sqlite3.Cursor):
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
            product_code TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_code) REFERENCES products(code)
        )
    """)
    
    # Balance transactions table (untuk balance history)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            growid TEXT NOT NULL,
            type TEXT NOT NULL,
            details TEXT,
            old_balance TEXT,
            new_balance TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # World info table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_info (
            id INTEGER PRIMARY KEY,
            world TEXT NOT NULL,
            owner TEXT NOT NULL,
            bot TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

async def _create_system_tables(cursor: sqlite3.Cursor):
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

async def _create_feature_tables(cursor: sqlite3.Cursor):
    """Buat tabel untuk fitur-fitur bot"""
    # Levels
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS levels (
            user_id TEXT PRIMARY KEY,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            total_xp INTEGER DEFAULT 0,
            last_message TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
