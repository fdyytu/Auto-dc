"""
Bot Core
Class utama untuk Discord Bot dengan struktur yang bersih
"""

import discord
from discord.ext import commands
import asyncio
import logging
from typing import Optional

from src.bot.config import config_manager
from src.bot.logging import logging_manager
from src.bot.hot_reload import HotReloadManager
from src.bot.module_loader import ModuleLoader
from src.services.cache_service import CacheManager
from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

class StoreBot(commands.Bot):
    """Bot utama untuk Discord Store"""
    
    def __init__(self):
        # Load konfigurasi
        self.config = config_manager.load_config()
        
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        # Initialize bot
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        # Initialize managers
        self.cache_manager = CacheManager()
        self.db_manager = DatabaseManager()
        self.hot_reload_manager = HotReloadManager(self)
        self.module_loader = ModuleLoader(self)
        
        # Status tracking
        self._ready = asyncio.Event()
        self._setup_done = False
    
    async def setup_hook(self):
        """Setup yang dijalankan sebelum bot login"""
        try:
            logger.info("Memulai setup bot...")
            
            # Setup database
            if not await self.db_manager.initialize():
                raise Exception("Gagal inisialisasi database")
            
            # Load semua modul menggunakan ModuleLoader
            success = await self.module_loader.load_all_modules()
            if not success:
                logger.warning("⚠️  Beberapa modul gagal dimuat, bot tetap berjalan")
            
            logger.info("Setup bot selesai")
            
        except Exception as e:
            logger.critical(f"Gagal setup bot: {e}")
            await self.close()
    

    async def on_ready(self):
        """Event ketika bot siap"""
        if not self._setup_done:
            logger.info(f"Bot login sebagai {self.user.name} ({self.user.id})")
            
            # Validasi channels
            await self._validate_channels()
            
            # Set status
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="Growtopia Shop 🏪"
            )
            await self.change_presence(activity=activity)
            
            # Cleanup cache
            await self.cache_manager.cleanup_expired()
            
            # Start hot reload manager
            await self.hot_reload_manager.start()
            
            self._setup_done = True
            self._ready.set()
            logger.info("Bot siap digunakan!")
    
    async def _validate_channels(self):
        """Validasi channel yang diperlukan"""
        required_channels = [
            ('id_live_stock', 'Live Stock'),
            ('id_log_purch', 'Purchase Log'),
            ('id_donation_log', 'Donation Log'),
            ('id_history_buy', 'Purchase History')
        ]
        
        for channel_key, channel_name in required_channels:
            channel_id = self.config.get(channel_key)
            if channel_id:
                channel = self.get_channel(channel_id)
                if not channel:
                    logger.error(f"Channel {channel_name} tidak ditemukan: {channel_id}")
                else:
                    logger.info(f"✓ {channel_name}: {channel.name}")
    
    async def close(self):
        """Cleanup sebelum shutdown"""
        try:
            logger.info("Memulai shutdown bot...")
            
            if hasattr(self, 'module_loader'):
                await self.module_loader.unload_all_cogs()
            
            if hasattr(self, 'cache_manager'):
                await self.cache_manager.clear_all()
            
            if hasattr(self, 'hot_reload_manager'):
                await self.hot_reload_manager.stop()
            
            if hasattr(self, 'db_manager'):
                await self.db_manager.close()
            
            await super().close()
            logger.info("Bot shutdown selesai")
            
        except Exception as e:
            logger.error(f"Error saat shutdown: {e}")
