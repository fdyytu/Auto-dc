"""
Live Stock Manager
Author: fdyytu
Created at: 2025-03-07 18:30:16 UTC
Last Modified: 2025-03-12 04:39:37 UTC

Dependencies:
- ext.product_manager: For product operations
- ext.balance_manager: For balance operations
- ext.trx: For transaction operations
- ext.admin_service: For maintenance mode
- ext.constants: For configuration and responses
"""

import discord
from discord.ext import commands, tasks
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict
from discord import ui

from src.config.constants.bot_constants import (
    COLORS,
    MESSAGES,
    UPDATE_INTERVAL,
    CACHE_TIMEOUT,
    Status,
    CURRENCY_RATES,
    COG_LOADED,
    Stock
)
from src.config.logging_config import get_logger
from src.utils.base_handler import BaseLockHandler
from src.services.cache_service import CacheManager
from src.services.product_service import ProductService
from src.services.balance_service import BalanceManagerService as BalanceService
from src.services.transaction_service import TransactionManager as TransactionService
from src.services.admin_service import AdminService

class LiveStockManager(BaseLockHandler):
    def __init__(self, bot):
        if not hasattr(self, 'initialized') or not self.initialized:
            super().__init__()
            self.bot = bot
            self.logger = get_logger("LiveStockManager")
            self.cache_manager = CacheManager()

            # Initialize services
            self.product_service = ProductService(bot.db_manager)
            self.balance_service = BalanceService(bot.db_manager)
            self.trx_manager = TransactionService(bot.db_manager)
            self.admin_service = AdminService(bot.db_manager)

            # Channel configuration
            self.stock_channel_id = int(self.bot.config.get('id_live_stock', 0))
            self.current_stock_message = None
            self.button_manager = None
            self._ready = asyncio.Event()
            self.initialized = True
            self.logger.info("LiveStockManager initialized")

    async def initialize(self):
        """Initialize manager and set ready state"""
        if not self._ready.is_set():
            self._ready.set()
            self.logger.info("LiveStockManager is ready")

    async def find_last_message(self) -> Optional[discord.Message]:
        """Cari pesan terakhir yang dikirim bot di channel"""
        try:
            channel = self.bot.get_channel(self.stock_channel_id)
            if not channel:
                return None
                
            # Cari pesan terakhir dari bot di channel
            async for message in channel.history(limit=50):  # Batasi 50 pesan terakhir
                if (message.author == self.bot.user and 
                    len(message.embeds) > 0 and 
                    message.embeds[0].title and 
                    "Growtopia Shop Status" in message.embeds[0].title):
                    return message
            return None
        except Exception as e:
            self.logger.error(f"Error finding last message: {e}")
            return None

    async def set_button_manager(self, button_manager):
        """Set button manager untuk integrasi"""
        self.button_manager = button_manager
        self.logger.info("Button manager set successfully")

    async def create_stock_embed(self) -> discord.Embed:
        """Buat embed untuk display stock dengan tema modern"""
        try:
            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                return discord.Embed(
                    title="🔧 Sistem dalam Maintenance",
                    description=MESSAGES.INFO['MAINTENANCE'],
                    color=COLORS.WARNING,
                    timestamp=datetime.utcnow()
                )

            # Get products dari ProductManager dengan proper response handling
            cache_key = 'all_products_display'
            cached_products = await self.cache_manager.get(cache_key)

            if not cached_products:
                product_response = await self.product_service.get_all_products()
                if not product_response.success:
                    raise ValueError(product_response.error)
                products = product_response.data
                await self.cache_manager.set(
                    cache_key,
                    products,
                    expires_in=CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.SHORT)
                )
            else:
                products = cached_products

            # Create modern embed with dark theme
            embed = discord.Embed(
                title="🏪 Growtopia Shop Status",
                description=(
                    "```ansi\n"
                    "\u001b[0;37mSelamat datang di \u001b[0;33mGrowtopia Shop\u001b[0m!\n"
                    "\u001b[0;90mReal-time stock monitoring system\u001b[0m\n"
                    "```"
                ),
                color=discord.Color.from_rgb(32, 34, 37)  # Discord dark theme color
            )

            # Server time dengan format modern
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            embed.add_field(
                name="⏰ Server Time",
                value=f"```ansi\n\u001b[0;36m{current_time} UTC\u001b[0m```",
                inline=False
            )

            try:
                # Grouping products by category
                categories = {}
                for product in products:
                    category = product.get('category', 'Other')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(product)

                for category, category_products in categories.items():
                    # Category header dengan styling
                    category_header = f"\n__**{category}**__\n"
                    category_items = []

                    for product in category_products:
                        try:
                            # Get stock count dengan caching
                            stock_cache_key = f'stock_count_{product["code"]}'
                            stock_count = await self.cache_manager.get(stock_cache_key)

                            if stock_count is None:
                                stock_response = await self.product_service.get_stock_count(product['code'])
                                if not stock_response.success:
                                    continue
                                stock_count = stock_response.data
                                await self.cache_manager.set(
                                    stock_cache_key,
                                    stock_count,
                                    expires_in=CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.SHORT)
                                )

                            # Status indicators dengan warna
                            if stock_count > Stock.ALERT_THRESHOLD:
                                status_color = "32"  # Green
                                status_emoji = "🟢"
                            elif stock_count > 0:
                                status_color = "33"  # Yellow
                                status_emoji = "🟡"
                            else:
                                status_color = "31"  # Red
                                status_emoji = "🔴"

                            # Format price menggunakan currency rates
                            price = float(product['price'])
                            price_display = self._format_price(price)

                            # Product display dengan ANSI formatting
                            product_info = (
                                f"```ansi\n"
                                f"{status_emoji} \u001b[0;{status_color}m{product['name']}\u001b[0m\n"
                                f"└─ Price : {price_display}\n"
                                f"└─ Stock : {stock_count} unit\n"
                            )

                            if product.get('description'):
                                product_info += f"└─ Info  : {product['description']}\n"

                            product_info += "```"
                            category_items.append(product_info)

                        except Exception as e:
                            self.logger.error(f"Error processing product {product.get('name', 'Unknown')}: {e}")
                            continue

                    if category_items:
                        items_text = "\n".join(category_items)
                        embed.add_field(
                            name=category_header,
                            value=items_text,
                            inline=False
                        )

            except Exception as e:
                self.logger.error(f"Error processing categories: {e}")
                raise

            # Footer dengan update info
            embed.set_footer(
                text=f"Auto-update every {int(UPDATE_INTERVAL.LIVE_STOCK)} seconds • Last Update"
            )
            embed.timestamp = datetime.utcnow()

            return embed

        except Exception as e:
            self.logger.error(f"Error creating stock embed: {e}")
            return discord.Embed(
                title="❌ System Error",
                description=MESSAGES.ERROR['DISPLAY_ERROR'],
                color=COLORS.ERROR
            )

    def _format_price(self, price: float) -> str:
        """Format price dengan currency rates dari constants"""
        try:
            if price >= CURRENCY_RATES['BGL']:
                return f"\u001b[0;35m{price/CURRENCY_RATES['BGL']:.1f} BGL\u001b[0m"
            elif price >= CURRENCY_RATES['DL']:
                return f"\u001b[0;34m{price/CURRENCY_RATES['DL']:.0f} DL\u001b[0m"
            return f"\u001b[0;32m{int(price)} WL\u001b[0m"
        except Exception:
            return "Invalid Price"

    async def update_stock_display(self) -> bool:
        """Update tampilan stock dengan tombol yang selalu ada"""
        try:
            channel = self.bot.get_channel(self.stock_channel_id)
            if not channel:
                self.logger.error(f"Channel stock dengan ID {self.stock_channel_id} tidak ditemukan")
                return False

            embed = await self.create_stock_embed()

            # Cari pesan yang ada jika belum ada current_message
            if not self.current_stock_message:
                self.current_stock_message = await self.find_last_message()

            # Buat view/tombol untuk update
            view = None
            if self.button_manager:
                try:
                    view = self.button_manager.create_view()
                    self.logger.debug("Tombol berhasil dibuat untuk update stock")
                except Exception as button_error:
                    self.logger.error(f"Error membuat tombol: {button_error}", exc_info=True)

            if not self.current_stock_message:
                # Buat pesan baru jika tidak ada yang ditemukan
                self.logger.info("Membuat pesan live stock baru dengan tombol")
                self.current_stock_message = await channel.send(embed=embed, view=view)
                if view:
                    self.logger.info("✅ Pesan baru berhasil dibuat dengan tombol")
                else:
                    self.logger.warning("⚠️ Pesan baru dibuat tanpa tombol")
                return True

            try:
                # Update pesan yang ada dengan embed DAN view
                if view:
                    await self.current_stock_message.edit(embed=embed, view=view)
                    self.logger.debug("✅ Pesan diupdate dengan embed dan tombol")
                else:
                    await self.current_stock_message.edit(embed=embed)
                    self.logger.warning("⚠️ Pesan diupdate hanya dengan embed (tanpa tombol)")
                return True

            except discord.NotFound:
                self.logger.warning(MESSAGES.WARNING['MESSAGE_NOT_FOUND'])
                self.current_stock_message = None
                # Buat pesan baru karena pesan lama tidak ditemukan
                self.logger.info("Membuat pesan baru karena pesan lama tidak ditemukan")
                self.current_stock_message = await channel.send(embed=embed, view=view)
                if view:
                    self.logger.info("✅ Pesan pengganti berhasil dibuat dengan tombol")
                else:
                    self.logger.warning("⚠️ Pesan pengganti dibuat tanpa tombol")
                return True

        except Exception as e:
            self.logger.error(f"Error updating stock display: {e}", exc_info=True)
            return False

    async def cleanup(self):
        """Cleanup resources dengan proper error handling"""
        try:
            if self.current_stock_message:
                embed = discord.Embed(
                    title="🔧 Maintenance",
                    description=MESSAGES.INFO['MAINTENANCE'],
                    color=COLORS.WARNING
                )
                await self.current_stock_message.edit(embed=embed)

            # Clear caches dengan pattern yang spesifik
            cache_keys = [
                'live_stock_message_id',
                'stock_count_all',
                'all_products_display',
                'world_info',
                'available_products'
            ]
            for key in cache_keys:
                try:
                    await self.cache_manager.delete(key)
                except Exception as cache_error:
                    self.logger.debug(f"Failed to delete cache key {key}: {cache_error}")

            self.logger.info("LiveStockManager cleanup completed")

        except Exception as e:
            self.logger.error(f"Error in cleanup: {e}")

class LiveStockCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stock_manager = LiveStockManager(bot)
        self.logger = get_logger("LiveStockCog")
        self._ready = asyncio.Event()
        self.update_stock_task = None
        self.logger.info("LiveStockCog instance created")
        asyncio.create_task(self.stock_manager.initialize())

    async def start_tasks(self):
        """Start background tasks safely"""
        try:
            self.logger.info("Attempting to start stock update task...")
            self.update_stock_task = self.update_stock.start()
            self.logger.info("Stock update task started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start tasks: {e}")
            raise

    async def cog_load(self):
        """Setup when cog is loaded"""
        try:
            self.logger.info("LiveStockCog loading...")
            
            # Setup dasar tanpa menunggu bot ready
            self._ready.set()  # Set ready flag awal
            
            # Schedule delayed setup
            self.bot.loop.create_task(self.delayed_setup())
            self.logger.info("LiveStockCog base loading complete")
    
        except Exception as e:
            self.logger.error(f"Error in cog_load: {e}")
            raise
    
    async def delayed_setup(self):
        """Setup yang membutuhkan bot ready"""
        try:
            self.logger.info("Starting delayed setup...")
            
            # Tunggu bot ready dengan timeout
            try:
                self.logger.info("Waiting for bot to be ready...")
                await asyncio.wait_for(self.bot.wait_until_ready(), timeout=30.0)
                self.logger.info("Bot is ready, proceeding with initialization...")
            except asyncio.TimeoutError:
                self.logger.error("Timeout waiting for bot ready")
                return
    
            # Initialize channel
            channel = self.bot.get_channel(self.stock_manager.stock_channel_id)
            if not channel:
                self.logger.error(f"Stock channel {self.stock_manager.stock_channel_id} not found")
                return
            else:
                self.logger.info(f"✓ Live stock channel found: {channel.name} (ID: {channel.id})")
            
            # Start background tasks
            await self.start_tasks()
            self.logger.info("LiveStockCog fully initialized and ready")
    
        except Exception as e:
            self.logger.error(f"Error in delayed setup: {e}", exc_info=True)

    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        try:
            if self.update_stock_task:
                self.update_stock_task.cancel()
            await self.stock_manager.cleanup()
            self.logger.info("LiveStockCog unloaded")
        except Exception as e:
            self.logger.error(f"Error in cog_unload: {e}")

    @tasks.loop(seconds=UPDATE_INTERVAL.LIVE_STOCK)
    async def update_stock(self):
        """Update stock display periodically with better error handling"""
        if not self._ready.is_set():
            self.logger.debug("Stock manager not ready, skipping update")
            return

        try:
            self.logger.debug(f"Running stock update loop (interval: {UPDATE_INTERVAL.LIVE_STOCK}s)")
            await self.stock_manager.update_stock_display()
            self.logger.debug("Stock update completed successfully")
        except Exception as e:
            self.logger.error(f"Error in stock update loop: {e}", exc_info=True)
            # Try to restart the task if it fails
            if not self.update_stock.is_running():
                self.logger.info("Restarting stock update task...")
                self.update_stock.restart()

    @update_stock.before_loop
    async def before_update_stock(self):
        """Wait until bot is ready before starting the loop"""
        await self.bot.wait_until_ready()

