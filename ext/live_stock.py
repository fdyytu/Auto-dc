"""
Live Stock Manager
Author: fdyytu
Created at: 2025-03-07 18:30:16 UTC
Last Modified: 2025-03-10 09:57:11 UTC

Dependencies:
- ext.product_manager: For product operations
- ext.balance_manager: For balance operations
- ext.trx: For transaction operations
- ext.admin_service: For maintenance mode
- ext.constants: For configuration and responses
- ext.live_buttons: For button integration
"""

import discord
from discord.ext import commands, tasks
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict

from .constants import (
    COLORS,
    MESSAGES,
    UPDATE_INTERVAL,
    CACHE_TIMEOUT,
    Stock,
    Status,
    CURRENCY_RATES,
    COG_LOADED,
    VERSION
)
from .base_handler import BaseLockHandler
from .cache_manager import CacheManager
from .product_manager import ProductManagerService
from .balance_manager import BalanceManagerService 
from .trx import TransactionManager
from .admin_service import AdminService

class LiveStockManager(BaseLockHandler):
    _instance = None
    _instance_lock = asyncio.Lock()

    def __new__(cls, bot):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, bot):
        if not self.initialized:
            super().__init__()
            self.bot = bot
            self.version = VERSION.LIVE_STOCK
            self.logger = logging.getLogger("LiveStockManager")
            self.cache_manager = CacheManager()
            self.stock_channel_id = int(self.bot.config.get('id_live_stock', 0))
            self.current_stock_message = None
            self.button_manager = None
            self._ready = asyncio.Event()
            self.initialized = True
            
    async def initialize_services(self):
        """Initialize services after bot is ready"""
        try:
            self.product_service = ProductManagerService(self.bot)
            self.balance_service = BalanceManagerService(self.bot)
            self.trx_manager = TransactionManager(self.bot)
            self.admin_service = AdminService(self.bot)
            self._ready.set()
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            return False

    async def wait_until_ready(self, timeout=30):
        """Wait until manager is ready"""
        try:
            await asyncio.wait_for(self._ready.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def set_button_manager(self, button_manager):
        """Set button manager untuk integrasi"""
        if not self._ready.is_set():
            await self.wait_until_ready()
        self.button_manager = button_manager
        self.logger.info(f"Button manager set successfully (version: {button_manager.version})")

    async def create_stock_embed(self) -> discord.Embed:
        """Buat embed untuk display stock dengan data dari ProductManager"""
        try:
            if not self._ready.is_set():
                return discord.Embed(
                    title="⏳ Initializing",
                    description=MESSAGES.INFO['INITIALIZING'],
                    color=COLORS.WARNING
                )

            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                return discord.Embed(
                    title="🔧 Maintenance Mode",
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
            
            embed = discord.Embed(
                title="🏪 Live Stock Status",
                description=(
                    "```yml\n"
                    "Selamat datang di Growtopia Shop!\n"
                    "Stock dan harga diperbarui secara real-time\n"
                    "```"
                ),
                color=COLORS.INFO
            )

            # Format waktu server
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            embed.add_field(
                name="🕒 Server Time",
                value=f"```{current_time} UTC```",
                inline=False
            )

            # Display products dengan format yang lebih rapi
            for product in products:
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
                    
                    # Status emoji based on stock level
                    status_emoji = "🟢" if stock_count > Stock.ALERT_THRESHOLD else "🟡" if stock_count > 0 else "🔴"
                    
                    # Format price using currency rates from constants
                    price = float(product['price'])
                    price_display = self._format_price(price)

                    field_value = (
                        "```yml\n"
                        f"Price : {price_display}\n"
                        f"Stock : {stock_count} unit\n"
                        "```"
                    )
                    
                    # Add description if exists
                    if product.get('description'):
                        field_value = field_value[:-3] + f"Info  : {product['description']}\n```"
                    
                    embed.add_field(
                        name=f"{status_emoji} {product['name']}",
                        value=field_value,
                        inline=True
                    )

                except Exception as e:
                    self.logger.error(f"Error processing product {product.get('name', 'Unknown')}: {e}")
                    continue

            embed.set_footer(text=f"Auto-update setiap {int(UPDATE_INTERVAL.LIVE_STOCK)} detik")
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
                return f"{price/CURRENCY_RATES['BGL']:.1f} BGL"
            elif price >= CURRENCY_RATES['DL']:
                return f"{price/CURRENCY_RATES['DL']:.0f} DL"
            return f"{int(price)} WL"
        except Exception:
            return "Invalid Price"

    async def update_stock_display(self) -> bool:
        """Update tampilan stock dengan proper error handling"""
        try:
            if not self._ready.is_set():
                self.logger.warning("Attempting to update before initialization")
                return False

            if not self.current_stock_message or not self.button_manager:
                channel = self.bot.get_channel(self.stock_channel_id)
                if channel:
                    embed = await self.create_stock_embed()
                    view = self.button_manager.create_view() if self.button_manager else None
                    self.current_stock_message = await channel.send(embed=embed, view=view)
                    return True
                return False

            embed = await self.create_stock_embed()
            view = self.button_manager.create_view() if self.button_manager else None
            await self.current_stock_message.edit(embed=embed, view=view)
            return True

        except discord.NotFound:
            self.logger.warning(MESSAGES.WARNING['MESSAGE_NOT_FOUND'])
            self.current_stock_message = None
            return False
            
        except discord.HTTPException as e:
            self.logger.error(f"HTTP error updating stock display: {e}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating stock display: {e}")
            try:
                error_embed = discord.Embed(
                    title="❌ System Error",
                    description=MESSAGES.ERROR['DISPLAY_ERROR'],
                    color=COLORS.ERROR
                )
                await self.current_stock_message.edit(embed=error_embed)
            except:
                pass
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
                
            # Clear caches
            patterns = [
                'all_products_display',
                'stock_count_*'
            ]
            for pattern in patterns:
                try:
                    await self.cache_manager.delete_pattern(pattern)
                except AttributeError:
                    # Fallback untuk cache manager yang tidak support pattern
                    if pattern.endswith('*'):
                        continue
                    await self.cache_manager.delete(pattern)
                    
            self._ready.clear()
            self.logger.info("LiveStockManager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error in cleanup: {e}")

class LiveStockCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stock_manager = LiveStockManager(bot)
        self.logger = logging.getLogger("LiveStockCog")
        self._initialization_lock = asyncio.Lock()
        
    # Tambahkan method ini 
    async def _validate_channel(self):
        """Validate stock channel exists"""
        channel_id = self.bot.config['id_live_stock']
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            self.logger.error(f"Stock channel with ID {channel_id} not found")
            return False
            
        self.channel = channel
        return True
    
    async def cog_load(self):
        """Setup when cog is loaded"""
        try:
            # Validate channel first
            if not await self._validate_channel():
                raise RuntimeError("Stock channel validation failed")
                
            async with self._initialization_lock:
                async with asyncio.timeout(30):  # 30 second timeout
                    # Initialize stock manager
                    self.stock_manager = LiveStockManager(self.bot, self.channel)
                    
                    # Initialize services
                    if not await self.stock_manager.initialize_services():
                        raise RuntimeError("Failed to initialize LiveStock services")
                    
                    # Set ready state
                    self.stock_manager._ready.set()
                    
                    # Start update loop
                    self.update_stock.start()
                    self.logger.info("LiveStock cog loaded and started successfully")
                    
        except asyncio.TimeoutError:
            self.logger.error("LiveStock initialization timed out")
            raise
        except Exception as e:
            self.logger.error(f"Error in cog_load: {e}")
            raise
    
    def cog_unload(self):
        """Cleanup when unloading"""
        try:
            self.update_stock.cancel()
            asyncio.create_task(self.stock_manager.cleanup())
            self.logger.info("LiveStock cog unloaded successfully")
        except Exception as e:
            self.logger.error(f"Error in cog_unload: {e}")
            

    @tasks.loop(seconds=UPDATE_INTERVAL.LIVE_STOCK)
    async def update_stock(self):
        """Update stock display periodically"""
        try:
            # Skip if not ready
            if not self.stock_manager._ready.is_set():
                return

            # Check button manager connection
            if not self.stock_manager.button_manager:
                self.logger.warning("Button manager not connected, attempting to reconnect...")
                button_cog = self.bot.get_cog('LiveButtonsCog')
                if button_cog and button_cog.button_manager:
                    await self.stock_manager.set_button_manager(button_cog.button_manager)

            # Dapatkan channel
            channel = self.bot.get_channel(self.stock_manager.stock_channel_id)
            if not channel:
                self.logger.error(f"Channel stock dengan ID {self.stock_manager.stock_channel_id} tidak ditemukan")
                return

            # Update stock display
            if not self.stock_manager.current_stock_message:
                # Buat pesan baru jika belum ada
                embed = await self.stock_manager.create_stock_embed()
                view = self.stock_manager.button_manager.create_view() if self.stock_manager.button_manager else None
                self.stock_manager.current_stock_message = await channel.send(embed=embed, view=view)
            else:
                # Update pesan yang ada dengan mempertahankan view
                try:
                    embed = await self.stock_manager.create_stock_embed()
                    view = self.stock_manager.button_manager.create_view() if self.stock_manager.button_manager else None
                    await self.stock_manager.current_stock_message.edit(embed=embed, view=view)
                except discord.NotFound:
                    # Pesan tidak ditemukan, buat pesan baru
                    self.logger.warning("Pesan stock tidak ditemukan, membuat pesan baru...")
                    self.stock_manager.current_stock_message = None
                    embed = await self.stock_manager.create_stock_embed()
                    view = self.stock_manager.button_manager.create_view() if self.stock_manager.button_manager else None
                    self.stock_manager.current_stock_message = await channel.send(embed=embed, view=view)
                except Exception as e:
                    self.logger.error(f"Error updating stock message: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in stock update loop: {e}")

    @update_stock.before_loop
    async def before_update_stock(self):
        """Wait until bot and manager are ready"""
        await self.bot.wait_until_ready()
        await self.stock_manager.wait_until_ready()
        
        # Pastikan channel ada
        channel = self.bot.get_channel(self.stock_manager.stock_channel_id)
        if not channel:
            self.logger.error(f"Channel stock dengan ID {self.stock_manager.stock_channel_id} tidak ditemukan")
            return
            
        # Hapus pesan lama di channel jika ada
        try:
            await channel.purge(limit=1)
        except Exception as e:
            self.logger.error(f"Error clearing channel: {e}")

async def setup(bot):
    """Setup cog dengan proper error handling"""
    if not hasattr(bot, COG_LOADED['LIVE_STOCK']):
        try:
            await bot.add_cog(LiveStockCog(bot))
            setattr(bot, COG_LOADED['LIVE_STOCK'], True)
            logging.info(
                f'LiveStock cog loaded successfully at '
                f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC'
            )
        except Exception as e:
            logging.error(f"Failed to load LiveStock cog: {e}")
            if hasattr(bot, COG_LOADED['LIVE_STOCK']):
                delattr(bot, COG_LOADED['LIVE_STOCK'])
            raise

async def teardown(bot):
    """Clean up resources when unloading the cog"""
    try:
        cog = bot.get_cog('LiveStockCog')
        if cog:
            await bot.remove_cog('LiveStockCog')
        if hasattr(bot, COG_LOADED['LIVE_STOCK']):
            delattr(bot, COG_LOADED['LIVE_STOCK'])
        logging.info("LiveStock cog unloaded successfully")
    except Exception as e:
        logging.error(f"Error unloading LiveStock cog: {e}")