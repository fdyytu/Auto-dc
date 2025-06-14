"""
Admin Commands Cog - Optimized
Menangani command admin dengan struktur yang lebih bersih
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime
from typing import Optional

from core.config import config_manager
from services.user_service import UserService
from services.product_service import ProductService
from handlers.command_handler import CommandHandler
from utils.formatters import message_formatter
from utils.validators import input_validator

logger = logging.getLogger(__name__)

class AdminCog(commands.Cog):
    """Cog untuk admin commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = config_manager
        self.user_service = UserService(bot.db_manager)
        self.product_service = ProductService(bot.db_manager)
        self.command_handler = CommandHandler(self.user_service, self.product_service)
    
    async def cog_check(self, ctx: commands.Context) -> bool:
        """Cek permission admin"""
        admin_id = self.config.get('admin_id')
        admin_roles = self.config.get_roles().get('admin')
        
        # Cek admin ID
        if ctx.author.id == admin_id:
            return True
        
        # Cek admin role
        if admin_roles:
            user_roles = [role.id for role in ctx.author.roles]
            if admin_roles in user_roles:
                return True
        
        return False
    
    @commands.command(name="addproduct")
    async def add_product(self, ctx, code: str, name: str, price: str, *, description: str = None):
        """Tambah produk baru"""
        try:
            # Validasi input
            if not input_validator.validate_product_code(code):
                await ctx.send(embed=message_formatter.error_embed("Kode produk tidak valid"))
                return
            
            validated_price = input_validator.validate_price(price)
            if not validated_price:
                await ctx.send(embed=message_formatter.error_embed("Harga tidak valid"))
                return
            
            # Buat produk
            success = await self.product_service.create_product(
                code.upper(), name, validated_price, description
            )
            
            if success:
                embed = message_formatter.success_embed(
                    "Produk Ditambahkan",
                    f"Kode: {code.upper()}\nNama: {name}\nHarga: {validated_price:,} WL"
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=message_formatter.error_embed("Gagal menambah produk"))
                
        except Exception as e:
            logger.error(f"Error add product: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error"))
    
    @commands.command(name="addstock")
    async def add_stock(self, ctx, code: str, *, content: str):
        """Tambah stock produk"""
        try:
            # Cek produk ada
            product = await self.product_service.get_product(code.upper())
            if not product:
                await ctx.send(embed=message_formatter.error_embed("Produk tidak ditemukan"))
                return
            
            # Tambah stock
            success = await self.product_service.add_stock(
                code.upper(), content, str(ctx.author.id)
            )
            
            if success:
                embed = message_formatter.success_embed(
                    "Stock Ditambahkan",
                    f"Produk: {product['name']} ({code.upper()})"
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=message_formatter.error_embed("Gagal menambah stock"))
                
        except Exception as e:
            logger.error(f"Error add stock: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error"))
    
    @commands.command(name="balance")
    async def manage_balance(self, ctx, action: str, growid: str, balance_type: str, amount: str):
        """Kelola balance user (add/remove)"""
        try:
            # Validasi input
            if action.lower() not in ['add', 'remove']:
                await ctx.send(embed=message_formatter.error_embed("Action harus 'add' atau 'remove'"))
                return
            
            if balance_type.lower() not in ['wl', 'dl', 'bgl']:
                await ctx.send(embed=message_formatter.error_embed("Balance type: wl, dl, atau bgl"))
                return
            
            validated_amount = input_validator.validate_price(amount)
            if not validated_amount:
                await ctx.send(embed=message_formatter.error_embed("Amount tidak valid"))
                return
            
            # Cek user ada
            user = await self.user_service.get_user_by_growid(growid)
            if not user:
                await ctx.send(embed=message_formatter.error_embed("User tidak ditemukan"))
                return
            
            # Update balance
            final_amount = validated_amount if action.lower() == 'add' else -validated_amount
            balance_field = f"balance_{balance_type.lower()}"
            
            success = await self.user_service.update_balance(growid, balance_field, final_amount)
            
            if success:
                embed = message_formatter.success_embed(
                    "Balance Diupdate",
                    f"User: {growid}\n{action.title()}: {validated_amount:,} {balance_type.upper()}"
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=message_formatter.error_embed("Gagal update balance"))
                
        except Exception as e:
            logger.error(f"Error manage balance: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error"))
    
    @commands.group(name="reload", invoke_without_command=True)
    async def reload_group(self, ctx):
        """Group command untuk hot reload"""
        embed = discord.Embed(
            title="🔄 Hot Reload Commands",
            description="Commands untuk mengelola hot reload system",
            color=0x00ff00
        )
        embed.add_field(
            name="Commands:",
            value="""
            `!reload status` - Cek status hot reload
            `!reload toggle` - Toggle hot reload on/off
            `!reload cog <nama>` - Reload cog tertentu
            `!reload all` - Reload semua cogs
            """,
            inline=False
        )
        await ctx.send(embed=embed)
    
    @reload_group.command(name="status")
    async def reload_status(self, ctx):
        """Cek status hot reload"""
        try:
            status = self.bot.hot_reload_manager.get_status()
            
            embed = discord.Embed(
                title="🔄 Hot Reload Status",
                color=0x00ff00 if status["enabled"] else 0xff0000
            )
            
            embed.add_field(
                name="Status",
                value="🟢 Aktif" if status["enabled"] else "🔴 Tidak Aktif",
                inline=True
            )
            embed.add_field(
                name="Watching Directories",
                value=str(status["watching"]),
                inline=True
            )
            embed.add_field(
                name="Loaded Extensions",
                value=str(status["loaded_extensions"]),
                inline=True
            )
            
            config_info = status["config"]
            embed.add_field(
                name="Configuration",
                value=f"""
                Auto Reload Cogs: {'✅' if config_info.get('auto_reload_cogs') else '❌'}
                Log Reloads: {'✅' if config_info.get('log_reloads') else '❌'}
                Reload Delay: {config_info.get('reload_delay', 1.0)}s
                """,
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting reload status: {e}")
            await ctx.send(embed=message_formatter.error_embed("Gagal mendapatkan status"))
    
    @reload_group.command(name="toggle")
    async def reload_toggle(self, ctx):
        """Toggle hot reload on/off"""
        try:
            if self.bot.hot_reload_manager.is_enabled():
                await self.bot.hot_reload_manager.stop()
                embed = message_formatter.success_embed(
                    "Hot Reload Dimatikan",
                    "Auto reload telah dinonaktifkan"
                )
            else:
                success = await self.bot.hot_reload_manager.start()
                if success:
                    embed = message_formatter.success_embed(
                        "Hot Reload Diaktifkan",
                        "Auto reload telah diaktifkan"
                    )
                else:
                    embed = message_formatter.error_embed("Gagal mengaktifkan hot reload")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error toggling reload: {e}")
            await ctx.send(embed=message_formatter.error_embed("Gagal toggle hot reload"))
    
    @reload_group.command(name="cog")
    async def reload_cog(self, ctx, cog_name: str):
        """Reload cog tertentu"""
        try:
            # Pastikan nama cog dalam format yang benar
            if not cog_name.startswith("cogs."):
                cog_name = f"cogs.{cog_name}"
            
            # Cek apakah cog ada
            if cog_name not in self.bot.extensions:
                await ctx.send(embed=message_formatter.error_embed(f"Cog {cog_name} tidak ditemukan"))
                return
            
            # Reload cog
            await self.bot.reload_extension(cog_name)
            
            embed = message_formatter.success_embed(
                "Cog Direload",
                f"✅ {cog_name} berhasil direload"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error reloading cog {cog_name}: {e}")
            await ctx.send(embed=message_formatter.error_embed(f"Gagal reload {cog_name}: {str(e)}"))
    
    @reload_group.command(name="all")
    async def reload_all(self, ctx):
        """Reload semua cogs"""
        try:
            # Kirim pesan loading
            loading_msg = await ctx.send("🔄 Reloading semua cogs...")
            
            # Reload semua cogs
            reloaded, failed = await self.bot.hot_reload_manager.reload_all_cogs()
            
            # Update pesan dengan hasil
            embed = discord.Embed(
                title="🔄 Reload All Cogs Complete",
                color=0x00ff00 if failed == 0 else 0xffaa00
            )
            embed.add_field(name="✅ Berhasil", value=str(reloaded), inline=True)
            embed.add_field(name="❌ Gagal", value=str(failed), inline=True)
            embed.add_field(name="📊 Total", value=str(reloaded + failed), inline=True)
            
            await loading_msg.edit(content="", embed=embed)
            
        except Exception as e:
            logger.error(f"Error reloading all cogs: {e}")
            await ctx.send(embed=message_formatter.error_embed("Gagal reload semua cogs"))

async def setup(bot):
    """Setup admin cog"""
    try:
        await bot.add_cog(AdminCog(bot))
        logger.info("Admin cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load admin cog: {e}")
        raise

