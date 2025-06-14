"""
Shop View untuk interface toko utama
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import discord
from discord.ui import View, Button
from discord import ui
import logging
import asyncio
from datetime import datetime
from typing import Dict

from config.constants import COLORS, MESSAGES, BUTTON_IDS, CURRENCY_RATES
from data.models.balance import Balance
from services.product_service import ProductService
from services.balance_service import BalanceService
from services.transaction_service import TransactionService
from services.admin_service import AdminService
from services.cache_service import CacheManager
from ui.modals.register_modal import RegisterModal
from ui.selects.product_select import ProductSelect

logger = logging.getLogger(__name__)

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
        style=discord.ButtonStyle.primary,
        label="📝 Daftar",
        custom_id=BUTTON_IDS.REGISTER
    )
    async def register_callback(self, interaction: discord.Interaction, button: Button):
        if not await self._acquire_interaction_lock(str(interaction.id)):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Mohon Tunggu",
                    description=MESSAGES.INFO['PROCESSING'],
                    color=COLORS.WARNING
                ),
                ephemeral=True
            )
            return

        try:
            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                raise ValueError(MESSAGES.ERROR['MAINTENANCE_MODE'])

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
            self.logger.error(f"Error in register callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Error",
                        description=MESSAGES.ERROR['TRANSACTION_FAILED'],
                        color=COLORS.ERROR
                    ),
                    ephemeral=True
                )
        finally:
            self._release_interaction_lock(str(interaction.id))

    @discord.ui.button(
        style=discord.ButtonStyle.success,
        label="💰 Saldo",
        custom_id=BUTTON_IDS.BALANCE
    )
    async def balance_callback(self, interaction: discord.Interaction, button: Button):
        if not await self._acquire_interaction_lock(str(interaction.id)):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Mohon Tunggu",
                    description=MESSAGES.INFO['PROCESSING'],
                    color=COLORS.WARNING
                ),
                ephemeral=True
            )
            return

        try:
            await interaction.response.defer(ephemeral=True)

            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                raise ValueError(MESSAGES.ERROR['MAINTENANCE_MODE'])

            growid_response = await self.balance_service.get_growid(str(interaction.user.id))
            if not growid_response.success:
                raise ValueError(growid_response.error)

            growid = growid_response.data
            if not growid:
                raise ValueError(MESSAGES.ERROR['USER_NOT_REGISTERED'])

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
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error in balance callback: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=MESSAGES.ERROR['TRANSACTION_FAILED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        finally:
            self._release_interaction_lock(str(interaction.id))
