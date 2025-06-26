"""
Button Handler Components for Live Buttons
Author: fdyytu
Created at: 2025-01-XX XX:XX:XX UTC

Komponen button handlers yang dipisahkan dari live_buttons.py
"""

import discord
from discord.ui import View, Button, Modal, TextInput
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from src.config.constants.bot_constants import COLORS, MESSAGES, BUTTON_IDS
from src.services.balance_service import BalanceManagerService as BalanceService
from src.services.product_service import ProductService
from src.services.transaction_service import TransactionManager as TransactionService
from src.services.admin_service import AdminService
from src.services.cache_service import CacheManager
from .modals import RegisterModal, QuantityModal

class ButtonStatistics:
    """Class untuk mengelola statistik button"""
    
    def __init__(self):
        self.stats = {
            'register': {'clicks': 0, 'errors': 0, 'last_used': None},
            'balance': {'clicks': 0, 'errors': 0, 'last_used': None},
            'world_info': {'clicks': 0, 'errors': 0, 'last_used': None},
            'buy': {'clicks': 0, 'errors': 0, 'last_used': None},
            'history': {'clicks': 0, 'errors': 0, 'last_used': None}
        }
        self.logger = logging.getLogger("ButtonStatistics")
    
    def update_stats(self, button_name: str, success: bool = True):
        """Update button statistics"""
        if button_name in self.stats:
            self.stats[button_name]['clicks'] += 1
            self.stats[button_name]['last_used'] = datetime.utcnow()
            if not success:
                self.stats[button_name]['errors'] += 1
            
            # Log statistics every 10 clicks
            stats = self.stats[button_name]
            if stats['clicks'] % 10 == 0:
                error_rate = (stats['errors'] / stats['clicks']) * 100 if stats['clicks'] > 0 else 0
                self.logger.info(f"[BUTTON_STATS] {button_name.upper()}: {stats['clicks']} clicks, {stats['errors']} errors ({error_rate:.1f}% error rate)")
    
    def get_health_report(self) -> str:
        """Generate button health report"""
        report_lines = ["📊 **Button Health Report**\n"]
        
        for button_name, stats in self.stats.items():
            if stats['clicks'] > 0:
                error_rate = (stats['errors'] / stats['clicks']) * 100
                last_used = stats['last_used'].strftime('%H:%M:%S') if stats['last_used'] else 'Never'
                
                status_emoji = "🟢" if error_rate < 5 else "🟡" if error_rate < 15 else "🔴"
                
                report_lines.append(
                    f"{status_emoji} **{button_name.title()}**: "
                    f"{stats['clicks']} clicks, {error_rate:.1f}% errors, "
                    f"Last: {last_used}"
                )
            else:
                report_lines.append(f"⚪ **{button_name.title()}**: No usage")
        
        return "\n".join(report_lines)

class InteractionLockManager:
    """Class untuk mengelola interaction locks"""
    
    def __init__(self):
        self._interaction_locks = {}
        self._last_cleanup = datetime.utcnow()
        self.logger = logging.getLogger("InteractionLockManager")
    
    async def cleanup_locks(self):
        """Cleanup old locks periodically"""
        now = datetime.utcnow()
        if (now - self._last_cleanup).total_seconds() > 300:  # Every 5 minutes
            self._interaction_locks.clear()
            self._last_cleanup = now
            self.logger.debug("Cleaned up interaction locks")
    
    async def acquire_lock(self, interaction_id: str) -> bool:
        """Acquire interaction lock"""
        await self.cleanup_locks()

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
    
    def release_lock(self, interaction_id: str):
        """Release interaction lock"""
        if interaction_id in self._interaction_locks:
            try:
                if self._interaction_locks[interaction_id].locked():
                    self._interaction_locks[interaction_id].release()
            except:
                pass

