#!/usr/bin/env python3
"""
Discord Bot for Store DC (REST API Version)
Author: fdyytu
Created at: 2025-03-10 18:58:57 UTC
Last Modified: 2025-03-10 18:58:57 UTC
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

# Initial extensions list - menggunakan EXTENSIONS dari constants.py
initial_extensions = EXTENSIONS.SERVICES + EXTENSIONS.FEATURES + EXTENSIONS.COGS

class DiscordAPI:
    def __init__(self, token):
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

class CacheManager:
    """Simple cache manager implementation"""
    def __init__(self):
        self._cache = {}
        
    async def set(self, key: str, value, expires_in: int = 300):
        """Set cache value"""
        self._cache[key] = value
        
    async def get(self, key: str):
        """Get cache value"""
        return self._cache.get(key)
        
    async def delete(self, key: str):
        """Delete cache value"""
        self._cache.pop(key, None)
        
    async def clear(self):
        """Clear all cache"""
        self._cache.clear()

class StoreBot:
    def __init__(self):
        self.config = self.load_config()
        self.api = DiscordAPI(self.config["token"])
        self.db = self.setup_database()
        self.cache_manager = CacheManager()
        self.cogs = {}
        self.is_ready = asyncio.Event()
        self.maintenance_mode = False
        
    def load_config(self):
        """Load configuration"""
        try:
            with open(PATHS.CONFIG, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            required_keys = [
                'token', 'guild_id', 'admin_id',
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

    def setup_database(self):
        """Setup database connection"""
        try:
            db = sqlite3.connect(PATHS.DATABASE)
            db.row_factory = sqlite3.Row
            logger.info("Database connected successfully")
            return db
        except Exception as e:
            logger.critical(f"Database connection failed: {e}")
            raise

    async def load_extension(self, name):
        """Load a bot extension"""
        try:
            # Import the extension module
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
        for ext in initial_extensions:
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
                await self.cache_manager.clear()
            
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