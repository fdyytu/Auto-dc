#!/usr/bin/env python3
"""
Discord Bot for Store DC (REST API Version)
Author: fdyytu
Created at: 2025-03-10 18:56:54 UTC
Last Modified: 2025-03-10 21:31:06 UTC
"""

import sys
import os
import aiohttp
import sqlite3
from discord.ext import commands
import asyncio
import logging
import logging.handlers
from datetime import datetime, timezone
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import constants
from ext.constants import (
    COLORS,
    MESSAGES,
    BUTTON_IDS,
    CACHE_TIMEOUT,
    Stock,
    Balance,
    TransactionType,
    Status,
    CURRENCY_RATES,
    UPDATE_INTERVAL,
    EXTENSIONS,
    LOGGING,
    PATHS,
    Database,
    CommandCooldown,
    NOTIFICATION_CHANNELS
)

# Initialize basic logging
logging.basicConfig(
    level=logging.INFO,
    format=LOGGING.FORMAT,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def setup_database():
    """Setup database connection dan tables"""
    try:
        # Pastikan direktori database ada
        db_path = Path(PATHS.DATABASE)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Buat koneksi database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Buat tables yang diperlukan
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                growid TEXT UNIQUE,
                balance_wl INTEGER DEFAULT 0,
                balance_dl INTEGER DEFAULT 0,
                balance_bgl INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Products table
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
        
        # Stock table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'available',
                buyer_id TEXT,
                added_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_code) REFERENCES products(code)
            )
        """)
        
        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                growid TEXT NOT NULL,
                type TEXT NOT NULL,
                details TEXT,
                old_balance TEXT,
                new_balance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (growid) REFERENCES users(growid)
            )
        """)
        
        # Cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at INTEGER
            )
        """)
        
        conn.commit()
        logger.info("Database setup completed successfully")
        return conn
        
    except Exception as e:
        logger.critical(f"Failed to setup database: {e}")
        raise

def get_token() -> str:
    """Get bot token dari environment variable atau config"""
    # Coba dari environment variable dulu
    token = os.getenv('DISCORD_TOKEN')
    
    # Kalau tidak ada, coba dari config.json
    if not token:
        try:
            with open(PATHS.CONFIG, 'r', encoding='utf-8') as f:
                config = json.load(f)
                token = config.get('token')
        except:
            pass
            
    # Kalau masih tidak ada, raise error
    if not token:
        raise ValueError(
            "Bot token tidak ditemukan! Pastikan token sudah diatur di:\n"
            "1. Environment variable 'DISCORD_TOKEN', atau\n"
            "2. File config.json dengan key 'token'"
        )
        
    return token

class DiscordAPI:
    def __init__(self, token):
        if not token:
            raise ValueError("Token tidak boleh kosong!")
            
        self.token = token
        self.base_url = "https://discord.com/api/v10"
        self.session = None
        self.headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json"
        }
        self.cache = {}
        self.is_ready = asyncio.Event()

    async def start(self):
        """Start API session"""
        connector = aiohttp.TCPConnector(
            force_close=True,
            enable_cleanup_closed=True,
            limit=100
        )
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )

    async def close(self):
        """Close API session"""
        if self.session:
            await self.session.close()

    async def make_request(self, method: str, endpoint: str, **kwargs):
        """Make API request with retries"""
        url = f"{self.base_url}{endpoint}"
        retries = 3
        
        for attempt in range(retries):
            try:
                async with getattr(self.session, method)(url, **kwargs) as resp:
                    if resp.status in (200, 201, 204):
                        if resp.status != 204:
                            return await resp.json()
                        return True
                    elif resp.status == 429:  # Rate limit
                        retry_after = (await resp.json()).get('retry_after', 5)
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        logger.error(f"Request failed: {resp.status}")
                        return None
            except Exception as e:
                logger.error(f"Request error (attempt {attempt+1}): {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(1)

class StoreBot:
    def __init__(self):
        self.config = self.load_config()
        self.token = get_token()
        self.api = DiscordAPI(self.token)
        self.db = setup_database()  # Menggunakan fungsi setup_database
        self.cache_manager = self.setup_cache()
        self.cogs = {}
        self.is_ready = asyncio.Event()
        self.maintenance_mode = False

    def load_config(self):
        """Load configuration"""
        try:
            with open(PATHS.CONFIG, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            required_keys = [
                'guild_id', 'admin_id',
                'id_live_stock', 'id_log_purch',
                'id_donation_log', 'id_history_buy'
            ]
            
            missing = [key for key in required_keys if key not in config]
            if missing:
                raise ValueError(f"Missing required config keys: {', '.join(missing)}")
                
            return config
        except Exception as e:
            logger.critical(f"Failed to load config: {e}")
            raise

    def setup_cache(self):
        """Setup cache manager"""
        from ext.cache_manager import CacheManager
        return CacheManager()
        
    async def load_extension(self, name):
        """Load a bot extension"""
        try:
            module = __import__(name, fromlist=['setup'])
            if hasattr(module, 'setup'):
                await module.setup(self)
                self.cogs[name] = module
                logger.info(f"Loaded extension: {name}")
            else:
                logger.error(f"Extension {name} missing setup function")
        except Exception as e:
            logger.error(f"Failed to load extension {name}: {e}")
            raise

    async def load_extensions(self):
        """Load all extensions"""
        for ext in EXTENSIONS.ALL:
            try:
                await self.load_extension(ext)
            except Exception as e:
                logger.error(f"Error loading {ext}: {e}")

    async def start(self):
        """Start the bot"""
        try:
            logger.info("Starting bot...")
            await self.api.start()
            
            # Initialize services
            logger.info("Loading extensions...")
            await self.load_extensions()
            
            # Verify channels
            channel_ids = [
                self.config['id_live_stock'],
                self.config['id_log_purch'],
                self.config['id_donation_log'],
                self.config['id_history_buy']
            ]
            
            for channel_id in channel_ids:
                channel = await self.api.make_request('get', f'/channels/{channel_id}')
                if not channel:
                    logger.error(f"Cannot find channel: {channel_id}")
                    return False
            
            self.is_ready.set()
            logger.info("Bot is ready!")
            
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.critical(f"Fatal error: {e}")
        finally:
            await self.close()

    async def close(self):
        """Cleanup and close bot"""
        try:
            # Close API session
            await self.api.close()
            
            # Close database
            if hasattr(self, 'db'):
                self.db.close()
            
            # Clear cache
            if hasattr(self, 'cache_manager'):
                await self.cache_manager.clear_all()
            
            # Unload extensions
            for ext in self.cogs.copy():
                try:
                    module = self.cogs.pop(ext)
                    if hasattr(module, 'teardown'):
                        await module.teardown(self)
                except Exception as e:
                    logger.error(f"Error unloading {ext}: {e}")
                    
            logger.info("Cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main entry point"""
    # Setup logging
    log_dir = Path(PATHS.LOGS)
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'bot.log',
        maxBytes=LOGGING.MAX_BYTES,
        backupCount=LOGGING.BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(LOGGING.FORMAT))
    logger.addHandler(file_handler)
    
    try:
        # Create and start bot
        bot = StoreBot()
        await bot.start()
        
    except ValueError as e:
        logger.critical(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down by user request...")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if 'bot' in locals():
            await bot.close()

if __name__ == "__main__":
    try:
        # Record start time
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting bot at {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Run bot
        asyncio.run(main())
        
        # Calculate runtime
        end_time = datetime.now(timezone.utc)
        runtime = end_time - start_time
        logger.info(f"Bot stopped after running for {runtime}")
        
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)