#!/usr/bin/env python3
"""
Discord Bot for Store DC (REST API Version)
Author: fdyytu
Created at: 2025-03-10 18:56:54 UTC
Last Modified: 2025-03-10 21:26:14 UTC
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

    # ... Rest of DiscordAPI class remains the same ...

class StoreBot:
    def __init__(self):
        self.config = self.load_config()
        # Pastikan token ada sebelum inisialisasi API
        self.token = get_token()
        self.api = DiscordAPI(self.token)
        self.db = self.setup_database()
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

    # ... Rest of StoreBot class remains the same ...

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