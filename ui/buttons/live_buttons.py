"""
Live Buttons Manager with Shop Integration (Refactored)
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-01-XX XX:XX:XX UTC (Refactored)

Dependencies:
- ext.product_manager: For product operations
- ext.balance_manager: For balance operations
- ext.trx: For transaction operations
- ext.admin_service: For maintenance mode
- ext.constants: For configuration and responses

Refactored version dengan komponen yang dipisahkan untuk maintainability yang lebih baik.
"""

import discord
from discord.ext import commands, tasks
from discord import ui
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Union
from discord.ui import Select, Button, View

from config.constants.bot_constants import (
    COLORS,
    MESSAGES,
    BUTTON_IDS,
    CACHE_TIMEOUT,
    Status,
    UPDATE_INTERVAL,
    COG_LOADED,
    TransactionType,
    Balance,
    CURRENCY_RATES
)
from config.logging_config import get_logger

from utils.base_handler import BaseLockHandler
from services.cache_service import CacheManager
from services.product_service import ProductService
from services.balance_service import BalanceManagerService as BalanceService
from services.transaction_service import TransactionManager as TransactionService
from services.admin_service import AdminService

# Import komponen yang sudah dipisahkan
from .components import (
    QuantityModal,
    RegisterModal,
    ButtonStatistics,
    InteractionLockManager,
    RegisterButtonHandler,
    BalanceButtonHandler,
    WorldInfoButtonHandler
)

class ProductSelectView(View):
    """View untuk memilih produk yang akan dibeli"""
    
    def __init__(self, bot, products: List[Dict]):
        super().__init__(timeout=300)
        self.bot = bot
        self.products = products
        self.logger = get_logger("ProductSelectView")
        
        # Create select menu for products
        options = []
        for product in products[:25]:  # Discord limit 25 options
            stock_count = product.get('stock_count', 0)
            status_emoji = "✅" if stock_count > 0 else "❌"
            
            options.append(discord.SelectOption(
                label=f"{product['name']} ({product['code']})",
                description=f"Harga: {product['price']:,.0f} WL | Stock: {stock_count}",
                value=product['code'],
                emoji=status_emoji
            ))
        
        if options:
            select = Select(
                placeholder="Pilih produk yang ingin dibeli...",
                options=options,
                custom_id="product_select"
            )
            select.callback = self.product_select_callback
            self.add_item(select)
    
    async def product_select_callback(self, interaction: discord.Interaction):
        """Handle product selection"""
        product_code = interaction.data['values'][0]
        self.logger.info(f"[PRODUCT_SELECT] User {interaction.user.id} selected product: {product_code}")
        
        # Find selected product
        selected_product = None
        for product in self.products:
            if product['code'] == product_code:
                selected_product = product
                break
        
        if not selected_product:
            await interaction.response.send_message("❌ Produk tidak ditemukan.", ephemeral=True)
            return
        
        # Check stock
        if selected_product.get('stock_count', 0) <= 0:
            await interaction.response.send_message("❌ Produk sedang habis.", ephemeral=True)
            return
        
        # Show quantity modal
        modal = QuantityModal(product_code, selected_product.get('stock_count', 1))
        await interaction.response.send_modal(modal)

