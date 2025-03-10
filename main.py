#!/usr/bin/env python3
"""
Discord Bot for Store DC
Author: fdyytu
Created at: 2025-03-07 18:30:16 UTC
Last Modified: 2025-03-10 14:27:45 UTC
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
import re

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

def validate_token(token: str) -> bool:
    """Validate Discord bot token format"""
    if not token:
        return False
        
    # Bersihkan token dari whitespace dan karakter newline
    token = token.strip().replace('\n', '').replace('\r', '')
    
    # Debug info
    parts = token.split('.')
    logger.info(f"Token parts: {len(parts)}")
    if len(parts) == 3:
        logger.info(f"Part lengths: {len(parts[0])}, {len(parts[1])}, {len(parts[2])}")
    
    # Token minimal harus memiliki 3 bagian yang dipisahkan oleh titik
    if len(parts) != 3:
        logger.error("Token harus memiliki 3 bagian yang dipisahkan oleh titik")
        return False
        
    # Validasi panjang setiap bagian
    if not (20 <= len(parts[0]) <= 30):  # Lebih fleksibel untuk bagian pertama
        logger.error("Bagian pertama token tidak valid (harus 20-30 karakter)")
        return False
        
    if not (4 <= len(parts[1]) <= 8):  # Lebih fleksibel untuk bagian kedua
        logger.error("Bagian kedua token tidak valid (harus 4-8 karakter)")
        return False
        
    if not (24 <= len(parts[2]) <= 40):  # Lebih fleksibel untuk bagian ketiga
        logger.error("Bagian ketiga token tidak valid (harus 24-40 karakter)")
        return False
        
    # Validasi karakter yang diizinkan
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
    if not all(c in allowed_chars for c in token.replace('.', '')):
        logger.error("Token mengandung karakter yang tidak valid")
        return False
        
    return True

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
    logger.info(f"Membaca config dari: {os.path.abspath(PATHS.CONFIG)}")
    
    # Gunakan keys dari CHANNEL_CONFIG + tambahan ID yang diperlukan
    id_keys = list(CHANNEL_CONFIG.keys()) + ['guild_id', 'admin_id']
    required_keys = ['token'] + id_keys
    
    try:
        with open(PATHS.CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Validate token
        token = config.get('token', '').strip()
        if not validate_token(token):
            logger.critical("Token format tidak valid! Harap periksa token di config.json")
            logger.info("Format token yang benar: 24 karakter + '.' + 6 karakter + '.' + 27-38 karakter")
            sys.exit(1)
        
        logger.info(f"Token terbaca dengan panjang: {len(token)} karakter")
        config['token'] = token  # Simpan token yang sudah di-strip
            
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
        logger.critical(f"Config file tidak ditemukan: {PATHS.CONFIG}")
        logger.info("Silakan buat file config.json dengan pengaturan yang diperlukan")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.critical(f"Format JSON tidak valid dalam config file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Error saat loading config: {e}")
        sys.exit(1)

class StoreBot(commands.Bot):
    def __init__(self):
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True  # Tambahan untuk akses guild
        
        logger.info("Initializing bot with required intents...")
        
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
        
        # Tambahan untuk status koneksi
        self._connection_retries = 0
        self._max_retries = 5
        self._gateway_connected = asyncio.Event()

    async def setup_hook(self):
        """Setup bot extensions and database"""
        try:
            logger.info("Starting bot setup...")
            
            # Setup database first
            logger.info("Setting up database...")
            setup_database()
            
            # Check Discord connection first
            logger.info("Checking Discord connection...")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://discord.com/api/v10/gateway') as resp:
                        if resp.status != 200:
                            raise ConnectionError(f"Discord API returned status {resp.status}")
                        logger.info("Discord API connection successful")
            except Exception as e:
                logger.critical(f"Cannot connect to Discord API: {e}")
                return
            
            # Load core services
            logger.info("Loading core services...")
            for ext in EXTENSIONS.SERVICES:
                try:
                    logger.info(f"Loading service: {ext}")
                    await self.load_extension(ext)
                    logger.info(f"Successfully loaded service: {ext}")
                    await asyncio.sleep(1)  # Reduced sleep time
                except Exception as e:
                    logger.critical(f"Failed to load critical service {ext}: {e}")
                    await self.close()
                    return

            # Modified gateway connection check with progressive timeout
            logger.info("Waiting for gateway connection...")
            try:
                for attempt in range(self._max_retries):
                    if self.is_ready():
                        logger.info("Gateway connection already established")
                        self._gateway_connected.set()
                        break
                        
                    try:
                        timeout = min(10 * (attempt + 1), 30)  # Progressive timeout: 10, 20, 30 seconds
                        logger.info(f"Attempting gateway connection (attempt {attempt + 1}/{self._max_retries}, timeout: {timeout}s)")
                        await asyncio.wait_for(self.wait_until_ready(), timeout=timeout)
                        logger.info("Gateway connection established")
                        self._gateway_connected.set()
                        break
                    except asyncio.TimeoutError:
                        logger.warning(f"Gateway connection attempt {attempt + 1} timed out")
                        if attempt < self._max_retries - 1:
                            wait_time = 5 * (attempt + 1)
                            logger.info(f"Waiting {wait_time} seconds before next attempt...")
                            await asyncio.sleep(wait_time)
                else:
                    raise RuntimeError("Failed to establish gateway connection after maximum retries")

            except Exception as e:
                logger.critical(f"Gateway connection error: {e}")
                await self.close()
                return

            # Load remaining extensions
            if self._gateway_connected.is_set():
                await self._load_remaining_extensions()
            else:
                logger.critical("Cannot load remaining extensions: Gateway not connected")
                await self.close()
                return

            logger.info("Bot setup completed successfully")
            self._ready.set()

        except Exception as e:
            logger.critical(f"Fatal error during setup: {e}", exc_info=True)
            await self.close()

    async def _load_remaining_extensions(self):
        """Load non-critical extensions"""
        try:
            # Load LiveStockCog
            await self._load_live_stock_cog()
            
            # Load remaining features
            logger.info("Loading remaining features...")
            remaining_features = [e for e in EXTENSIONS.FEATURES if e not in ['ext.live_stock', 'ext.live_buttons']]
            for ext in remaining_features:
                try:
                    await self.load_extension(ext)
                    logger.info(f"Loaded feature: {ext}")
                except Exception as e:
                    logger.error(f"Failed to load feature {ext}: {e}")
            
            # Load optional cogs
            logger.info("Loading optional cogs...")
            for ext in EXTENSIONS.COGS:
                try:
                    await self.load_extension(ext)
                    logger.info(f"Loaded optional cog: {ext}")
                except Exception as e:
                    logger.warning(f"Failed to load optional cog {ext}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading remaining extensions: {e}")
            raise

    async def _load_live_stock_cog(self):
        """Load LiveStockCog with validation"""
        try:
            stock_channel_id = self.config['id_live_stock']
            channel = await self._verify_channel(stock_channel_id, "Stock")
            
            if not channel:
                raise RuntimeError("Stock channel not found or inaccessible")
                
            await self.load_extension('ext.live_stock')
            await asyncio.sleep(2)
            
            # Verify LiveStockCog
            if not self.get_cog('LiveStockCog'):
                raise RuntimeError("LiveStockCog failed to load properly")
                
            # Load LiveButtonsCog
            await self.load_extension('ext.live_buttons')
            if not self.get_cog('LiveButtonsCog'):
                raise RuntimeError("LiveButtonsCog failed to load properly")
                
            logger.info("Successfully loaded stock management cogs")
            
        except Exception as e:
            logger.critical(f"Failed to load stock management: {e}")
            raise

    async def _verify_channel(self, channel_id: int, channel_type: str):
        """Verify channel exists and is accessible"""
        retries = 3
        for i in range(retries):
            channel = self.get_channel(channel_id)
            if channel:
                logger.info(f"Found {channel_type} channel: {channel.name}")
                return channel
            logger.warning(f"{channel_type} channel not found, attempt {i+1}/{retries}")
            await asyncio.sleep(2)
        return None

    async def on_ready(self):
        try:
            logger.info(f"Logged in as {self.user.name} ({self.user.id})")
            logger.info(f"Discord.py Version: {discord.__version__}")
            
            # Validate channels
            logger.info("Validating channels...")
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
            if hasattr(self, 'cache_manager'):
                await self.cache_manager.cleanup_expired()
            
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks[:100]:
                task.cancel()
            
            await asyncio.gather(*tasks[:100], return_exceptions=True)
            await super().close()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
        finally:
            logger.info("Bot shutdown complete")

async def run_bot():
    """Run the bot"""
    logger.info("Initializing bot...")
    bot = StoreBot()
    
    try:
        logger.info("Starting bot...")
        async with bot:
            # Mencoba koneksi dengan token
            try:
                logger.info("Attempting to connect with token...")
                await bot.start(bot.config['token'])
            except discord.LoginFailure as e:
                logger.critical(f"Login gagal - Token tidak valid: {str(e)}")
                return
            except discord.HTTPException as e:
                logger.critical(f"HTTP Error saat koneksi: {str(e)}")
                return
            except Exception as e:
                logger.critical(f"Error tidak terduga saat login: {str(e)}")
                return
            
            # Menunggu bot siap dengan timeout
            try:
                logger.info("Waiting for bot to be ready...")
                await asyncio.wait_for(bot._ready.wait(), timeout=60)
                logger.info("Bot is ready and running!")
            except asyncio.TimeoutError:
                logger.critical("Bot gagal siap dalam waktu 60 detik")
                await bot.close()
                return
                
    except KeyboardInterrupt:
        logger.info("Menerima keyboard interrupt, menutup bot...")
    except Exception as e:
        logger.critical(f"Bot crash dengan error: {e}", exc_info=True)
    finally:
        if not bot.is_closed():
            logger.info("Menutup koneksi bot...")
            await bot.close()

if __name__ == "__main__":
    try:
        # Set waktu mulai
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting bot at {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Jalankan bot
        asyncio.run(run_bot())
        
        # Hitung durasi running
        end_time = datetime.now(timezone.utc)
        duration = end_time - start_time
        logger.info(f"Bot stopped after running for {duration}")
        
    except KeyboardInterrupt:
        logger.info("Program dihentikan oleh user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)