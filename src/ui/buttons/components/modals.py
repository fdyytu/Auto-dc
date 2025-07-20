"""
Modal Components for Live Buttons
Author: fdyytu
Created at: 2025-01-XX XX:XX:XX UTC

Komponen modal yang dipisahkan dari live_buttons.py
"""

import discord
from discord.ui import Modal, TextInput
import logging
import io
from datetime import datetime
from typing import Optional

from src.config.constants.bot_constants import MESSAGES, COLORS, NOTIFICATION_CHANNELS
from src.services.product_service import ProductService
from src.services.balance_service import BalanceManagerService as BalanceService
from src.services.transaction_service import TransactionManager as TransactionService, TransactionManager

class QuantityModal(Modal):
    """Modal untuk input jumlah pembelian"""
    
    def __init__(self, product_code: str, max_quantity: int):
        super().__init__(title="🛍️ Jumlah Pembelian")
        self.product_code = product_code
        self.logger = logging.getLogger("QuantityModal")

        self.quantity = TextInput(
            label="Masukkan jumlah yang ingin dibeli",
            placeholder=f"Maksimal {max_quantity}",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.quantity)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle quantity submission"""
        self.logger.info(f"[QUANTITY_MODAL] User {interaction.user.id} ({interaction.user.name}) submitted quantity: {self.quantity.value} for product: {self.product_code}")
        self.logger.debug(f"[QUANTITY_MODAL] Interaction ID: {interaction.id}, Guild: {interaction.guild_id}, Channel: {interaction.channel_id}")
        
        await interaction.response.defer(ephemeral=True)
        try:
            quantity = int(self.quantity.value)
            self.logger.info(f"[QUANTITY_MODAL] Processing purchase: {quantity}x {self.product_code} for user {interaction.user.id}")
            
            if quantity <= 0:
                self.logger.warning(f"[QUANTITY_MODAL] Invalid quantity {quantity} from user {interaction.user.id}")
                raise ValueError(MESSAGES.ERROR['INVALID_AMOUNT'])

            # Initialize services
            product_service = ProductService(interaction.client.db_manager)
            balance_service = BalanceService(interaction.client)
            trx_manager = TransactionManager(interaction.client)

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
            user_balance_wl = balance.total_wl()
            total_price_int = int(total_price)
            
            # Add detailed logging for debugging
            self.logger.info(f"[QUANTITY_MODAL] Balance check for user {interaction.user.id}: Balance={user_balance_wl} WL, Required={total_price_int} WL")
            self.logger.info(f"[QUANTITY_MODAL] Balance details: WL={balance.wl}, DL={balance.dl}, BGL={balance.bgl}")
            self.logger.info(f"[QUANTITY_MODAL] Balance total_wl calculation: {balance.wl} + ({balance.dl} * 100) + ({balance.bgl} * 10000) = {user_balance_wl}")
            
            # Use can_afford method for more reliable balance checking
            if not balance.can_afford(total_price_int):
                self.logger.warning(f"[QUANTITY_MODAL] Purchase failed for user {interaction.user.id}: ❌ Balance tidak cukup!")
                self.logger.warning(f"[QUANTITY_MODAL] Balance verification failed: Available={user_balance_wl} WL, Required={total_price_int} WL")
                raise ValueError(f"❌ Balance tidak cukup! Saldo Anda: {user_balance_wl:,.0f} WL, Dibutuhkan: {total_price_int:,.0f} WL")

            # Process purchase
            purchase_response = await trx_manager.process_purchase(
                buyer_id=str(interaction.user.id),
                product_code=self.product_code,
                quantity=quantity
            )

            if not purchase_response.success:
                raise ValueError(purchase_response.error)

            # Get purchased items content
            purchased_items = purchase_response.data.get('content', [])
            
            # Create and send file via DM
            await self._send_items_via_dm(interaction, purchased_items, product, quantity, total_price)
            
            # Log to channels
            await self._log_purchase_to_channels(interaction, product, quantity, total_price, growid)

            # Create success embed
            success_embed = discord.Embed(
                title="✅ Pembelian Berhasil",
                description=f"Berhasil membeli {quantity}x {product['name']}\nTotal: {total_price:,.0f} WL\n\n📩 **Item telah dikirim via DM!**",
                color=COLORS.SUCCESS
            )
            success_embed.add_field(
                name="📦 Detail Produk",
                value=f"**Kode:** {self.product_code}\n**Nama:** {product['name']}\n**Harga Satuan:** {product['price']:,.0f} WL",
                inline=False
            )
            success_embed.add_field(
                name="💰 Sisa Saldo",
                value=f"{balance.total_wl() - total_price:,.0f} WL",
                inline=True
            )
            
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            self.logger.info(f"[QUANTITY_MODAL] Purchase successful: {quantity}x {self.product_code} for user {interaction.user.id}")

        except ValueError as e:
            self.logger.warning(f"[QUANTITY_MODAL] Purchase failed for user {interaction.user.id}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"[QUANTITY_MODAL] Unexpected error for user {interaction.user.id}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=MESSAGES.ERROR['TRANSACTION_FAILED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    async def _send_items_via_dm(self, interaction: discord.Interaction, items: list, product: dict, quantity: int, total_price: float):
        """Send purchased items via DM as .txt file"""
        try:
            if not items:
                self.logger.warning(f"No items to send for user {interaction.user.id}")
                return

            # Create file content
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file_content = f"=== PEMBELIAN BERHASIL ===\n"
            file_content += f"Tanggal: {timestamp}\n"
            file_content += f"Produk: {product['name']} ({self.product_code})\n"
            file_content += f"Jumlah: {quantity}x\n"
            file_content += f"Total Harga: {total_price:,.0f} WL\n"
            file_content += f"Pembeli: {interaction.user.name} ({interaction.user.id})\n\n"
            file_content += "=== ITEM YANG DIBELI ===\n"
            
            for i, item in enumerate(items, 1):
                file_content += f"{i}. {item}\n"

            # Create file
            file_buffer = io.StringIO(file_content)
            file = discord.File(
                io.BytesIO(file_buffer.getvalue().encode('utf-8')),
                filename=f"{self.product_code}_{quantity}x_{timestamp.replace(':', '-').replace(' ', '_')}.txt"
            )

            # Send DM
            try:
                await interaction.user.send(
                    content=f"🎉 **Pembelian Berhasil!**\n\nHalo {interaction.user.mention}! Berikut adalah item yang telah kamu beli:",
                    file=file
                )
                self.logger.info(f"[QUANTITY_MODAL] Items sent via DM to user {interaction.user.id}")
            except discord.Forbidden:
                self.logger.warning(f"[QUANTITY_MODAL] Cannot send DM to user {interaction.user.id} - DMs disabled")
                # Send notification in channel that DM failed
                await interaction.followup.send(
                    "⚠️ **Tidak dapat mengirim DM!**\nSilakan buka DM Anda untuk menerima item. Item akan dikirim ulang jika DM dibuka.",
                    ephemeral=True
                )

        except Exception as e:
            self.logger.error(f"[QUANTITY_MODAL] Error sending items via DM: {e}")

    async def _log_purchase_to_channels(self, interaction: discord.Interaction, product: dict, quantity: int, total_price: float, growid: str):
        """Log purchase to history and log channels"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create log embed
            log_embed = discord.Embed(
                title="💰 Pembelian Baru",
                color=COLORS.SUCCESS,
                timestamp=datetime.now()
            )
            log_embed.add_field(
                name="👤 Pembeli",
                value=f"{interaction.user.mention}\n`{growid}`",
                inline=True
            )
            log_embed.add_field(
                name="📦 Produk",
                value=f"**{product['name']}**\n`{self.product_code}`",
                inline=True
            )
            log_embed.add_field(
                name="💎 Detail",
                value=f"Jumlah: {quantity}x\nTotal: {total_price:,.0f} WL",
                inline=True
            )
            log_embed.set_footer(text=f"User ID: {interaction.user.id}")

            # Send to history buy channel
            try:
                history_channel = interaction.client.get_channel(NOTIFICATION_CHANNELS.HISTORY_BUY)
                if history_channel:
                    await history_channel.send(embed=log_embed)
                    self.logger.info(f"[QUANTITY_MODAL] Purchase logged to history channel")
            except Exception as e:
                self.logger.error(f"[QUANTITY_MODAL] Error logging to history channel: {e}")

            # Send to buy log channel
            try:
                log_channel = interaction.client.get_channel(NOTIFICATION_CHANNELS.BUY_LOG)
                if log_channel:
                    log_message = f"`[{timestamp}]` **{interaction.user.name}** ({growid}) membeli {quantity}x **{product['name']}** ({self.product_code}) seharga {total_price:,.0f} WL"
                    await log_channel.send(log_message)
                    self.logger.info(f"[QUANTITY_MODAL] Purchase logged to buy log channel")
            except Exception as e:
                self.logger.error(f"[QUANTITY_MODAL] Error logging to buy log channel: {e}")

        except Exception as e:
            self.logger.error(f"[QUANTITY_MODAL] Error logging purchase: {e}")