class BaseButtonHandler:
    """Base class untuk button handlers"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.balance_service = BalanceService(bot.db_manager)
        self.product_service = ProductService(bot.db_manager)
        self.trx_manager = TransactionService(bot.db_manager)
        self.admin_service = AdminService(bot.db_manager)
        self.cache_manager = CacheManager()
        self.stats = ButtonStatistics()
        self.lock_manager = InteractionLockManager()
    
    async def handle_interaction_with_lock(self, interaction: discord.Interaction, handler_func, button_name: str):
        """Handle interaction with proper locking and statistics"""
        interaction_id = str(interaction.id)
        
        self.logger.info(f"[BUTTON_HANDLER] User {interaction.user.id} ({interaction.user.name}) mengklik tombol {button_name}")
        
        # Acquire lock
        if not await self.lock_manager.acquire_lock(interaction_id):
            self.logger.warning(f"[BUTTON_HANDLER] User {interaction.user.id} mencoba mengklik {button_name} saat masih ada proses yang berjalan")
            await interaction.response.send_message(
                "⏳ Mohon tunggu, sedang memproses permintaan sebelumnya...", 
                ephemeral=True
            )
            return
        
        try:
            self.logger.debug(f"[BUTTON_HANDLER] Memproses {button_name} untuk user {interaction.user.id}")
            await handler_func(interaction)
            self.stats.update_stats(button_name, success=True)
            self.logger.info(f"[BUTTON_HANDLER] ✅ {button_name} berhasil diproses untuk user {interaction.user.id}")
        except Exception as e:
            self.logger.error(f"[BUTTON_HANDLER] ❌ Error dalam {button_name} button handler untuk user {interaction.user.id}: {e}", exc_info=True)
            self.stats.update_stats(button_name, success=False)
            
            # Detailed error logging
            error_details = {
                'user_id': interaction.user.id,
                'username': interaction.user.name,
                'button': button_name,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'guild_id': interaction.guild_id if interaction.guild else None,
                'channel_id': interaction.channel_id if interaction.channel else None
            }
            self.logger.error(f"[BUTTON_ERROR_DETAILS] {error_details}")
            
            error_message = f"❌ Terjadi kesalahan saat memproses permintaan {button_name}.\nError: {type(e).__name__}"
            
            if not interaction.response.is_done():
                await interaction.response.send_message(error_message, ephemeral=True)
            else:
                await interaction.followup.send(error_message, ephemeral=True)
        finally:
            self.lock_manager.release_lock(interaction_id)
            self.logger.debug(f"[BUTTON_HANDLER] Lock released untuk {interaction_id}")

class RegisterButtonHandler(BaseButtonHandler):
    """Handler untuk button registrasi"""
    
    async def handle_register(self, interaction: discord.Interaction):
        """Handle register button click"""
        self.logger.info(f"[BUTTON_REGISTER] User {interaction.user.id} ({interaction.user.name}) clicked register button")
        
        # Check if user already registered
        growid_response = await self.balance_service.get_growid(str(interaction.user.id))
        if growid_response.success:
            # User already registered, show update option
            embed = discord.Embed(
                title="ℹ️ Sudah Terdaftar",
                description=f"Anda sudah terdaftar dengan GrowID: **{growid_response.data}**\n\nIngin memperbarui GrowID Anda?",
                color=COLORS.INFO
            )
            
            # Create view with update button
            view = UpdateGrowIDView(growid_response.data)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        
        # Show registration modal
        modal = RegisterModal()
        await interaction.response.send_modal(modal)

class BalanceButtonHandler(BaseButtonHandler):
    """Handler untuk button balance"""
    
    async def handle_balance(self, interaction: discord.Interaction):
        """Handle balance button click"""
        self.logger.info(f"[BUTTON_BALANCE] User {interaction.user.id} ({interaction.user.name}) clicked balance button")
        
        await interaction.response.defer(ephemeral=True)
        
        # Get user's GrowID
        growid_response = await self.balance_service.get_growid(str(interaction.user.id))
        if not growid_response.success:
            embed = discord.Embed(
                title="❌ Belum Terdaftar",
                description=MESSAGES.ERROR['NOT_REGISTERED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Get balance
        balance_response = await self.balance_service.get_balance(growid_response.data)
        if not balance_response.success:
            embed = discord.Embed(
                title="❌ Error",
                description=balance_response.error,
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        balance = balance_response.data
        embed = discord.Embed(
            title="💰 Saldo Anda",
            color=COLORS.SUCCESS,
            timestamp=datetime.utcnow()
        )
        embed.add_field(
            name="🏦 GrowID",
            value=f"**{growid_response.data}**",
            inline=False
        )
        embed.add_field(
            name="💎 World Lock",
            value=f"{balance.wl:,}",
            inline=True
        )
        embed.add_field(
            name="💰 Diamond Lock",
            value=f"{balance.dl:,}",
            inline=True
        )
        embed.add_field(
            name="🔥 Blue Gem Lock",
            value=f"{balance.bgl:,}",
            inline=True
        )
        embed.add_field(
            name="📊 Total (dalam WL)",
            value=f"{balance.total_wl():,.0f} WL",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class WorldInfoButtonHandler(BaseButtonHandler):
    """Handler untuk button world info"""
    
    async def handle_world_info(self, interaction: discord.Interaction):
        """Handle world info button click"""
        self.logger.info(f"[BUTTON_WORLD_INFO] User {interaction.user.id} ({interaction.user.name}) clicked world info button")
        
        await interaction.response.defer(ephemeral=True)
        
        # Get world info from database
        try:
            from src.database.connection import get_connection
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if world_info table exists, if not create it
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS world_info (
                    id INTEGER PRIMARY KEY,
                    world TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    bot TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default data if table is empty
            cursor.execute("SELECT COUNT(*) FROM world_info")
            count = cursor.fetchone()[0]
            
            if count == 0:
                cursor.execute("""
                    INSERT INTO world_info (id, world, owner, bot) 
                    VALUES (1, 'BUYWORLD', 'OWNER', 'BOTNAME')
                """)
                conn.commit()
            
            cursor.execute("SELECT world, owner, bot FROM world_info WHERE id = 1")
            result = cursor.fetchone()
            
            if result:
                embed = discord.Embed(
                    title="🌍 Informasi World",
                    color=COLORS.INFO,
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="🏠 World", value=result[0], inline=True)
                embed.add_field(name="👑 Owner", value=result[1], inline=True)
                embed.add_field(name="🤖 Bot", value=result[2], inline=True)
                embed.add_field(
                    name="📝 Catatan",
                    value="Pastikan Anda berada di world yang benar untuk melakukan transaksi.",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Informasi world tidak ditemukan.",
                    color=COLORS.ERROR
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"Error getting world info: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Gagal mengambil informasi world.",
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        finally:
            if 'conn' in locals() and conn:
                conn.close()

class UpdateGrowIDView(View):
    """View untuk update GrowID yang sudah terdaftar"""
    
    def __init__(self, current_growid: str):
        super().__init__(timeout=300)
        self.current_growid = current_growid
        self.logger = logging.getLogger("UpdateGrowIDView")
    
    @discord.ui.button(
        label="🔄 Perbarui GrowID",
        style=discord.ButtonStyle.primary,
        custom_id="update_growid"
    )
    async def update_growid_button(self, interaction: discord.Interaction, button: Button):
        """Button untuk update GrowID"""
        self.logger.info(f"[UPDATE_GROWID] User {interaction.user.id} clicked update GrowID button")
        
        # Show update modal
        modal = UpdateGrowIDModal(self.current_growid)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label="❌ Batal",
        style=discord.ButtonStyle.secondary,
        custom_id="cancel_update"
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Button untuk batal update"""
        embed = discord.Embed(
            title="✅ Dibatalkan",
            description="Update GrowID dibatalkan.",
            color=COLORS.INFO
        )
        await interaction.response.edit_message(embed=embed, view=None)