class ShopView(View):
    """Main shop view dengan buttons yang sudah direfactor"""
    
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.logger = get_logger("ShopView")
        
        # Initialize services
        self.balance_service = BalanceService(bot.db_manager)
        self.product_service = ProductService(bot.db_manager)
        self.trx_manager = TransactionService(bot.db_manager)
        self.admin_service = AdminService(bot.db_manager)
        self.cache_manager = CacheManager()
        
        # Initialize handlers
        self.register_handler = RegisterButtonHandler(bot)
        self.balance_handler = BalanceButtonHandler(bot)
        self.world_info_handler = WorldInfoButtonHandler(bot)
        
        # Initialize statistics and lock manager
        self.stats = ButtonStatistics()
        self.lock_manager = InteractionLockManager()
        
        self.logger.info("[SHOP_VIEW] ShopView initialized with refactored components")

    async def handle_with_lock(self, interaction: discord.Interaction, handler_func, button_name: str):
        """Handle interaction with proper locking"""
        interaction_id = str(interaction.id)
        
        if not await self.lock_manager.acquire_lock(interaction_id):
            await interaction.response.send_message(
                "⏳ Mohon tunggu, sedang memproses permintaan sebelumnya...", 
                ephemeral=True
            )
            return
        
        try:
            await handler_func(interaction)
            self.stats.update_stats(button_name, success=True)
        except Exception as e:
            self.logger.error(f"Error in {button_name} handler: {e}")
            self.stats.update_stats(button_name, success=False)
            
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Terjadi kesalahan saat memproses permintaan.", 
                    ephemeral=True
                )
        finally:
            self.lock_manager.release_lock(interaction_id)

    @discord.ui.button(
        label="📝 Daftar",
        style=discord.ButtonStyle.green,
        custom_id=BUTTON_IDS.REGISTER,
        row=0
    )
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button untuk registrasi GrowID"""
        await self.handle_with_lock(
            interaction, 
            self.register_handler.handle_register, 
            'register'
        )

    @discord.ui.button(
        label="💰 Saldo",
        style=discord.ButtonStyle.blurple,
        custom_id=BUTTON_IDS.BALANCE,
        row=0
    )
    async def balance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button untuk cek saldo"""
        await self.handle_with_lock(
            interaction, 
            self.balance_handler.handle_balance, 
            'balance'
        )

    @discord.ui.button(
        label="🌍 World Info",
        style=discord.ButtonStyle.secondary,
        custom_id=BUTTON_IDS.WORLD_INFO,
        row=0
    )
    async def world_info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button untuk info world"""
        await self.handle_with_lock(
            interaction, 
            self.world_info_handler.handle_world_info, 
            'world_info'
        )

    @discord.ui.button(
        label="🛒 Beli",
        style=discord.ButtonStyle.primary,
        custom_id=BUTTON_IDS.BUY,
        row=1
    )
    async def buy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button untuk membeli produk"""
        await self.handle_with_lock(interaction, self._handle_buy, 'buy')

    async def _handle_buy(self, interaction: discord.Interaction):
        """Handle buy button click"""
        self.logger.info(f"[BUTTON_BUY] User {interaction.user.id} ({interaction.user.name}) clicked buy button")
        
        await interaction.response.defer(ephemeral=True)
        
        # Check if user is registered
        growid_response = await self.balance_service.get_growid(str(interaction.user.id))
        if not growid_response.success:
            embed = discord.Embed(
                title="❌ Belum Terdaftar",
                description=MESSAGES.ERROR['NOT_REGISTERED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Get available products
        product_response = await self.product_service.get_all_products()
        if not product_response.success:
            embed = discord.Embed(
                title="❌ Error",
                description="Gagal mengambil daftar produk.",
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        products = product_response.data
        if not products:
            embed = discord.Embed(
                title="📦 Tidak Ada Produk",
                description="Saat ini tidak ada produk yang tersedia.",
                color=COLORS.WARNING
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Show product selection
        view = ProductSelectView(self.bot, products)
        embed = discord.Embed(
            title="🛒 Pilih Produk",
            description="Pilih produk yang ingin Anda beli dari menu di bawah:",
            color=COLORS.PRIMARY
        )
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(
        label="📋 Riwayat",
        style=discord.ButtonStyle.secondary,
        custom_id=BUTTON_IDS.HISTORY,
        row=1
    )
    async def history_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button untuk riwayat transaksi"""
        await self.handle_with_lock(interaction, self._handle_history, 'history')

    async def _handle_history(self, interaction: discord.Interaction):
        """Handle history button click"""
        self.logger.info(f"[BUTTON_HISTORY] User {interaction.user.id} ({interaction.user.name}) clicked history button")
        
        await interaction.response.defer(ephemeral=True)
        
        # Check if user is registered
        growid_response = await self.balance_service.get_growid(str(interaction.user.id))
        if not growid_response.success:
            embed = discord.Embed(
                title="❌ Belum Terdaftar",
                description=MESSAGES.ERROR['NOT_REGISTERED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Get transaction history
        history_response = await self.trx_manager.get_user_transactions(growid_response.data, limit=10)
        if not history_response.success:
            embed = discord.Embed(
                title="❌ Error",
                description=history_response.error,
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        transactions = history_response.data
        if not transactions:
            embed = discord.Embed(
                title="📋 Riwayat Transaksi",
                description="Anda belum memiliki riwayat transaksi.",
                color=COLORS.INFO
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Create history embed
        embed = discord.Embed(
            title="📋 Riwayat Transaksi",
            description=f"10 transaksi terakhir untuk **{growid_response.data}**",
            color=COLORS.INFO,
            timestamp=datetime.utcnow()
        )
        
        for i, trx in enumerate(transactions[:10], 1):
            trx_type = "🛒 Pembelian" if trx['type'] == 'purchase' else "💰 Deposit"
            embed.add_field(
                name=f"{i}. {trx_type}",
                value=f"**Jumlah:** {trx['amount']:,.0f} WL\n**Waktu:** {trx['created_at']}",
                inline=True
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    def get_button_health_report(self) -> str:
        """Get button health report"""
        return self.stats.get_health_report()

class LiveButtonManager(BaseLockHandler):
    """Manager untuk live buttons yang sudah direfactor"""
    
    def __init__(self, bot):
        if not hasattr(self, 'initialized') or not self.initialized:
            super().__init__()
            self.bot = bot
            self.logger = get_logger("LiveButtonManager")
            self.cache_manager = CacheManager()
            self.admin_service = AdminService(bot.db_manager)
            self.stock_channel_id = int(self.bot.config.get('id_live_stock', 0))
            self.current_message = None
            self.stock_manager = None
            self._ready = asyncio.Event()
            self.initialized = True
            self.logger.info("LiveButtonManager initialized (refactored)")

    def create_view(self):
        """Create shop view with buttons"""
        self.logger.info("[VIEW_CREATION] Creating new ShopView with refactored components")
        view = ShopView(self.bot)
        self.logger.debug(f"[VIEW_CREATION] ShopView created with {len(view.children)} buttons")
        return view

    def get_button_health_report(self):
        """Get button health report from current view"""
        try:
            temp_view = ShopView(self.bot)
            return temp_view.get_button_health_report()
        except Exception as e:
            self.logger.error(f"Error getting button health report: {e}")
            return "Unable to generate button health report"

    async def set_stock_manager(self, stock_manager):
        """Set stock manager untuk integrasi"""
        self.stock_manager = stock_manager
        self._ready.set()
        self.logger.info("Stock manager set successfully")
        await self.force_update()

    async def get_or_create_message(self) -> Optional[discord.Message]:
        """Create or get existing message with both stock display and buttons"""
        self.logger.info("[MESSAGE_MANAGEMENT] Getting or creating live stock message")
        try:
            channel = self.bot.get_channel(self.stock_channel_id)
            if not channel:
                self.logger.error(f"[MESSAGE_MANAGEMENT] Channel stock dengan ID {self.stock_channel_id} tidak ditemukan")
                return None

            # First check if stock manager has a valid message
            if self.stock_manager and self.stock_manager.current_stock_message:
                self.current_message = self.stock_manager.current_stock_message
                # Update buttons only
                view = self.create_view()
                await self.current_message.edit(view=view)
                return self.current_message

            # Find last message if exists
            if self.stock_manager:
                existing_message = await self.stock_manager.find_last_message()
                if existing_message:
                    self.current_message = existing_message
                    # Update both stock manager and button manager references
                    self.stock_manager.current_stock_message = existing_message

                    # Update embed and view
                    embed = await self.stock_manager.create_stock_embed()
                    view = self.create_view()
                    await existing_message.edit(embed=embed, view=view)
                    return existing_message

            # Create new message if none found
            if self.stock_manager:
                embed = await self.stock_manager.create_stock_embed()
            else:
                embed = discord.Embed(
                    title="🏪 Live Stock",
                    description=MESSAGES.INFO['INITIALIZING'],
                    color=COLORS.WARNING
                )

            view = self.create_view()
            self.current_message = await channel.send(embed=embed, view=view)

            # Update stock manager reference
            if self.stock_manager:
                self.stock_manager.current_stock_message = self.current_message

            return self.current_message

        except Exception as e:
            self.logger.error(f"Error in get_or_create_message: {e}")
            return None

    async def force_update(self):
        """Force update display"""
        try:
            await self.get_or_create_message()
            self.logger.info("Force update completed")
        except Exception as e:
            self.logger.error(f"Error in force_update: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        try:
            self.logger.info("Cleaning up LiveButtonManager...")
            # Add cleanup logic here if needed
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

class LiveButtonsCog(commands.Cog):
    """Cog untuk live buttons yang sudah direfactor"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger("LiveButtonsCog")
        self.button_manager = LiveButtonManager(bot)
        self.stock_manager = None
        self._ready = asyncio.Event()
        self.logger.info("LiveButtonsCog initialized (refactored)")

    async def initialize_dependencies(self) -> bool:
        """Initialize dependencies dengan timeout"""
        try:
            self.logger.info("Initializing dependencies...")
            
            # Wait for LiveStockCog
            max_attempts = 30
            for attempt in range(max_attempts):
                self.stock_manager = self.bot.get_cog('LiveStockCog')
                if self.stock_manager and hasattr(self.stock_manager, 'stock_manager'):
                    await self.button_manager.set_stock_manager(self.stock_manager.stock_manager)
                    self.logger.info("LiveStockCog found and connected")
                    break
                
                self.logger.debug(f"Waiting for LiveStockCog... attempt {attempt + 1}/{max_attempts}")
                await asyncio.sleep(1)
            else:
                self.logger.warning("LiveStockCog not found after waiting")
                return False

            self.logger.info("Dependencies initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing dependencies: {e}", exc_info=True)
            return False

    async def cog_load(self):
        """Setup when cog is loaded"""
        try:
            self.logger.info("LiveButtonsCog loading...")

            # Initialize dependencies with timeout
            try:
                async with asyncio.timeout(45):
                    success = await self.initialize_dependencies()
                    if not success:
                        raise RuntimeError("Failed to initialize dependencies")
                    self.logger.info("Dependencies initialized successfully")
            except asyncio.TimeoutError:
                self.logger.error("Initialization timed out")
                raise

            # Start background task
            self.check_display.start()
            self.logger.info("LiveButtonsCog loaded successfully (refactored)")

        except Exception as e:
            self.logger.error(f"Error in cog_load: {e}")
            raise

    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        try:
            self.check_display.cancel()
            await self.button_manager.cleanup()
            self.logger.info("LiveButtonsCog unloaded (refactored)")
        except Exception as e:
            self.logger.error(f"Error in cog_unload: {e}")

    @tasks.loop(minutes=5.0)
    async def check_display(self):
        """Periodically check and update display"""
        if not self._ready.is_set():
            return

        try:
            message = self.button_manager.current_message
            if not message:
                await self.button_manager.get_or_create_message()
            else:
                # Hanya update embed, TIDAK update view
                if self.stock_manager:
                    embed = await self.stock_manager.stock_manager.create_stock_embed()
                    await message.edit(embed=embed)
        except Exception as e:
            self.logger.error(f"Error in check_display: {e}")

    @check_display.before_loop
    async def before_check_display(self):
        """Wait until ready before starting the loop"""
        await self.bot.wait_until_ready()
        await self._ready.wait()

async def setup(bot):
    """Setup cog dengan proper error handling"""
    logger = get_logger("LiveButtonsCog.setup")
    try:
        if not hasattr(bot, COG_LOADED['LIVE_BUTTONS']):
            logger.info("Setting up LiveButtonsCog (refactored)...")
            
            # Tunggu LiveStockCog tersedia
            stock_cog = bot.get_cog('LiveStockCog')
            if not stock_cog:
                logger.warning("LiveStockCog not found, will wait for it during initialization")

            cog = LiveButtonsCog(bot)
            await bot.add_cog(cog)
            logger.info("LiveButtonsCog added to bot (refactored)")

            # Wait for initialization with timeout
            try:
                async with asyncio.timeout(45):
                    await cog._ready.wait()
                    logger.info("LiveButtonsCog initialization completed (refactored)")
            except asyncio.TimeoutError:
                logger.error("LiveButtonsCog initialization timed out")
                await bot.remove_cog('LiveButtonsCog')
                raise RuntimeError("Initialization timed out")

            setattr(bot, COG_LOADED['LIVE_BUTTONS'], True)
            logger.info("LiveButtons cog loaded successfully (refactored)")

    except Exception as e:
        logger.error(f"Failed to load LiveButtonsCog: {e}", exc_info=True)
        if hasattr(bot, COG_LOADED['LIVE_BUTTONS']):
            delattr(bot, COG_LOADED['LIVE_BUTTONS'])
        raise

async def teardown(bot):
    """Cleanup when unloading the cog"""
    try:
        cog = bot.get_cog('LiveButtonsCog')
        if cog:
            await bot.remove_cog('LiveButtonsCog')
        if hasattr(bot, COG_LOADED['LIVE_BUTTONS']):
            delattr(bot, COG_LOADED['LIVE_BUTTONS'])
        logging.info("LiveButtons cog unloaded successfully (refactored)")
    except Exception as e:
        logging.error(f"Error unloading LiveButtonsCog: {e}")
