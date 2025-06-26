"""
Admin Balance Management - Manajemen balance user
Menangani command untuk mengelola balance user
"""

import discord
from discord.ext import commands
import logging

from src.cogs.admin_base import AdminBaseCog
from src.services.balance_service import BalanceManagerService
from src.utils.formatters import message_formatter
from src.utils.validators import input_validator

logger = logging.getLogger(__name__)

class AdminBalanceCog(AdminBaseCog):
    """Cog untuk manajemen balance admin"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.balance_service = BalanceManagerService(bot)
    
    @commands.command(name="addbal")
    async def add_balance(self, ctx, growid: str, amount: str, balance_type: str = "WL"):
        """Tambah balance user - Command yang hilang"""
        try:
            # Validasi input
            validated_amount = input_validator.validate_amount(amount)
            if not validated_amount:
                await ctx.send(embed=message_formatter.error_embed("Jumlah tidak valid"))
                return
            
            balance_type = balance_type.upper()
            if balance_type not in ["WL", "DL", "BGL"]:
                await ctx.send(embed=message_formatter.error_embed("Tipe balance tidak valid (WL/DL/BGL)"))
                return
            
            # Tentukan parameter berdasarkan tipe balance
            wl = validated_amount if balance_type == "WL" else 0
            dl = validated_amount if balance_type == "DL" else 0
            bgl = validated_amount if balance_type == "BGL" else 0
            
            # Update balance
            response = await self.balance_service.update_balance(
                growid=growid,
                wl=wl,
                dl=dl,
                bgl=bgl,
                transaction_type="admin_add"
            )
            
            if response.success:
                embed = message_formatter.success_embed(
                    f"Balance berhasil ditambahkan!\n"
                    f"User: {growid}\n"
                    f"Ditambah: {validated_amount:,} {balance_type}"
                )
            else:
                embed = message_formatter.error_embed(f"Gagal menambah balance: {response.error}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error add balance: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat menambah balance"))

async def setup(bot):
    """Setup admin balance cog"""
    try:
        await bot.add_cog(AdminBalanceCog(bot))
        logger.info("Admin balance cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load admin balance cog: {e}")
        raise
