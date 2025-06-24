"""
Admin Commands Cog - Optimized
Menangani command admin dengan struktur yang lebih bersih
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime
from typing import Optional

from src.bot.config import config_manager
from src.services.user_service import UserService
from src.services.product_service import ProductService
from src.services.world_service import WorldService
from src.handlers.command_handler import CommandHandler
from src.utils.formatters import message_formatter
from src.utils.validators import input_validator

logger = logging.getLogger(__name__)

class AdminCog(commands.Cog):
    """Cog untuk admin commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = config_manager
        self.user_service = UserService(bot.db_manager)
        self.product_service = ProductService(bot.db_manager)
        self.world_service = WorldService(bot.db_manager)
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
    
    @commands.group(name="world", invoke_without_command=True)
    async def world_group(self, ctx):
        """Group command untuk world management"""
        embed = discord.Embed(
            title="🌍 World Management Commands",
            description="Commands untuk mengelola world system",
            color=0x00ff00
        )
        embed.add_field(
            name="Commands:",
            value="""
            `!world add <world> <owner> <bot>` - Tambah world baru
            `!world list` - Lihat semua world
            `!world info <world>` - Info detail world
            `!world update <world> [owner] [bot]` - Update world
            `!world remove <world>` - Hapus world
            """,
            inline=False
        )
        await ctx.send(embed=embed)
    
    @world_group.command(name="add")
    async def world_add(self, ctx, world_name: str, owner_name: str, bot_name: str):
        """Tambah world baru"""
        try:
            response = await self.world_service.add_world(world_name, owner_name, bot_name)
            
            if response.success:
                embed = message_formatter.success_embed(
                    "World Ditambahkan",
                    f"World: {world_name}\nOwner: {owner_name}\nBot: {bot_name}"
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=message_formatter.error_embed(response.error))
                
        except Exception as e:
            logger.error(f"Error adding world: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error"))
    
    @world_group.command(name="list")
    async def world_list(self, ctx):
        """Lihat semua world"""
        try:
            response = await self.world_service.get_all_worlds()
            
            if not response.success:
                await ctx.send(embed=message_formatter.error_embed(response.error))
                return
            
            worlds = response.data
            if not worlds:
                await ctx.send(embed=message_formatter.info_embed("Tidak ada world yang terdaftar"))
                return
            
            embed = discord.Embed(
                title="🌍 Daftar World",
                color=0x00ff00
            )
            
            for world in worlds:
                embed.add_field(
                    name=f"🌍 {world['world_name']}",
                    value=f"Owner: {world['owner_name']}\nBot: {world['bot_name']}\nCreated: {world['created_at'][:10]}",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing worlds: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error"))
    
    @world_group.command(name="info")
    async def world_info(self, ctx, world_name: str):
        """Info detail world"""
        try:
            response = await self.world_service.get_world(world_name)
            
            if not response.success:
                await ctx.send(embed=message_formatter.error_embed(response.error))
                return
            
            world = response.data
            embed = discord.Embed(
                title=f"🌍 {world['world_name']}",
                color=0x00ff00
            )
            embed.add_field(name="Owner", value=world['owner_name'], inline=True)
            embed.add_field(name="Bot", value=world['bot_name'], inline=True)
            embed.add_field(name="Status", value="🟢 Active" if world['is_active'] else "🔴 Inactive", inline=True)
            embed.add_field(name="Created", value=world['created_at'][:19], inline=True)
            embed.add_field(name="Updated", value=world['updated_at'][:19], inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting world info: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error"))
    
    @world_group.command(name="update")
    async def world_update(self, ctx, world_name: str, owner_name: str = None, bot_name: str = None):
        """Update world data"""
        try:
            if not owner_name and not bot_name:
                await ctx.send(embed=message_formatter.error_embed("Minimal satu parameter harus diisi"))
                return
            
            response = await self.world_service.update_world(world_name, owner_name, bot_name)
            
            if response.success:
                embed = message_formatter.success_embed(
                    "World Diupdate",
                    f"World {world_name} berhasil diupdate"
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=message_formatter.error_embed(response.error))
                
        except Exception as e:
            logger.error(f"Error updating world: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error"))
    
    @world_group.command(name="remove")
    async def world_remove(self, ctx, world_name: str):
        """Hapus world"""
        try:
            response = await self.world_service.delete_world(world_name)
            
            if response.success:
                embed = message_formatter.success_embed(
                    "World Dihapus",
                    f"World {world_name} berhasil dihapus"
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=message_formatter.error_embed(response.error))
                
        except Exception as e:
            logger.error(f"Error removing world: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error"))

async def setup(bot):
    """Setup admin cog"""
    try:
        await bot.add_cog(AdminCog(bot))
        logger.info("Admin cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load admin cog: {e}")
        raise

