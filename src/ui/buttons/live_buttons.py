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
import re
from datetime import datetime
from typing import List, Dict, Optional, Union
from discord.ui import Select, Button, View

from src.config.constants.bot_constants import (
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
from src.config.logging_config import get_logger

from src.utils.base_handler import BaseLockHandler
from src.services.cache_service import CacheManager
from src.services.product_service import ProductService
from src.services.balance_service import BalanceManagerService as BalanceService
from src.services.transaction_service import TransactionManager as TransactionService
from src.services.admin_service import AdminService

# Import komponen yang sudah dipisahkan
from .components import (
    QuantityModal,
    RegisterModal,
    BuyModal,
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
        self.trx_manager = TransactionService(bot)
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
        """Handle buy button click - langsung buka modal"""
        self.logger.info(f"[BUTTON_BUY] User {interaction.user.id} ({interaction.user.name}) clicked buy button")
        
        # Check if user is registered first
        growid_response = await self.balance_service.get_growid(str(interaction.user.id))
        if not growid_response.success:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Belum Terdaftar",
                    description=MESSAGES.ERROR['NOT_REGISTERED'],
                    color=COLORS.ERROR
                ),
                ephemeral=True
            )
            return
        
        # Langsung tampilkan modal untuk input kode produk dan jumlah
        modal = BuyModal()
        await interaction.response.send_modal(modal)

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
            
            # Extract amount from details or use balance difference
            amount_text = "N/A"
            try:
                if trx.get('details'):
                    # Try to extract amount from details
                    details = trx['details']
                    if 'WL' in details:
                        # Extract number before WL
                        match = re.search(r'(\d+(?:,\d+)*)\s*WL', details)
                        if match:
                            amount_text = f"{match.group(1)} WL"
                        else:
                            amount_text = details
                    else:
                        amount_text = details
                elif trx.get('old_balance') and trx.get('new_balance'):
                    # Calculate difference from balance change
                    old_bal = trx['old_balance']
                    new_bal = trx['new_balance']
                    amount_text = f"Balance: {old_bal} → {new_bal}"
            except Exception as e:
                amount_text = "N/A"
            
            embed.add_field(
                name=f"{i}. {trx_type}",
                value=f"**Detail:** {amount_text}\n**Waktu:** {trx['created_at']}",
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
            
            # Status tracking untuk sinkronisasi dengan livestock
            self.button_status = {
                'is_healthy': True,
                'last_error': None,
                'error_count': 0,
                'last_update': None
            }
            
            self.initialized = True
            self.logger.info(f"LiveButtonManager initialized (refactored) - Channel ID: {self.stock_channel_id}")
            
            # Validasi channel ID
            if self.stock_channel_id == 0:
                self.logger.error("❌ Stock channel ID tidak dikonfigurasi dengan benar")
            else:
                self.logger.info(f"✅ Stock channel ID dikonfigurasi: {self.stock_channel_id}")

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

    def get_status(self) -> Dict:
        """Get current button status"""
        return self.button_status.copy()

    def is_healthy(self) -> bool:
        """Check if button manager is healthy"""
        return self.button_status['is_healthy']

    async def _update_status(self, is_healthy: bool, error: str = None):
        """Update button status"""
        self.button_status['is_healthy'] = is_healthy
        self.button_status['last_update'] = datetime.utcnow()
        
        if error:
            self.button_status['last_error'] = error
            self.button_status['error_count'] += 1
            self.logger.error(f"❌ Button error: {error}")
        else:
            self.button_status['error_count'] = 0
            self.button_status['last_error'] = None
            
        # Notify livestock manager if available (tanpa circular call)
        if self.stock_manager and hasattr(self.stock_manager, 'livestock_status'):
            try:
                # Update status langsung tanpa memanggil function yang bisa circular
                self.stock_manager.livestock_status['button_error'] = error
                self.stock_manager.livestock_status['button_healthy'] = is_healthy
                self.logger.debug(f"✅ Status synced to livestock manager")
            except Exception as e:
                self.logger.error(f"Error syncing to livestock manager: {e}")

    # Removed on_livestock_status_change to prevent circular calls
    # Status sync now handled directly in _update_status

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
            # Check if livestock is healthy before proceeding
            if self.stock_manager and hasattr(self.stock_manager, 'is_healthy'):
                if not self.stock_manager.is_healthy():
                    self.logger.warning("⚠️ Livestock tidak sehat, button tidak akan ditampilkan")
                    await self._update_status(False, "Livestock tidak sehat")
                    return None

            # Pastikan bot sudah ready sebelum mengakses channel
            if not self.bot.is_ready():
                self.logger.warning("[MESSAGE_MANAGEMENT] Bot belum ready, menunggu...")
                try:
                    await asyncio.wait_for(self.bot.wait_until_ready(), timeout=10.0)
                    self.logger.info("[MESSAGE_MANAGEMENT] ✅ Bot sudah ready")
                except asyncio.TimeoutError:
                    error_msg = "Timeout menunggu bot ready"
                    self.logger.error(f"[MESSAGE_MANAGEMENT] {error_msg}")
                    await self._update_status(False, error_msg)
                    return None

            # Retry mechanism untuk mendapatkan channel
            channel = None
            max_retries = 3
            for attempt in range(max_retries):
                channel = self.bot.get_channel(self.stock_channel_id)
                if channel:
                    self.logger.info(f"[MESSAGE_MANAGEMENT] ✅ Channel stock ditemukan: {channel.name} (ID: {channel.id})")
                    break
                
                if attempt < max_retries - 1:
                    self.logger.warning(f"[MESSAGE_MANAGEMENT] Channel tidak ditemukan, retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(1)
                else:
                    error_msg = f"Channel stock dengan ID {self.stock_channel_id} tidak ditemukan setelah {max_retries} percobaan"
                    self.logger.error(f"[MESSAGE_MANAGEMENT] {error_msg}")
                    await self._update_status(False, error_msg)
                    return None

            # First check if stock manager has a valid message
            if self.stock_manager and self.stock_manager.current_stock_message:
                self.current_message = self.stock_manager.current_stock_message
                self.logger.info("[MESSAGE_MANAGEMENT] Menggunakan pesan yang sudah ada dari stock manager")
                
                # Cek apakah pesan masih valid
                try:
                    await self.current_message.fetch()
                    # Update tombol saja, jangan buat embed baru
                    view = self.create_view()
                    await self.current_message.edit(view=view)
                    self.logger.info("✅ Tombol berhasil diupdate pada pesan yang sudah ada")
                    await self._update_status(True)
                    return self.current_message
                except discord.NotFound:
                    self.logger.warning("Pesan yang ada sudah tidak valid, akan mencari yang baru")
                    self.stock_manager.current_stock_message = None
                    self.current_message = None
                except Exception as e:
                    error_msg = f"Error updating existing message: {e}"
                    self.logger.error(error_msg)
                    await self._update_status(False, error_msg)
                    return None

            # Find last message if exists
            if self.stock_manager:
                existing_message = await self.stock_manager.find_last_message()
                if existing_message:
                    self.current_message = existing_message
                    # Update both stock manager and button manager references
                    self.stock_manager.current_stock_message = existing_message
                    self.logger.info("[MESSAGE_MANAGEMENT] Pesan live stock ditemukan, mengupdate tombol")

                    # Cek apakah pesan sudah memiliki tombol
                    has_buttons = len(existing_message.components) > 0
                    if has_buttons:
                        self.logger.info("✅ Pesan sudah memiliki tombol, hanya update view")
                        view = self.create_view()
                        await existing_message.edit(view=view)
                    else:
                        self.logger.info("⚠️ Pesan tidak memiliki tombol, menambahkan embed dan view")
                        # Update embed dan view
                        embed = await self.stock_manager.create_stock_embed()
                        view = self.create_view()
                        await existing_message.edit(embed=embed, view=view)
                    
                    return existing_message

            # Create new message if none found
            self.logger.info("[MESSAGE_MANAGEMENT] Tidak ada pesan yang ditemukan, membuat pesan baru")
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
            self.logger.info("✅ Pesan baru berhasil dibuat dengan embed dan tombol")

            # Update stock manager reference
            if self.stock_manager:
                self.stock_manager.current_stock_message = self.current_message

            return self.current_message

        except Exception as e:
            self.logger.error(f"Error in get_or_create_message: {e}", exc_info=True)
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
        """Initialize dependencies dengan timeout yang lebih pendek"""
        try:
            self.logger.info("Initializing dependencies...")
            
            # Wait for LiveStockCog dengan timeout yang lebih pendek
            max_attempts = 15  # Kurangi timeout menjadi 15 detik
            for attempt in range(max_attempts):
                # Cari LiveStockCog dengan berbagai cara
                self.stock_manager = self.bot.get_cog('LiveStockCog')
                
                # Jika tidak ditemukan, coba cari LiveStockWrapper
                if not self.stock_manager:
                    wrapper = self.bot.get_cog('LiveStockWrapper')
                    if wrapper:
                        # Coba dapatkan LiveStockCog dari wrapper
                        for cog_name, cog in self.bot.cogs.items():
                            if 'LiveStock' in cog_name and hasattr(cog, 'stock_manager'):
                                self.stock_manager = cog
                                break
                
                if self.stock_manager and hasattr(self.stock_manager, 'stock_manager'):
                    await self.button_manager.set_stock_manager(self.stock_manager.stock_manager)
                    self.logger.info(f"✅ LiveStockCog found and connected: {type(self.stock_manager).__name__}")
                    break
                
                if attempt % 5 == 0:  # Log setiap 5 detik
                    self.logger.info(f"Still waiting for LiveStockCog... attempt {attempt + 1}/{max_attempts}")
                await asyncio.sleep(1)
            else:
                # Jika tidak ditemukan, tetap lanjutkan tanpa stock manager
                self.logger.warning("⚠️ LiveStockCog not found after waiting, continuing without stock integration")
                return True  # Return True agar tidak gagal

            self.logger.info("✅ Dependencies initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error initializing dependencies: {e}", exc_info=True)
            return True  # Return True agar tidak gagal, bisa berjalan tanpa stock integration

    async def cog_load(self):
        """Setup when cog is loaded"""
        try:
            self.logger.info("LiveButtonsCog loading...")

            # Jangan tunggu bot ready di sini, karena bot mungkin belum sepenuhnya ready
            # Sebagai gantinya, gunakan asyncio.create_task untuk menjalankan initialization secara asynchronous
            self.logger.info("Memulai initialization secara asynchronous...")
            
            # Buat task untuk initialization yang akan berjalan di background
            asyncio.create_task(self._delayed_initialization())
            
            # Set ready state langsung agar tidak blocking
            self._ready.set()
            self.logger.info("LiveButtonsCog loaded successfully (refactored)")

        except Exception as e:
            self.logger.error(f"Error in cog_load: {e}")
            # Jangan raise error, biarkan cog tetap dimuat
            self.logger.warning("Continuing with partial initialization...")
            self._ready.set()

    async def _delayed_initialization(self):
        """Delayed initialization yang berjalan di background"""
        try:
            self.logger.info("Memulai delayed initialization...")
            
            # Tunggu bot ready dengan timeout yang lebih lama
            self.logger.info("Menunggu bot ready...")
            try:
                await asyncio.wait_for(self.bot.wait_until_ready(), timeout=60.0)
                self.logger.info("✅ Bot sudah ready")
            except asyncio.TimeoutError:
                self.logger.warning("⚠️ Timeout menunggu bot ready, melanjutkan tanpa full integration")
                return

            # Tunggu sebentar untuk memastikan semua cogs lain sudah dimuat
            await asyncio.sleep(5)

            # Initialize dependencies dengan retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"Mencoba initialize dependencies (attempt {attempt + 1}/{max_retries})...")
                    success = await asyncio.wait_for(
                        self.initialize_dependencies(),
                        timeout=30.0
                    )
                    if success:
                        self.logger.info("✅ Dependencies initialization completed")
                        break
                except asyncio.TimeoutError:
                    self.logger.warning(f"⚠️ Initialization attempt {attempt + 1} timed out")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(10)  # Tunggu 10 detik sebelum retry
                    else:
                        self.logger.warning("⚠️ All initialization attempts failed, continuing without full integration")
                except Exception as e:
                    self.logger.error(f"Error in initialization attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(10)
                    else:
                        self.logger.warning("⚠️ All initialization attempts failed, continuing without full integration")

            # Start background task
            if not self.check_display.is_running():
                self.check_display.start()
                self.logger.info("✅ Background task started")

        except Exception as e:
            self.logger.error(f"Error in delayed initialization: {e}")
            self.logger.warning("Continuing without full initialization...")

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
                self.logger.info("[CHECK_DISPLAY] Tidak ada pesan, membuat pesan baru")
                await self.button_manager.get_or_create_message()
            else:
                # Cek apakah pesan masih valid
                try:
                    await message.fetch()
                    # Cek apakah pesan memiliki tombol
                    has_buttons = len(message.components) > 0
                    
                    if self.stock_manager:
                        embed = await self.stock_manager.stock_manager.create_stock_embed()
                        
                        if has_buttons:
                            # Hanya update embed, jangan update view karena tombol sudah ada
                            await message.edit(embed=embed)
                            self.logger.debug("[CHECK_DISPLAY] ✅ Update embed saja (tombol sudah ada)")
                        else:
                            # Update embed dan tambahkan view karena tombol tidak ada
                            view = self.button_manager.create_view()
                            await message.edit(embed=embed, view=view)
                            self.logger.info("[CHECK_DISPLAY] ✅ Update embed dan tambahkan tombol")
                    else:
                        self.logger.warning("[CHECK_DISPLAY] Stock manager tidak tersedia")
                        
                except discord.NotFound:
                    self.logger.warning("[CHECK_DISPLAY] Pesan tidak ditemukan, akan membuat yang baru")
                    self.button_manager.current_message = None
                    if self.stock_manager:
                        self.stock_manager.stock_manager.current_stock_message = None
                    await self.button_manager.get_or_create_message()
                    
        except Exception as e:
            self.logger.error(f"Error in check_display: {e}", exc_info=True)

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
            
            # Validasi konfigurasi channel stock
            stock_channel_id = int(bot.config.get('id_live_stock', 0))
            if stock_channel_id == 0:
                logger.warning("⚠️ Live stock channel ID tidak dikonfigurasi dalam config.json")
                logger.warning("LiveButtonsCog akan dimuat tanpa stock integration")
            else:
                logger.info(f"✅ Live stock channel ID dari config: {stock_channel_id}")
            
            # Tunggu LiveStockCog tersedia (optional)
            stock_cog = bot.get_cog('LiveStockCog')
            if not stock_cog:
                logger.warning("LiveStockCog not found, will wait for it during initialization")

            cog = LiveButtonsCog(bot)
            await bot.add_cog(cog)
            logger.info("LiveButtonsCog added to bot (refactored)")

            # Jangan tunggu initialization selesai, biarkan berjalan di background
            # Karena initialization sekarang menggunakan delayed mechanism
            logger.info("✅ LiveButtonsCog setup completed (initialization running in background)")

            setattr(bot, COG_LOADED['LIVE_BUTTONS'], True)
            logger.info("LiveButtons cog loaded successfully (refactored)")

    except Exception as e:
        logger.error(f"Failed to load LiveButtonsCog: {e}", exc_info=True)
        if hasattr(bot, COG_LOADED['LIVE_BUTTONS']):
            delattr(bot, COG_LOADED['LIVE_BUTTONS'])
        # Jangan raise error, biarkan bot tetap berjalan
        logger.warning("Continuing without LiveButtonsCog...")

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
