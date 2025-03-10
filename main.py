#!/usr/bin/env python3
"""
Discord Bot for Store DC
Author: fdyytu
Created at: 2025-03-07 18:30:16 UTC
Last Modified: 2025-03-10 13:04:33 UTC
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Core imports
import discord
from discord.ext import commands
import json
import logging
import asyncio
import aiohttp
import sqlite3
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

# Import constants first
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
    CommandCooldown
)

# Import database
from database import setup_database, get_connection

# Import handlers and managers
from ext.cache_manager import CacheManager
from ext.base_handler import BaseLockHandler, BaseResponseHandler
from utils.command_handler import AdvancedCommandHandler

# Channel configuration
CHANNEL_CONFIG = {
    'id_live_stock': 'Live Stock Channel',
    'id_log_purch': 'Purchase Log Channel',
    'id_donation_log': 'Donation Log Channel',
    'id_history_buy': 'Purchase History Channel'
}

# Initialize basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def setup_project_structure():
    """Create necessary directories and files"""
    dirs = ['logs', 'ext', 'utils', 'cogs', 'data', 'temp', 'backups']
    for directory in dirs:
        Path(directory).mkdir(exist_ok=True)
        init_file = Path(directory) / '__init__.py'
        init_file.touch(exist_ok=True)

def check_dependencies():
    """Check if all required dependencies are installed"""
    required = {
        'discord.py': 'discord',
        'aiohttp': 'aiohttp',
        'sqlite3': 'sqlite3',
        'asyncio': 'asyncio',
        'PyNaCl': 'nacl'  # Optional for voice support
    }
    
    missing = []
    for package, import_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            if package != 'PyNaCl':  # Skip PyNaCl as it's optional
                missing.append(package)
    
    if missing:
        logger.critical(f"Missing required packages: {', '.join(missing)}")
        logger.info("Please install required packages using:")
        logger.info(f"pip install {' '.join(missing)}")
        sys.exit(1)

# Check dependencies and setup structure first
check_dependencies()
setup_project_structure()

# Setup enhanced logging
log_dir = Path(PATHS.LOGS)
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format=LOGGING.FORMAT,
    handlers=[
        RotatingFileHandler(
            log_dir / 'bot.log',
            maxBytes=LOGGING.MAX_BYTES,
            backupCount=LOGGING.BACKUP_COUNT,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

def load_config():
    """Load and validate configuration"""
    # Gunakan keys dari CHANNEL_CONFIG + tambahan ID yang diperlukan
    id_keys = list(CHANNEL_CONFIG.keys()) + ['guild_id', 'admin_id']
    required_keys = ['token'] + id_keys
    
    try:
        with open(PATHS.CONFIG, 'r') as f:
            config = json.load(f)
            
        # Validate required keys
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise KeyError(f"Missing required config keys: {', '.join(missing_keys)}")
        
        # Validate value types
        for key in id_keys:
            try:
                config[key] = int(config[key])
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for {key}. Expected integer.")
        
        # Set default values
        defaults = {
            'cooldown_time': CommandCooldown.DEFAULT,
            'max_items': Stock.MAX_ITEMS,
            'cache_timeout': CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.SHORT)
        }
        
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
        
        return config
        
    except FileNotFoundError:
        logger.critical(f"Config file not found: {PATHS.CONFIG}")
        logger.info("Please create a config.json file with required settings")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.critical(f"Invalid JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Error loading config: {e}")
        sys.exit(1)

class StoreBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.config = load_config()
        self.cache_manager = CacheManager()
        self.start_time = datetime.now(timezone.utc)
        self.maintenance_mode = False
        self._ready = asyncio.Event()

    async def setup_hook(self):
        """Setup bot extensions and database"""
        try:
            # Setup database first
            logger.info("Setting up database...")
            setup_database()
            
            # Load core services first and verify
            logger.info("Loading core services...")
            for ext in EXTENSIONS.SERVICES:
                try:
                    logger.info(f"Loading service: {ext}")
                    await self.load_extension(ext)
                    logger.info(f"Successfully loaded service: {ext}")
                    await asyncio.sleep(2)  # Increased delay between service loads
                except Exception as e:
                    logger.critical(f"Failed to load critical service {ext}: {e}")
                    await self.close()
                    return

            # Load LiveStockCog first with proper channel validation
            logger.info("Loading LiveStockCog...")
            try:
                # Validate stock channel first
                stock_channel_id = self.config['id_live_stock']
                await asyncio.sleep(2)  # Wait for gateway connection
                
                if not self.get_channel(stock_channel_id):
                    logger.error(f"Stock channel with ID {stock_channel_id} not found")
                    raise RuntimeError("Stock channel not found")
                    
                await self.load_extension('ext.live_stock')
                await asyncio.sleep(5)  # Give time for LiveStockCog to initialize
                
                # Verify LiveStockCog loaded properly
                stock_cog = self.get_cog('LiveStockCog')
                if not stock_cog or not hasattr(stock_cog, 'stock_manager'):
                    raise RuntimeError("LiveStockCog failed to initialize properly")
                    
                logger.info("Successfully loaded LiveStockCog")
                
                # Now load LiveButtonsCog
                logger.info("Loading LiveButtonsCog...")
                try:
                    await self.load_extension('ext.live_buttons')
                    await asyncio.sleep(3)  # Wait for LiveButtonsCog to initialize
                    
                    # Verify LiveButtonsCog loaded properly
                    buttons_cog = self.get_cog('LiveButtonsCog')
                    if not buttons_cog:
                        raise RuntimeError("LiveButtonsCog failed to initialize")
                        
                    logger.info("Successfully loaded LiveButtonsCog")
                except Exception as e:
                    logger.error(f"Failed to load LiveButtonsCog: {e}")
                    # Continue loading other extensions even if this fails

            except Exception as e:
                logger.critical(f"Failed to load LiveStockCog: {e}")
                await self.close()
                return

            # Load remaining features
            logger.info("Loading remaining features...")
            for ext in [e for e in EXTENSIONS.FEATURES if e not in ['ext.live_stock', 'ext.live_buttons']]:
                try:
                    logger.info(f"Loading feature: {ext}")
                    await self.load_extension(ext)
                    logger.info(f"Successfully loaded feature: {ext}")
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Failed to load feature {ext}: {e}")
            
            # Load optional cogs last
            logger.info("Loading optional cogs...")
            for ext in EXTENSIONS.COGS:
                try:
                    logger.info(f"Loading cog: {ext}")
                    await self.load_extension(ext)
                    logger.info(f"Successfully loaded cog: {ext}")
                except Exception as e:
                    logger.warning(f"Failed to load optional cog {ext}: {e}")
            
            # Set ready event after everything is loaded
            logger.info("Setting ready event...")
            self._ready.set()
            
            logger.info("Bot setup completed successfully")
            
        except Exception as e:
            logger.critical(f"Failed to setup bot: {e}", exc_info=True)
            await self.close()
    
    async def on_ready(self):
        try:
            logger.info(f"Logged in as {self.user.name} ({self.user.id})")
            logger.info(f"Discord.py Version: {discord.__version__}")
            
            # Validasi channels menggunakan CHANNEL_CONFIG
            logger.info("Validating channels...")
            await asyncio.sleep(2)
            
            for channel_id, channel_name in CHANNEL_CONFIG.items():
                channel = self.get_channel(self.config[channel_id])
                if not channel:
                    logger.error(f"{channel_name} dengan ID {self.config[channel_id]} tidak ditemukan")
                    await self.close()
                    return
                logger.info(f"Found {channel_name}: {channel.name}")
            
            # Set bot status
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="Growtopia Shop 🏪"
            )
            await self.change_presence(activity=activity)
            
            # Cleanup expired cache
            await self.cache_manager.cleanup_expired()
            
            logger.info("Bot is fully ready!")
            
        except Exception as e:
            logger.critical(f"Error in on_ready: {e}", exc_info=True)
            await self.close()
        
    async def on_error(self, event_method: str, *args, **kwargs):
        """Global error handler"""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(f"Error in {event_method}: {exc_type.__name__}: {exc_value}")
        logger.error("Full traceback:", exc_info=True)
        
    async def close(self):
        """Cleanup before closing"""
        try:
            # Cleanup tasks
            if hasattr(self, 'cache_manager'):
                await self.cache_manager.cleanup_expired()
            
            # Cancel all tasks dengan limit
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks[:100]:  # Batasi hanya 100 task
                task.cancel()
            
            await asyncio.gather(*tasks[:100], return_exceptions=True)
            await super().close()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
        finally:
            logger.info("Bot shutdown complete")
            
async def run_bot():
    """Run the bot"""
    bot = StoreBot()
    
    try:
        async with bot:
            await bot.start(bot.config['token'])
            
            # Add timeout for wait_until_ready
            try:
                await asyncio.wait_for(bot._ready.wait(), timeout=60)  # 60 seconds timeout
            except asyncio.TimeoutError:
                logger.critical("Bot failed to become ready within 60 seconds")
                await bot.close()
                return
                
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except discord.LoginFailure:
        logger.critical("Invalid bot token")
    except Exception as e:
        logger.critical(f"Bot crashed: {e}", exc_info=True)
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)