class BuyModal(Modal):
    """Modal untuk pembelian produk dengan input code dan quantity"""
    
    def __init__(self):
        super().__init__(title="🛍️ Beli Produk")
        self.logger = logging.getLogger("BuyModal")

        self.product_code = TextInput(
            label="Kode Produk",
            placeholder="Contoh: BUAH, SAYUR, dll",
            min_length=1,
            max_length=20,
            required=True
        )
        self.add_item(self.product_code)

        self.quantity = TextInput(
            label="Jumlah Pembelian",
            placeholder="Masukkan jumlah yang ingin dibeli",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.quantity)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle buy submission"""
        self.logger.info(f"[BUY_MODAL] User {interaction.user.id} ({interaction.user.name}) submitted buy request")
        self.logger.debug(f"[BUY_MODAL] Product: {self.product_code.value}, Quantity: {self.quantity.value}")
        
        await interaction.response.defer(ephemeral=True)
        try:
            product_code = str(self.product_code.value).strip().upper()
            quantity = int(self.quantity.value)
            
            self.logger.info(f"[BUY_MODAL] Processing purchase: {quantity}x {product_code} for user {interaction.user.id}")
            
            if quantity <= 0:
                self.logger.warning(f"[BUY_MODAL] Invalid quantity {quantity} from user {interaction.user.id}")
                raise ValueError(MESSAGES.ERROR['INVALID_AMOUNT'])

            # Initialize services
            product_service = ProductService(interaction.client.db_manager)
            balance_service = BalanceService(interaction.client)
            trx_manager = TransactionManager(interaction.client)

            # Get product details
            product_response = await product_service.get_product(product_code)
            if not product_response.success:
                raise ValueError(f"Produk dengan kode '{product_code}' tidak ditemukan")

            product = product_response.data

            # Verify stock
            stock_response = await product_service.get_stock_count(product_code)
            if not stock_response.success:
                raise ValueError(stock_response.error)

            available_stock = stock_response.data['count']
            if available_stock < quantity:
                raise ValueError(f"Stock tidak mencukupi. Tersedia: {available_stock}, Diminta: {quantity}")

            # Calculate total price
            total_price = float(product['price']) * quantity

            # Get user's GrowID
            growid_response = await balance_service.get_growid(str(interaction.user.id))
            if not growid_response.success:
                raise ValueError("Anda belum terdaftar. Silakan daftar terlebih dahulu dengan tombol Register.")

            growid = growid_response.data

            # Verify balance
            balance_response = await balance_service.get_balance(growid)
            if not balance_response.success:
                raise ValueError(balance_response.error)

            balance = balance_response.data
            user_balance_wl = balance.total_wl()
            total_price_int = int(total_price)
            
            # Add detailed logging for debugging
            self.logger.info(f"[BUY_MODAL] Balance check for user {interaction.user.id}: Balance={user_balance_wl} WL, Required={total_price_int} WL")
            self.logger.info(f"[BUY_MODAL] Balance details: WL={balance.wl}, DL={balance.dl}, BGL={balance.bgl}")
            self.logger.info(f"[BUY_MODAL] Balance total_wl calculation: {balance.wl} + ({balance.dl} * 100) + ({balance.bgl} * 10000) = {user_balance_wl}")
            
            # Log balance verification details for debugging
            self.logger.info(f"[BUY_MODAL] Pre-purchase balance verification:")
            self.logger.info(f"[BUY_MODAL] User balance: {user_balance_wl} WL")
            self.logger.info(f"[BUY_MODAL] Required: {total_price_int} WL")
            self.logger.info(f"[BUY_MODAL] Can afford check: {balance.can_afford(total_price_int)}")
            
            # Use can_afford method for more reliable balance checking
            if not balance.can_afford(total_price_int):
                self.logger.warning(f"[BUY_MODAL] Purchase failed for user {interaction.user.id}: ❌ Balance tidak cukup!")
                self.logger.warning(f"[BUY_MODAL] Balance verification failed: Available={user_balance_wl} WL, Required={total_price_int} WL")
                raise ValueError(f"❌ Balance tidak cukup! Saldo Anda: {user_balance_wl:,.0f} WL, Dibutuhkan: {total_price_int:,.0f} WL")

            # Process purchase - let TransactionManager handle the final balance verification
            self.logger.info(f"[BUY_MODAL] Proceeding to TransactionManager.process_purchase")
            purchase_response = await trx_manager.process_purchase(
                buyer_id=str(interaction.user.id),
                product_code=product_code,
                quantity=quantity
            )

            if not purchase_response.success:
                self.logger.error(f"[BUY_MODAL] TransactionManager.process_purchase failed: {purchase_response.error}")
                raise ValueError(purchase_response.error)

            # Get purchased items content
            purchased_items = purchase_response.data.get('content', [])
            
            # Create and send file via DM
            await self._send_items_via_dm(interaction, purchased_items, product, quantity, total_price, product_code)
            
            # Log to channels
            await self._log_purchase_to_channels(interaction, product, quantity, total_price, growid, product_code)

            # Create success embed
            success_embed = discord.Embed(
                title="✅ Pembelian Berhasil",
                description=f"Berhasil membeli {quantity}x {product['name']}\nTotal: {total_price:,.0f} WL\n\n📩 **Item telah dikirim via DM!**",
                color=COLORS.SUCCESS
            )
            success_embed.add_field(
                name="📦 Detail Produk",
                value=f"**Kode:** {product_code}\n**Nama:** {product['name']}\n**Harga Satuan:** {product['price']:,.0f} WL",
                inline=False
            )
            success_embed.add_field(
                name="💰 Sisa Saldo",
                value=f"{balance.total_wl() - total_price:,.0f} WL",
                inline=True
            )
            
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            self.logger.info(f"[BUY_MODAL] Purchase successful: {quantity}x {product_code} for user {interaction.user.id}")
            
            # Clear cache stock untuk produk ini agar live display terupdate
            try:
                live_stock_cog = interaction.client.get_cog('LiveStockCog')
                if live_stock_cog and hasattr(live_stock_cog, 'stock_manager'):
                    await live_stock_cog.stock_manager.clear_stock_cache(product_code)
                    self.logger.info(f"✅ Stock cache cleared for product: {product_code}")
            except Exception as e:
                self.logger.warning(f"Failed to clear stock cache: {e}")

        except ValueError as e:
            self.logger.warning(f"[BUY_MODAL] Purchase failed for user {interaction.user.id}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"[BUY_MODAL] Unexpected error for user {interaction.user.id}: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                description="Terjadi kesalahan saat memproses transaksi. Silakan coba lagi.",
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    async def _send_items_via_dm(self, interaction: discord.Interaction, items: list, product: dict, quantity: int, total_price: float, product_code: str):
        """Send purchased items via DM as .txt file"""
        try:
            if not items:
                self.logger.warning(f"No items to send for user {interaction.user.id}")
                return

            # Create file content
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file_content = f"=== PEMBELIAN BERHASIL ===\n"
            file_content += f"Tanggal: {timestamp}\n"
            file_content += f"Produk: {product['name']} ({product_code})\n"
            file_content += f"Jumlah: {quantity}x\n"
            file_content += f"Total Harga: {total_price:,.0f} WL\n"
            file_content += f"Pembeli: {interaction.user.name} ({interaction.user.id})\n\n"
            file_content += "=== ITEM YANG DIBELI ===\n"
            
            for i, item in enumerate(items, 1):
                file_content += f"{i}. {item}\n"

            # Create file
            file_buffer = io.StringIO(file_content)
            file = discord.File(
                io.BytesIO(file_buffer.getvalue().encode('utf-8')),
                filename=f"{product_code}_{quantity}x_{timestamp.replace(':', '-').replace(' ', '_')}.txt"
            )

            # Send DM
            try:
                await interaction.user.send(
                    content=f"🎉 **Pembelian Berhasil!**\n\nHalo {interaction.user.mention}! Berikut adalah item yang telah kamu beli:",
                    file=file
                )
                self.logger.info(f"[BUY_MODAL] Items sent via DM to user {interaction.user.id}")
            except discord.Forbidden:
                self.logger.warning(f"[BUY_MODAL] Cannot send DM to user {interaction.user.id} - DMs disabled")
                # Send notification in channel that DM failed
                await interaction.followup.send(
                    "⚠️ **Tidak dapat mengirim DM!**\nSilakan buka DM Anda untuk menerima item. Item akan dikirim ulang jika DM dibuka.",
                    ephemeral=True
                )

        except Exception as e:
            self.logger.error(f"[BUY_MODAL] Error sending items via DM: {e}")

    async def _log_purchase_to_channels(self, interaction: discord.Interaction, product: dict, quantity: int, total_price: float, growid: str, product_code: str):
        """Log purchase to history and log channels"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create log embed
            log_embed = discord.Embed(
                title="💰 Pembelian Baru",
                color=COLORS.SUCCESS,
                timestamp=datetime.now()
            )
            log_embed.add_field(
                name="👤 Pembeli",
                value=f"{interaction.user.mention}\n`{growid}`",
                inline=True
            )
            log_embed.add_field(
                name="📦 Produk",
                value=f"**{product['name']}**\n`{product_code}`",
                inline=True
            )
            log_embed.add_field(
                name="💎 Detail",
                value=f"Jumlah: {quantity}x\nTotal: {total_price:,.0f} WL",
                inline=True
            )
            log_embed.set_footer(text=f"User ID: {interaction.user.id}")

            # Send to history buy channel
            try:
                history_channel = interaction.client.get_channel(NOTIFICATION_CHANNELS.HISTORY_BUY)
                if history_channel:
                    await history_channel.send(embed=log_embed)
                    self.logger.info(f"[BUY_MODAL] Purchase logged to history channel")
            except Exception as e:
                self.logger.error(f"[BUY_MODAL] Error logging to history channel: {e}")

            # Send to buy log channel
            try:
                log_channel = interaction.client.get_channel(NOTIFICATION_CHANNELS.BUY_LOG)
                if log_channel:
                    log_message = f"`[{timestamp}]` **{interaction.user.name}** ({growid}) membeli {quantity}x **{product['name']}** ({product_code}) seharga {total_price:,.0f} WL"
                    await log_channel.send(log_message)
                    self.logger.info(f"[BUY_MODAL] Purchase logged to buy log channel")
            except Exception as e:
                self.logger.error(f"[BUY_MODAL] Error logging to buy log channel: {e}")

        except Exception as e:
            self.logger.error(f"[BUY_MODAL] Error logging purchase: {e}")