class UpdateGrowIDModal(Modal):
    """Modal untuk update GrowID"""
    
    def __init__(self, current_growid: str):
        super().__init__(title="🔄 Perbarui GrowID")
        self.current_growid = current_growid
        self.logger = logging.getLogger("UpdateGrowIDModal")

        self.growid = TextInput(
            label="Masukkan GrowID Baru",
            placeholder=f"GrowID saat ini: {current_growid}",
            min_length=3,
            max_length=20,
            required=True
        )
        self.add_item(self.growid)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle GrowID update submission"""
        self.logger.info(f"[UPDATE_GROWID_MODAL] User {interaction.user.id} attempting GrowID update")
        
        await interaction.response.defer(ephemeral=True)
        try:
            balance_service = BalanceService(interaction.client.db_manager)
            
            new_growid = str(self.growid.value).strip()
            self.logger.info(f"[UPDATE_GROWID_MODAL] Updating GrowID for user {interaction.user.id}: {self.current_growid} -> {new_growid}")
            
            if not new_growid or len(new_growid) < 3:
                self.logger.warning(f"[UPDATE_GROWID_MODAL] Invalid GrowID format from user {interaction.user.id}: {new_growid}")
                raise ValueError(MESSAGES.ERROR['INVALID_GROWID'])
            
            if new_growid == self.current_growid:
                raise ValueError("❌ GrowID baru sama dengan yang lama!")

            # Update GrowID
            update_response = await balance_service.update_growid(
                str(interaction.user.id),
                new_growid
            )

            if not update_response.success:
                raise ValueError(update_response.error)

            success_embed = discord.Embed(
                title="✅ Berhasil",
                description=f"GrowID berhasil diperbarui!\n\n**Lama:** {self.current_growid}\n**Baru:** {new_growid}",
                color=COLORS.SUCCESS
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            self.logger.info(f"[UPDATE_GROWID_MODAL] GrowID update successful for user {interaction.user.id}: {self.current_growid} -> {new_growid}")

        except ValueError as e:
            self.logger.warning(f"[UPDATE_GROWID_MODAL] GrowID update failed for user {interaction.user.id}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"[UPDATE_GROWID_MODAL] Unexpected error for user {interaction.user.id}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error",
                description="Gagal memperbarui GrowID. Silakan coba lagi.",
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