async def setup(bot):
    """Setup cog dengan proper error handling"""
    logger = get_logger("LiveStockCog.setup")
    try:
        if not hasattr(bot, COG_LOADED['LIVE_STOCK']):
            logger.info("Setting up LiveStockCog...")
            
            # Validate stock channel exists
            stock_channel_id = int(bot.config.get('id_live_stock', 0))
            if stock_channel_id == 0:
                logger.error("Live stock channel ID not configured in config.json")
                raise RuntimeError("Live stock channel not configured")
            
            logger.info(f"Live stock channel ID from config: {stock_channel_id}")
            
            cog = LiveStockCog(bot)
            await bot.add_cog(cog)
            logger.info("LiveStockCog added to bot")
            
            # Tunggu stock manager ready dengan timeout yang lebih panjang
            try:
                await asyncio.wait_for(cog.stock_manager._ready.wait(), timeout=30.0)
                logger.info("Stock manager is ready")
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for stock manager initialization")
                raise RuntimeError("Stock manager initialization timeout")
                
            setattr(bot, COG_LOADED['LIVE_STOCK'], True)
            logger.info(f'✓ LiveStock cog loaded successfully at {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC')
            return True
        else:
            logger.info("LiveStockCog already loaded, skipping...")
            return True
    except Exception as e:
        logger.error(f"Failed to load LiveStock cog: {e}", exc_info=True)
        if hasattr(bot, COG_LOADED['LIVE_STOCK']):
            delattr(bot, COG_LOADED['LIVE_STOCK'])
        raise

async def teardown(bot):
    """Cleanup when extension is unloaded"""
    try:
        if hasattr(bot, COG_LOADED['LIVE_STOCK']):
            cog = bot.get_cog('LiveStockCog')
            if cog:
                await bot.remove_cog('LiveStockCog')
                if hasattr(cog, 'stock_manager'):
                    await cog.stock_manager.cleanup()
            delattr(bot, COG_LOADED['LIVE_STOCK'])
            logging.info("LiveStock extension unloaded successfully")
    except Exception as e:
        logging.error(f"Error unloading LiveStock extension: {e}")