class RegisterModal(Modal):
    """Modal untuk registrasi GrowID"""
    
    def __init__(self):
        super().__init__(title="📝 Registrasi GrowID")
        self.logger = logging.getLogger("RegisterModal")

        self.growid = TextInput(
            label="Masukkan GrowID Anda",
            placeholder="Contoh: PLAYERNAME",
            min_length=3,
            max_length=20,
            required=True
        )
        self.add_item(self.growid)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle registration submission"""
        self.logger.info(f"[REGISTER_MODAL] User {interaction.user.id} ({interaction.user.name}) attempting registration")
        
        await interaction.response.defer(ephemeral=True)
        try:
            balance_service = BalanceService(interaction.client)
            
            growid = str(self.growid.value).strip()
            self.logger.info(f"[REGISTER_MODAL] Processing registration for user {interaction.user.id} with GrowID: {growid}")
            
            if not growid or len(growid) < 3:
                self.logger.warning(f"[REGISTER_MODAL] Invalid GrowID format from user {interaction.user.id}: {growid}")
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
            self.logger.info(f"[REGISTER_MODAL] Registration successful for user {interaction.user.id} with GrowID: {growid}")

        except ValueError as e:
            self.logger.warning(f"[REGISTER_MODAL] Registration failed for user {interaction.user.id}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"[REGISTER_MODAL] Unexpected error for user {interaction.user.id}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=MESSAGES.ERROR['REGISTRATION_FAILED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
