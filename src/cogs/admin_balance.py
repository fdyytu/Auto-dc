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
from src.config.constants.bot_constants import TransactionType

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
                transaction_type=TransactionType.ADMIN_ADD
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
    
    @commands.command(name="removebal")
    async def remove_balance(self, ctx, growid: str, amount: str, balance_type: str = "WL"):
        """Kurangi balance user"""
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
            
            # Tentukan parameter berdasarkan tipe balance (negatif untuk mengurangi)
            wl = -validated_amount if balance_type == "WL" else 0
            dl = -validated_amount if balance_type == "DL" else 0
            bgl = -validated_amount if balance_type == "BGL" else 0
            
            # Update balance
            response = await self.balance_service.update_balance(
                growid=growid,
                wl=wl,
                dl=dl,
                bgl=bgl,
                transaction_type=TransactionType.ADMIN_REMOVE
            )
            
            if response.success:
                embed = message_formatter.success_embed(
                    f"Balance berhasil dikurangi!\n"
                    f"User: {growid}\n"
                    f"Dikurangi: {validated_amount:,} {balance_type}"
                )
            else:
                embed = message_formatter.error_embed(f"Gagal mengurangi balance: {response.error}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error remove balance: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat mengurangi balance"))
    
    @commands.command(name="checkbal")
    async def check_balance(self, ctx, growid: str):
        """Cek balance user"""
        try:
            response = await self.balance_service.get_balance(growid)
            
            if response.success and response.data:
                balance_data = response.data
                embed = discord.Embed(
                    title=f"💰 Balance {growid}",
                    color=0x00ff00
                )
                embed.add_field(
                    name="World Locks (WL)",
                    value=f"{balance_data.wl:,}",
                    inline=True
                )
                embed.add_field(
                    name="Diamond Locks (DL)",
                    value=f"{balance_data.dl:,}",
                    inline=True
                )
                embed.add_field(
                    name="Blue Gem Locks (BGL)",
                    value=f"{balance_data.bgl:,}",
                    inline=True
                )
            else:
                embed = message_formatter.error_embed("User tidak ditemukan atau belum terdaftar")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error check balance: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat mengecek balance"))
    
    @commands.command(name="resetuser")
    async def reset_user(self, ctx, growid: str):
        """Reset balance user ke 0"""
        try:
            # Konfirmasi reset
            confirm_embed = discord.Embed(
                title="⚠️ Konfirmasi Reset",
                description=f"Apakah Anda yakin ingin reset balance {growid}?\n"
                           "Ketik `ya` untuk konfirmasi atau `tidak` untuk batal.",
                color=0xffaa00
            )
            await ctx.send(embed=confirm_embed)
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            try:
                response = await self.bot.wait_for('message', check=check, timeout=30.0)
                
                if response.content.lower() in ['ya', 'yes', 'y']:
                    # Reset balance ke 0
                    reset_response = await self.balance_service.reset_balance(growid)
                    
                    if reset_response.success:
                        embed = message_formatter.success_embed(
                            f"Balance {growid} berhasil direset!\n"
                            f"Semua balance telah dikembalikan ke 0."
                        )
                    else:
                        embed = message_formatter.error_embed(f"Gagal reset balance: {reset_response.error}")
                else:
                    embed = discord.Embed(
                        title="❌ Reset Dibatalkan",
                        description="Reset balance dibatalkan.",
                        color=0xff0000
                    )
                
                await ctx.send(embed=embed)
                
            except Exception as timeout_error:
                timeout_embed = discord.Embed(
                    title="⏰ Timeout",
                    description="Konfirmasi reset timeout. Reset dibatalkan.",
                    color=0xff0000
                )
                await ctx.send(embed=timeout_embed)
                
        except Exception as e:
            logger.error(f"Error reset user: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat reset user"))

async def setup(bot):
    """Setup admin balance cog"""
    try:
        await bot.add_cog(AdminBalanceCog(bot))
        logger.info("Admin balance cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load admin balance cog: {e}")
        raise
