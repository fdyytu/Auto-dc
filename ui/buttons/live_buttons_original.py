"""
Live Buttons Manager with Shop Integration
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC

Dependencies:
- ext.product_manager: For product operations
- ext.balance_manager: For balance operations
- ext.trx: For transaction operations
- ext.admin_service: For maintenance mode
- ext.constants: For configuration and responses
"""

import discord
from discord.ext import commands, tasks
from discord import ui
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Union
from discord.ui import Select, Button, View, Modal, TextInput

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

from utils.base_handler import BaseLockHandler
from services.cache_service import CacheManager
from services.product_service import ProductService
from services.balance_service import BalanceManagerService as BalanceService
from services.transaction_service import TransactionManager as TransactionService
from services.admin_service import AdminService

class QuantityModal(Modal):
    def __init__(self, product_code: str, max_quantity: int):
        super().__init__(title="🛍️ Jumlah Pembelian")
        self.product_code = product_code

        self.quantity = TextInput(
            label="Masukkan jumlah yang ingin dibeli",
            placeholder=f"Maksimal {max_quantity}",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.quantity)

    async def on_submit(self, interaction: discord.Interaction):
        # Log detail interaksi quantity modal
        logger = logging.getLogger("QuantityModal")
        logger.info(f"[QUANTITY_MODAL] User {interaction.user.id} ({interaction.user.name}) submitted quantity: {self.quantity.value} for product: {self.product_code}")
        logger.debug(f"[QUANTITY_MODAL] Interaction ID: {interaction.id}, Guild: {interaction.guild_id}, Channel: {interaction.channel_id}")
        
        await interaction.response.defer(ephemeral=True)
        try:
            quantity = int(self.quantity.value)
            logger.info(f"[QUANTITY_MODAL] Processing purchase: {quantity}x {self.product_code} for user {interaction.user.id}")
            if quantity <= 0:
                logger.warning(f"[QUANTITY_MODAL] Invalid quantity {quantity} from user {interaction.user.id}")
                raise ValueError(MESSAGES.ERROR['INVALID_AMOUNT'])

            product_service = ProductService(interaction.client.db_manager)
            balance_service = BalanceService(interaction.client.db_manager)
            trx_manager = TransactionService(interaction.client.db_manager)

            # Get product details
            product_response = await product_service.get_product(self.product_code)
            if not product_response.success:
                raise ValueError(product_response.error)

            product = product_response.data

            # Verify stock
            stock_response = await product_service.get_stock_count(self.product_code)
            if not stock_response.success:
                raise ValueError(stock_response.error)

            if stock_response.data < quantity:
                raise ValueError(MESSAGES.ERROR['INSUFFICIENT_STOCK'])

            # Calculate total price
            total_price = float(product['price']) * quantity

            # Get user's GrowID
            growid_response = await balance_service.get_growid(str(interaction.user.id))
            if not growid_response.success:
                raise ValueError(growid_response.error)

            growid = growid_response.data

            # Verify balance
            balance_response = await balance_service.get_balance(growid)
            if not balance_response.success:
                raise ValueError(balance_response.error)

            balance = balance_response.data
            if balance.total_wl() < total_price:
                raise ValueError(MESSAGES.ERROR['INSUFFICIENT_BALANCE'])

            # Process purchase
            purchase_response = await trx_manager.process_purchase(
                growid=growid,
                product_code=self.product_code,
                quantity=quantity,
                price=total_price
            )

            if not purchase_response.success:
                raise ValueError(purchase_response.error)

            # Create success message
            embed = discord.Embed(
                title="✅ Pembelian Berhasil",
                color=COLORS.SUCCESS
            )

            embed.add_field(
                name="Detail Pembelian",
                value=(
                    f"```yml\n"
                    f"Produk   : {product['name']}\n"
                    f"Jumlah   : {quantity}x\n"
                    f"Harga    : {total_price} WL\n"
                    f"GrowID   : {growid}\n"
                    "```"
                ),
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=MESSAGES.ERROR['TRANSACTION_FAILED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

class ProductSelect(Select):
    def __init__(self, products: List[Dict], balance_service, product_service, trx_manager):
        self.products_cache = {p['code']: p for p in products}
        self.balance_service = balance_service
        self.product_service = product_service
        self.trx_manager = trx_manager

        options = [
            discord.SelectOption(
                label=f"{product['name']}",
                description=f"Stok: {product['stock']} | Harga: {product['price']} WL",
                value=product['code'],
                emoji="🛍️"
            ) for product in products[:25]  # Discord limit 25 options
        ]
        super().__init__(
            placeholder="Pilih produk yang ingin dibeli...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # Log detail interaksi product select
        logger = logging.getLogger("ProductSelect")
        logger.info(f"[PRODUCT_SELECT] User {interaction.user.id} ({interaction.user.name}) selected product: {self.values[0] if self.values else 'None'}")
        logger.debug(f"[PRODUCT_SELECT] Interaction ID: {interaction.id}, Guild: {interaction.guild_id}, Channel: {interaction.channel_id}")
        
        await interaction.response.defer(ephemeral=True)
        try:
            selected_code = self.values[0]
            logger.info(f"[PRODUCT_SELECT] Processing product selection: {selected_code} for user {interaction.user.id}")
            product_response = await self.product_service.get_product(selected_code)
            if not product_response.success:
                logger.error(f"[PRODUCT_SELECT] Failed to get product {selected_code}: {product_response.error}")
                raise ValueError(product_response.error)

            selected_product = product_response.data

            # Verifikasi stock realtime
            stock_response = await self.product_service.get_stock_count(selected_code)
            if not stock_response.success:
                raise ValueError(stock_response.error)

            current_stock = stock_response.data
            if current_stock <= 0:
                raise ValueError(MESSAGES.ERROR['OUT_OF_STOCK'])

            # Verifikasi user balance
            growid_response = await self.balance_service.get_growid(str(interaction.user.id))
            if not growid_response.success:
                raise ValueError(growid_response.error)

            growid = growid_response.data
            if not growid:
                raise ValueError(MESSAGES.ERROR['NOT_REGISTERED'])

            await interaction.followup.send_modal(
                QuantityModal(selected_code, min(current_stock, 999))
            )

        except Exception as e:
            error_msg = str(e) if isinstance(e, ValueError) else MESSAGES.ERROR['TRANSACTION_FAILED']
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=error_msg,
                    color=COLORS.ERROR
                ),
                ephemeral=True
            )

class RegisterModal(Modal):
    def __init__(self):
        super().__init__(title="📝 Pendaftaran GrowID")

        self.growid = TextInput(
            label="Masukkan GrowID Anda",
            placeholder="Contoh: GROW_ID",
            min_length=3,
            max_length=30,
            required=True
        )
        self.add_item(self.growid)

    async def on_submit(self, interaction: discord.Interaction):
        # Log detail interaksi register modal
        logger = logging.getLogger("RegisterModal")
        logger.info(f"[REGISTER_MODAL] User {interaction.user.id} ({interaction.user.name}) submitted registration with GrowID: {self.growid.value}")
        logger.debug(f"[REGISTER_MODAL] Interaction ID: {interaction.id}, Guild: {interaction.guild_id}, Channel: {interaction.channel_id}")
        
        await interaction.response.defer(ephemeral=True)
        try:
            balance_service = BalanceService(interaction.client.db_manager)

            growid = str(self.growid.value).strip().upper()
            logger.info(f"[REGISTER_MODAL] Processing registration for user {interaction.user.id} with GrowID: {growid}")
            if not growid or len(growid) < 3:
                logger.warning(f"[REGISTER_MODAL] Invalid GrowID format from user {interaction.user.id}: {growid}")
                raise ValueError(MESSAGES.ERROR['INVALID_GROWID'])

            register_response = await balance_service.register_user(
                str(interaction.user.id),
                growid
            )

            if not register_response.success:
                raise ValueError(register_response.error)

            success_embed = discord.Embed(
                title="✅ Berhasil",
                description=MESSAGES.SUCCESS['REGISTRATION'].format(growid=growid),
                color=COLORS.SUCCESS
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)

        except ValueError as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=MESSAGES.ERROR['REGISTRATION_FAILED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

class ShopView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.balance_service = BalanceService(bot.db_manager)
        self.product_service = ProductService(bot.db_manager)
        self.trx_manager = TransactionService(bot.db_manager)
        self.admin_service = AdminService(bot.db_manager)
        self.cache_manager = CacheManager()
        self.logger = logging.getLogger("ShopView")
        self._interaction_locks = {}
        self._last_cleanup = datetime.utcnow()
        self._button_stats = {
            'register': {'clicks': 0, 'errors': 0, 'last_used': None},
            'balance': {'clicks': 0, 'errors': 0, 'last_used': None},
            'world_info': {'clicks': 0, 'errors': 0, 'last_used': None},
            'buy': {'clicks': 0, 'errors': 0, 'last_used': None},
            'history': {'clicks': 0, 'errors': 0, 'last_used': None}
        }
        self.logger.info("[SHOP_VIEW] ShopView initialized with button statistics tracking")

    async def _cleanup_locks(self):
        """Cleanup old locks periodically"""
        now = datetime.utcnow()
        if (now - self._last_cleanup).total_seconds() > 300:  # Every 5 minutes
            self._interaction_locks.clear()
            self._last_cleanup = now

    async def _acquire_interaction_lock(self, interaction_id: str) -> bool:
        await self._cleanup_locks()

        if interaction_id not in self._interaction_locks:
            self._interaction_locks[interaction_id] = asyncio.Lock()

        try:
            await asyncio.wait_for(
                self._interaction_locks[interaction_id].acquire(),
                timeout=3.0
            )
            return True
        except:
            return False

    def _release_interaction_lock(self, interaction_id: str):
        if interaction_id in self._interaction_locks:
            try:
                if self._interaction_locks[interaction_id].locked():
                    self._interaction_locks[interaction_id].release()
            except:
                pass

    def _update_button_stats(self, button_name: str, success: bool = True):
        """Update button statistics"""
        if button_name in self._button_stats:
            self._button_stats[button_name]['clicks'] += 1
            self._button_stats[button_name]['last_used'] = datetime.utcnow()
            if not success:
                self._button_stats[button_name]['errors'] += 1
            
            # Log statistics every 10 clicks
            stats = self._button_stats[button_name]
            if stats['clicks'] % 10 == 0:
                error_rate = (stats['errors'] / stats['clicks']) * 100 if stats['clicks'] > 0 else 0
                self.logger.info(f"[BUTTON_STATS] {button_name.upper()}: {stats['clicks']} clicks, {stats['errors']} errors ({error_rate:.1f}% error rate)")

    def get_button_health_report(self) -> str:
        """Generate button health report"""
        report = []
        for button_name, stats in self._button_stats.items():
            if stats['clicks'] > 0:
                error_rate = (stats['errors'] / stats['clicks']) * 100
                last_used = stats['last_used'].strftime('%H:%M:%S') if stats['last_used'] else 'Never'
                status = "🔴 CRITICAL" if error_rate > 50 else "🟡 WARNING" if error_rate > 20 else "🟢 HEALTHY"
                report.append(f"{button_name}: {status} ({stats['clicks']} clicks, {error_rate:.1f}% errors, last: {last_used})")
        return "\n".join(report) if report else "No button activity recorded"

    @discord.ui.button(
        style=discord.ButtonStyle.primary,
        label="📝 Daftar",
        custom_id=BUTTON_IDS.REGISTER
    )
    async def register_callback(self, interaction: discord.Interaction, button: Button):
        # Log detail interaksi tombol
        self.logger.info(f"[BUTTON_REGISTER] User {interaction.user.id} ({interaction.user.name}) clicked register button")
        self.logger.debug(f"[BUTTON_REGISTER] Interaction ID: {interaction.id}, Guild: {interaction.guild_id}, Channel: {interaction.channel_id}")
        
        # Update button statistics
        self._update_button_stats('register')
        
        if not await self._acquire_interaction_lock(str(interaction.id)):
            self.logger.warning(f"[BUTTON_REGISTER] Failed to acquire lock for user {interaction.user.id}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Mohon Tunggu",
                    description=MESSAGES.INFO['COOLDOWN'],
                    color=COLORS.WARNING
                ),
                ephemeral=True
            )
            return

        try:
            self.logger.info(f"[BUTTON_REGISTER] Processing registration for user {interaction.user.id}")
            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                self.logger.warning(f"[BUTTON_REGISTER] Maintenance mode active, blocking user {interaction.user.id}")
                raise ValueError(MESSAGES.INFO['MAINTENANCE'])

            growid_response = await self.balance_service.get_growid(str(interaction.user.id))
            if growid_response.success and growid_response.data:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Sudah Terdaftar",
                        description=f"Anda sudah terdaftar dengan GrowID: `{growid_response.data}`",
                        color=COLORS.ERROR
                    ),
                    ephemeral=True
                )
                return

            modal = RegisterModal()
            await interaction.response.send_modal(modal)

        except ValueError as e:
            self._update_button_stats('register', success=False)
            self.logger.warning(f"[BUTTON_REGISTER] ValueError for user {interaction.user.id}: {str(e)}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Error",
                        description=str(e),
                        color=COLORS.ERROR
                    ),
                    ephemeral=True
                )
        except Exception as e:
            self._update_button_stats('register', success=False)
            self.logger.error(f"[BUTTON_REGISTER] Unexpected error for user {interaction.user.id}: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Error",
                        description=MESSAGES.ERROR['REGISTRATION_FAILED'],
                        color=COLORS.ERROR
                    ),
                    ephemeral=True
                )
        finally:
            self.logger.debug(f"[BUTTON_REGISTER] Releasing interaction lock for user {interaction.user.id}")
            self._release_interaction_lock(str(interaction.id))

    @discord.ui.button(
        style=discord.ButtonStyle.success,
        label="💰 Saldo",
        custom_id=BUTTON_IDS.BALANCE
    )
    async def balance_callback(self, interaction: discord.Interaction, button: Button):
        # Log detail interaksi tombol
        self.logger.info(f"[BUTTON_BALANCE] User {interaction.user.id} ({interaction.user.name}) clicked balance button")
        self.logger.debug(f"[BUTTON_BALANCE] Interaction ID: {interaction.id}, Guild: {interaction.guild_id}, Channel: {interaction.channel_id}")
        
        # Update button statistics
        self._update_button_stats('balance')
        
        if not await self._acquire_interaction_lock(str(interaction.id)):
            self.logger.warning(f"[BUTTON_BALANCE] Failed to acquire lock for user {interaction.user.id}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Mohon Tunggu",
                    description=MESSAGES.INFO['COOLDOWN'],
                    color=COLORS.WARNING
                ),
                ephemeral=True
            )
            return

        try:
            self.logger.info(f"[BUTTON_BALANCE] Processing balance request for user {interaction.user.id}")
            await interaction.response.defer(ephemeral=True)

            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                self.logger.warning(f"[BUTTON_BALANCE] Maintenance mode active, blocking user {interaction.user.id}")
                raise ValueError(MESSAGES.INFO['MAINTENANCE'])

            growid_response = await self.balance_service.get_growid(str(interaction.user.id))
            if not growid_response.success:
                raise ValueError(growid_response.error)

            growid = growid_response.data
            if not growid:
                raise ValueError(MESSAGES.ERROR['NOT_REGISTERED'])

            balance_response = await self.balance_service.get_balance(growid)
            if not balance_response.success:
                raise ValueError(balance_response.error)

            balance = balance_response.data

            # Format balance untuk display
            balance_wls = balance.total_wl()
            display_balance = self._format_currency(balance_wls)

            embed = discord.Embed(
                title="💰 Informasi Saldo",
                description=f"Saldo untuk `{growid}`",
                color=COLORS.INFO
            )

            embed.add_field(
                name="Saldo Saat Ini",
                value=f"```yml\n{display_balance}```",
                inline=False
            )

            # Get transaction history
            trx_response = await self.trx_manager.get_transaction_history(growid, limit=3)
            if trx_response.success and trx_response.data:
                transactions = trx_response.data
                trx_details = []
                for trx in transactions:
                    old_balance = Balance.from_string(trx['old_balance'])
                    new_balance = Balance.from_string(trx['new_balance'])
                    change = new_balance.total_wl() - old_balance.total_wl()
                    sign = "+" if change >= 0 else ""

                    trx_details.append(
                        f"• {trx['type']}: {sign}{change} WL - {trx['details']}"
                    )

                embed.add_field(
                    name="Transaksi Terakhir",
                    value=f"```yml\n{chr(10).join(trx_details)}```",
                    inline=False
                )

            embed.set_footer(text="Diperbarui")
            embed.timestamp = datetime.utcnow()

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e:
            self._update_button_stats('balance', success=False)
            self.logger.warning(f"[BUTTON_BALANCE] ValueError for user {interaction.user.id}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            self._update_button_stats('balance', success=False)
            self.logger.error(f"[BUTTON_BALANCE] Unexpected error for user {interaction.user.id}: {e}", exc_info=True)
            error_embed = discord.Embed(
                title="❌ Error",
                description=MESSAGES.ERROR['BALANCE_FAILED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        finally:
            self.logger.debug(f"[BUTTON_BALANCE] Releasing interaction lock for user {interaction.user.id}")
            self._release_interaction_lock(str(interaction.id))

    def _format_currency(self, amount: int) -> str:
        """Format currency amount with proper denominations"""
        try:
            if amount >= CURRENCY_RATES['BGL']:
                return f"{amount/CURRENCY_RATES['BGL']:.1f} BGL"
            elif amount >= CURRENCY_RATES['DL']:
                return f"{amount/CURRENCY_RATES['DL']:.0f} DL"
            return f"{int(amount)} WL"
        except Exception:
            return "Invalid Amount"

    @discord.ui.button(
        style=discord.ButtonStyle.secondary,
        label="🌎 World Info",
        custom_id=BUTTON_IDS.WORLD_INFO
    )
    async def world_info_callback(self, interaction: discord.Interaction, button: Button):
        # Log detail interaksi tombol
        self.logger.info(f"[BUTTON_WORLD_INFO] User {interaction.user.id} ({interaction.user.name}) clicked world info button")
        self.logger.debug(f"[BUTTON_WORLD_INFO] Interaction ID: {interaction.id}, Guild: {interaction.guild_id}, Channel: {interaction.channel_id}")
        
        # Update button statistics
        self._update_button_stats('world_info')
        
        if not await self._acquire_interaction_lock(str(interaction.id)):
            self.logger.warning(f"[BUTTON_WORLD_INFO] Failed to acquire lock for user {interaction.user.id}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Mohon Tunggu",
                    description=MESSAGES.INFO['COOLDOWN'],
                    color=COLORS.WARNING
                ),
                ephemeral=True
            )
            return
    
        try:
            self.logger.info(f"[BUTTON_WORLD_INFO] Processing world info request for user {interaction.user.id}")
            await interaction.response.defer(ephemeral=True)
            
            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                self.logger.warning(f"[BUTTON_WORLD_INFO] Maintenance mode active, blocking user {interaction.user.id}")
                raise ValueError(MESSAGES.INFO['MAINTENANCE'])
                
            # Gunakan ProductService untuk get world info (FIXED BUG)
            world_response = await self.product_service.get_world_info()
            if not world_response.success:
                raise ValueError(world_response.error or MESSAGES.ERROR['WORLD_INFO_FAILED'])
                
            world_info = world_response.data
            
            # Format status dengan proper emoji
            status_emoji = {
                'online': '🟢',
                'offline': '🔴',
                'maintenance': '🔧',
                'busy': '🟡',
                'full': '🔵'
            }
            
            status = world_info.get('status', '').lower()
            status_display = f"{status_emoji.get(status, '❓')} {status.upper()}"
    
            embed = discord.Embed(
                title="🌎 World Information",
                color=COLORS.INFO
            )
    
            # Basic info dalam format yang rapi
            basic_info = [
                f"{'World':<12}: {world_info.get('world', 'N/A')}",
                f"{'Owner':<12}: {world_info.get('owner', 'N/A')}",
                f"{'Bot':<12}: {world_info.get('bot', 'N/A')}",
                f"{'Status':<12}: {status_display}"
            ]
            
            embed.add_field(
                name="Basic Info",
                value="```" + "\n".join(basic_info) + "```",
                inline=False
            )
    
            # Last updated dengan format yang benar
            updated_at = world_info.get('updated_at')
            if updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    last_update = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except:
                    last_update = "Unknown"
                embed.set_footer(text=f"Last Updated: {last_update}")
    
            await interaction.followup.send(embed=embed, ephemeral=True)
    
        except ValueError as e:
            self._update_button_stats('world_info', success=False)
            self.logger.warning(f"[BUTTON_WORLD_INFO] ValueError for user {interaction.user.id}: {str(e)}")
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=str(e),
                    color=COLORS.ERROR
                ),
                ephemeral=True
            )
        except Exception as e:
            self._update_button_stats('world_info', success=False)
            self.logger.error(f"[BUTTON_WORLD_INFO] Unexpected error for user {interaction.user.id}: {e}", exc_info=True)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=MESSAGES.ERROR['WORLD_INFO_FAILED'],
                    color=COLORS.ERROR
                ),
                ephemeral=True
            )
        finally:
            self.logger.debug(f"[BUTTON_WORLD_INFO] Releasing interaction lock for user {interaction.user.id}")
            self._release_interaction_lock(str(interaction.id))

    @discord.ui.button(
        style=discord.ButtonStyle.success,
        label="🛒 Beli",
        custom_id=BUTTON_IDS.BUY
    )
    async def buy_callback(self, interaction: discord.Interaction, button: Button):
        # Log detail interaksi tombol
        self.logger.info(f"[BUTTON_BUY] User {interaction.user.id} ({interaction.user.name}) clicked buy button")
        self.logger.debug(f"[BUTTON_BUY] Interaction ID: {interaction.id}, Guild: {interaction.guild_id}, Channel: {interaction.channel_id}")
        
        # Update button statistics
        self._update_button_stats('buy')
        
        if not await self._acquire_interaction_lock(str(interaction.id)):
            self.logger.warning(f"[BUTTON_BUY] Failed to acquire lock for user {interaction.user.id}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Mohon Tunggu",
                    description=MESSAGES.INFO['COOLDOWN'],
                    color=COLORS.WARNING
                ),
                ephemeral=True
            )
            return

        try:
            self.logger.info(f"[BUTTON_BUY] Processing buy request for user {interaction.user.id}")
            await interaction.response.defer(ephemeral=True)

            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                self.logger.warning(f"[BUTTON_BUY] Maintenance mode active, blocking user {interaction.user.id}")
                raise ValueError(MESSAGES.INFO['MAINTENANCE'])

            growid_response = await self.balance_service.get_growid(str(interaction.user.id))
            if not growid_response.success:
                raise ValueError(growid_response.error)

            growid = growid_response.data
            if not growid:
                raise ValueError(MESSAGES.ERROR['NOT_REGISTERED'])

            # Get products with proper response handling
            product_response = await self.product_service.get_all_products()
            if not product_response.success:
                raise ValueError(product_response.error)

            products = product_response.data
            available_products = []

            for product in products:
                stock_response = await self.product_service.get_stock_count(product['code'])
                if stock_response.success and stock_response.data > 0:
                    product['stock'] = stock_response.data
                    available_products.append(product)

            if not available_products:
                raise ValueError(MESSAGES.ERROR['OUT_OF_STOCK'])

            embed = discord.Embed(
                title="🏪 Daftar Produk",
                description=(
                    "```yml\n"
                    "Pilih produk dari menu di bawah untuk membeli\n"
                    "```"
                ),
                color=COLORS.INFO
            )

            for product in available_products:
                price = float(product['price'])
                price_display = self._format_currency(price)

                embed.add_field(
                    name=f"{product['name']} [{product['code']}]",
                    value=(
                        f"```yml\n"
                        f"Harga: {price_display}\n"
                        f"Stok: {product['stock']} unit\n"
                        f"```"
                        f"{product.get('description', '')}"
                    ),
                    inline=True
                )

            view = View(timeout=300)
            view.add_item(ProductSelect(
                available_products,
                self.balance_service,
                self.product_service,
                self.trx_manager
            ))

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except ValueError as e:
            self._update_button_stats('buy', success=False)
            self.logger.warning(f"[BUTTON_BUY] ValueError for user {interaction.user.id}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            self._update_button_stats('buy', success=False)
            self.logger.error(f"[BUTTON_BUY] Unexpected error for user {interaction.user.id}: {e}", exc_info=True)
            error_embed = discord.Embed(
                title="❌ Error",
                description=MESSAGES.ERROR['TRANSACTION_FAILED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        finally:
            self.logger.debug(f"[BUTTON_BUY] Releasing interaction lock for user {interaction.user.id}")
            self._release_interaction_lock(str(interaction.id))

    @discord.ui.button(
        style=discord.ButtonStyle.secondary,
        label="📜 Riwayat",
        custom_id=BUTTON_IDS.HISTORY
    )
    async def history_callback(self, interaction: discord.Interaction, button: Button):
        # Log detail interaksi tombol
        self.logger.info(f"[BUTTON_HISTORY] User {interaction.user.id} ({interaction.user.name}) clicked history button")
        self.logger.debug(f"[BUTTON_HISTORY] Interaction ID: {interaction.id}, Guild: {interaction.guild_id}, Channel: {interaction.channel_id}")
        
        # Update button statistics
        self._update_button_stats('history')
        
        if not await self._acquire_interaction_lock(str(interaction.id)):
            self.logger.warning(f"[BUTTON_HISTORY] Failed to acquire lock for user {interaction.user.id}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Mohon Tunggu",
                    description=MESSAGES.INFO['COOLDOWN'],
                    color=COLORS.WARNING
                ),
                ephemeral=True
            )
            return

        try:
            self.logger.info(f"[BUTTON_HISTORY] Processing history request for user {interaction.user.id}")
            await interaction.response.defer(ephemeral=True)

            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                self.logger.warning(f"[BUTTON_HISTORY] Maintenance mode active, blocking user {interaction.user.id}")
                raise ValueError(MESSAGES.INFO['MAINTENANCE'])

            growid_response = await self.balance_service.get_growid(str(interaction.user.id))
            if not growid_response.success:
                raise ValueError(growid_response.error)

            growid = growid_response.data
            if not growid:
                raise ValueError(MESSAGES.ERROR['NOT_REGISTERED'])

            trx_response = await self.trx_manager.get_transaction_history(growid, limit=5)
            if not trx_response.success:
                raise ValueError(trx_response.error)

            transactions = trx_response.data
            if not transactions:
                raise ValueError(MESSAGES.ERROR['NO_HISTORY'])

            embed = discord.Embed(
                title="📊 Riwayat Transaksi",
                description=f"Transaksi terakhir untuk `{growid}`",
                color=COLORS.INFO
            )

            for i, trx in enumerate(transactions, 1):
                # Set emoji berdasarkan tipe transaksi
                emoji_map = {
                    TransactionType.DEPOSIT.value: "💰",
                    TransactionType.PURCHASE.value: "🛒",
                    TransactionType.WITHDRAWAL.value: "💸",
                    TransactionType.ADMIN_ADD.value: "⚡",
                    TransactionType.ADMIN_REMOVE.value: "🔸"
                }
                emoji = emoji_map.get(trx['type'], "❓")

                # Format timestamp
                timestamp = datetime.fromisoformat(trx['created_at'].replace('Z', '+00:00'))

                # Calculate balance change
                old_balance = Balance.from_string(trx['old_balance'])
                new_balance = Balance.from_string(trx['new_balance'])
                balance_change = new_balance.total_wl() - old_balance.total_wl()

                # Format balance change
                change_display = self._format_currency(abs(balance_change))
                change_prefix = "+" if balance_change >= 0 else "-"

                embed.add_field(
                    name=f"{emoji} Transaksi #{i}",
                    value=(
                        f"```yml\n"
                        f"Tipe: {trx['type']}\n"
                        f"Tanggal: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                        f"Perubahan: {change_prefix}{change_display}\n"
                        f"Status: {trx['status']}\n"
                        f"Detail: {trx['details']}\n"
                        "```"
                    ),
                    inline=False
                )

            embed.set_footer(text="Menampilkan 5 transaksi terakhir")
            embed.timestamp = datetime.utcnow()

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e:
            self._update_button_stats('history', success=False)
            self.logger.warning(f"[BUTTON_HISTORY] ValueError for user {interaction.user.id}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            self._update_button_stats('history', success=False)
            self.logger.error(f"[BUTTON_HISTORY] Unexpected error for user {interaction.user.id}: {e}", exc_info=True)
            error_embed = discord.Embed(
                title="❌ Error",
                description=MESSAGES.ERROR['TRANSACTION_FAILED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        finally:
            self.logger.debug(f"[BUTTON_HISTORY] Releasing interaction lock for user {interaction.user.id}")
            self._release_interaction_lock(str(interaction.id))

class LiveButtonManager(BaseLockHandler):
    def __init__(self, bot):
        if not hasattr(self, 'initialized') or not self.initialized:
            super().__init__()
            self.bot = bot
            self.logger = logging.getLogger("LiveButtonManager")
            self.cache_manager = CacheManager()
            self.admin_service = AdminService(bot.db_manager)
            self.stock_channel_id = int(self.bot.config.get('id_live_stock', 0))
            self.current_message = None
            self.stock_manager = None
            self._ready = asyncio.Event()
            self.initialized = True
            self.logger.info("LiveButtonManager initialized")

    def create_view(self):
        """Create shop view with buttons"""
        self.logger.info("[VIEW_CREATION] Creating new ShopView with buttons")
        view = ShopView(self.bot)
        self.logger.debug(f"[VIEW_CREATION] ShopView created with {len(view.children)} buttons")
        return view

    def get_button_health_report(self):
        """Get button health report from current view"""
        try:
            # Create a temporary view to access button statistics
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

    # Di LiveButtonManager, perbaiki method force_update
    async def force_update(self) -> bool:
        """Force update stock display and buttons"""
        self.logger.info("[FORCE_UPDATE] Starting force update of live stock display")
        try:
            if not self.current_message:
                self.logger.debug("[FORCE_UPDATE] No current message, creating new one")
                self.current_message = await self.get_or_create_message()

            if not self.current_message:
                self.logger.error("[FORCE_UPDATE] Failed to get or create message")
                return False

            # Check maintenance mode 
            try:
                is_maintenance = await self.admin_service.is_maintenance_mode()
                if is_maintenance:
                    self.logger.info("[FORCE_UPDATE] Maintenance mode active, showing maintenance message")
                    embed = discord.Embed(
                        title="🔧 Maintenance Mode",
                        description=MESSAGES.INFO['MAINTENANCE'],
                        color=COLORS.WARNING
                    )
                    await self.current_message.edit(embed=embed, view=None)
                    return True
            except Exception as e:
                self.logger.error(f"[FORCE_UPDATE] Error checking maintenance mode: {e}")
                return False

            if self.stock_manager:
                self.logger.debug("[FORCE_UPDATE] Updating stock display via stock manager")
                await self.stock_manager.update_stock_display()

            self.logger.debug("[FORCE_UPDATE] Creating new view with buttons")
            view = self.create_view()
            
            self.logger.debug("[FORCE_UPDATE] Editing message with new view")
            await self.current_message.edit(view=view)
            self.logger.info("[FORCE_UPDATE] Force update completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"[FORCE_UPDATE] Error in force update: {e}")
            return False

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.current_message:
                embed = discord.Embed(
                    title="🛠️ Maintenance",
                    description=MESSAGES.INFO['MAINTENANCE'],
                    color=COLORS.WARNING
                )
                await self.current_message.edit(embed=embed, view=None)

            # Clear caches
            patterns = [
                'live_stock_message_id',
                'world_info',
                'available_products'
            ]

            for pattern in patterns:
                await self.cache_manager.delete(pattern)

            self.logger.info("LiveButtonManager cleanup completed")

        except Exception as e:
            self.logger.error(f"Error in cleanup: {e}")

class LiveButtonsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.button_manager = LiveButtonManager(bot)
        self.stock_manager = None
        self.logger = logging.getLogger("LiveButtonsCog")
        self._ready = asyncio.Event()
        self._initialization_lock = asyncio.Lock()
        self.logger.info("LiveButtonsCog initialized")

    async def wait_for_stock_manager(self, timeout=30) -> bool:
        """Wait for stock manager to be available"""
        try:
            start_time = datetime.utcnow()
            self.logger.info(f"Waiting for StockManager (timeout: {timeout}s)...")

            while (datetime.utcnow() - start_time).total_seconds() < timeout:
                self.logger.debug("Attempting to get StockManager...")
                stock_cog = self.bot.get_cog('LiveStockCog')

                if stock_cog and hasattr(stock_cog, 'stock_manager'):
                    self.logger.info("Found StockManager")
                    self.stock_manager = stock_cog.stock_manager
                    if self.stock_manager and hasattr(self.stock_manager, '_ready') and self.stock_manager._ready.is_set():
                        self.logger.info("StockManager is ready")
                        return True
                    else:
                        self.logger.debug("StockManager found but not ready yet")
                else:
                    self.logger.debug("LiveStockCog or stock_manager not found")

                await asyncio.sleep(2)

            self.logger.error(f"Timeout waiting for StockManager after {timeout}s")
            return False

        except Exception as e:
            self.logger.error(f"Error waiting for stock manager: {e}", exc_info=True)
            return False

    async def initialize_dependencies(self) -> bool:
        """Initialize all dependencies"""
        try:
            async with self._initialization_lock:
                self.logger.info("Starting dependency initialization...")

                if self._ready.is_set():
                    self.logger.info("Dependencies already initialized")
                    return True

                # Wait for bot to be ready
                if not self.bot.is_ready():
                    self.logger.info("Waiting for bot to be ready...")
                    await self.bot.wait_until_ready()
                    self.logger.info("Bot is ready")

                # Wait for stock manager
                self.logger.info("Waiting for stock manager...")
                if not await self.wait_for_stock_manager():
                    self.logger.error("Failed to get stock manager")
                    return False

                # Set stock manager to button manager
                self.logger.info("Setting stock manager to button manager...")
                await self.button_manager.set_stock_manager(self.stock_manager)

                self._ready.set()
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
            self.logger.info("LiveButtonsCog loaded successfully")

        except Exception as e:
            self.logger.error(f"Error in cog_load: {e}")
            raise

    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        try:
            self.check_display.cancel()
            await self.button_manager.cleanup()
            self.logger.info("LiveButtonsCog unloaded")
        except Exception as e:
            self.logger.error(f"Error in cog_unload: {e}")

    @tasks.loop(minutes=5.0)  # Ubah dari seconds=30 menjadi minutes=5.0
    async def check_display(self):
        """Periodically check and update display"""
        if not self._ready.is_set():
            return

        try:
            message = self.button_manager.current_message
            if not message:
                # Hanya buat pesan baru jika tidak ada
                await self.button_manager.get_or_create_message()
            else:
                # Hanya update embed, TIDAK update view
                if self.stock_manager:
                    embed = await self.stock_manager.create_stock_embed()
                    await message.edit(embed=embed)
        except Exception as e:
            self.logger.error(f"Error in check_display: {e}")

    @check_display.before_loop
    async def before_check_display(self):
        """Wait until ready before starting the loop"""
        await self.bot.wait_until_ready()
        await self._ready.wait()

async def setup(bot):
    """Setup cog with proper error handling"""
    logger = logging.getLogger("LiveButtonsCog.setup")
    try:
        if not hasattr(bot, COG_LOADED['LIVE_BUTTONS']):
            logger.info("Setting up LiveButtonsCog...")
            
            # Tunggu LiveStockCog tersedia (sudah diload oleh sistem)
            # TIDAK load manual untuk menghindari duplikasi
            stock_cog = bot.get_cog('LiveStockCog')
            if not stock_cog:
                logger.warning("LiveStockCog not found, will wait for it during initialization")

            cog = LiveButtonsCog(bot)
            await bot.add_cog(cog)
            logger.info("LiveButtonsCog added to bot")

            # Wait for initialization with timeout
            try:
                async with asyncio.timeout(45):
                    await cog._ready.wait()
                    logger.info("LiveButtonsCog initialization completed")
            except asyncio.TimeoutError:
                logger.error("LiveButtonsCog initialization timed out")
                await bot.remove_cog('LiveButtonsCog')
                raise RuntimeError("Initialization timed out")

            setattr(bot, COG_LOADED['LIVE_BUTTONS'], True)
            logger.info("LiveButtons cog loaded successfully")

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
        logging.info("LiveButtons cog unloaded successfully")
    except Exception as e:
        logging.error(f"Error unloading LiveButtonsCog: {e}")
