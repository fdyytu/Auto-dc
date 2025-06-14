"""
Button Handler Components for Live Buttons
Author: fdyytu
Created at: 2025-01-XX XX:XX:XX UTC

Komponen button handlers yang dipisahkan dari live_buttons.py
"""

import discord
from discord.ui import View, Button
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from config.constants.bot_constants import COLORS, MESSAGES, BUTTON_IDS
from services.balance_service import BalanceManagerService as BalanceService
from services.product_service import ProductService
from services.transaction_service import TransactionManager as TransactionService
from services.admin_service import AdminService
from services.cache_service import CacheManager
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
        
        # Acquire lock
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

class RegisterButtonHandler(BaseButtonHandler):
    """Handler untuk button registrasi"""
    
    async def handle_register(self, interaction: discord.Interaction):
        """Handle register button click"""
        self.logger.info(f"[BUTTON_REGISTER] User {interaction.user.id} ({interaction.user.name}) clicked register button")
        
        # Check if user already registered
        growid_response = await self.balance_service.get_growid(str(interaction.user.id))
        if growid_response.success:
            embed = discord.Embed(
                title="ℹ️ Sudah Terdaftar",
                description=f"Anda sudah terdaftar dengan GrowID: **{growid_response.data}**",
                color=COLORS.INFO
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
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
            conn = self.bot.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT world, owner, bot FROM world_info WHERE id = 1")
            result = cursor.fetchone()
            
            if result:
                embed = discord.Embed(
                    title="🌍 Informasi World",
                    color=COLORS.INFO,
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="🏠 World", value=result['world'], inline=True)
                embed.add_field(name="👑 Owner", value=result['owner'], inline=True)
                embed.add_field(name="🤖 Bot", value=result['bot'], inline=True)
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
            if conn:
                conn.close()
