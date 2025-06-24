"""
Command Handler
Menangani processing command dengan clean architecture
"""

import logging
from typing import Optional, Dict, Any, Callable
from discord.ext import commands
import discord

from services.user_service import UserService
from services.product_service import ProductService
from core.config import config_manager

logger = logging.getLogger(__name__)

class CommandHandler:
    """Handler untuk processing command"""
    
    def __init__(self, user_service: UserService, product_service: ProductService):
        self.user_service = user_service
        self.product_service = product_service
        self.config = config_manager
        self.cooldowns = {}
    
    async def check_permissions(self, ctx: commands.Context, required_permission: str) -> bool:
        """Cek permission user untuk command"""
        try:
            user_roles = [role.id for role in ctx.author.roles]
            permissions = self.config.get_permissions()
            
            for role_name, role_perms in permissions.items():
                role_id = self.config.get_roles().get(role_name)
                if role_id in user_roles:
                    if "all" in role_perms or required_permission in role_perms:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error check permissions: {e}")
            return False
    
    async def check_cooldown(self, ctx: commands.Context, command_name: str) -> bool:
        """Cek cooldown command"""
        try:
            cooldowns = self.config.get_cooldowns()
            cooldown_time = cooldowns.get(command_name, cooldowns.get('default', 3))
            
            user_id = str(ctx.author.id)
            current_time = ctx.message.created_at.timestamp()
            
            if user_id in self.cooldowns:
                last_used = self.cooldowns[user_id].get(command_name, 0)
                if current_time - last_used < cooldown_time:
                    remaining = cooldown_time - (current_time - last_used)
                    await ctx.send(f"⏰ Command masih cooldown. Tunggu {remaining:.1f} detik.")
                    return False
            
            # Update cooldown
            if user_id not in self.cooldowns:
                self.cooldowns[user_id] = {}
            self.cooldowns[user_id][command_name] = current_time
            
            return True
            
        except Exception as e:
            logger.error(f"Error check cooldown: {e}")
            return True
    
    async def handle_user_command(self, ctx: commands.Context, action: str, **kwargs) -> bool:
        """Handle command yang berkaitan dengan user"""
        try:
            if action == "register":
                growid = kwargs.get('growid')
                if not growid:
                    await ctx.send("❌ Growid diperlukan untuk registrasi.")
                    return False
                
                success = await self.user_service.create_user(growid, str(ctx.author.id))
                if success:
                    await ctx.send(f"✅ User {growid} berhasil didaftarkan!")
                    await self.user_service.log_user_activity(str(ctx.author.id), "register", growid)
                else:
                    await ctx.send("❌ Gagal mendaftarkan user. Mungkin sudah terdaftar.")
                return success
            
            elif action == "balance":
                user = await self.user_service.get_user_by_discord_id(str(ctx.author.id))
                if not user:
                    await ctx.send("❌ Anda belum terdaftar. Gunakan `!register <growid>`")
                    return False
                
                balance = await self.user_service.get_user_balance(user['growid'])
                if balance:
                    embed = discord.Embed(title="💰 Balance Anda", color=0x00ff00)
                    embed.add_field(name="World Lock", value=f"{balance['wl']:,}", inline=True)
                    embed.add_field(name="Diamond Lock", value=f"{balance['dl']:,}", inline=True)
                    embed.add_field(name="Blue Gem Lock", value=f"{balance['bgl']:,}", inline=True)
                    await ctx.send(embed=embed)
                    return True
                else:
                    await ctx.send("❌ Gagal mengambil balance.")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error handle user command: {e}")
            await ctx.send("❌ Terjadi error saat memproses command.")
            return False
    
    async def handle_product_command(self, ctx: commands.Context, action: str, **kwargs) -> bool:
        """Handle command yang berkaitan dengan product"""
        try:
            if action == "list":
                products = await self.product_service.get_all_products()
                if not products:
                    await ctx.send("📦 Tidak ada produk tersedia.")
                    return True
                
                embed = discord.Embed(title="🛒 Daftar Produk", color=0x0099ff)
                for product in products[:10]:  # Limit 10 products
                    stock_count = await self.product_service.get_product_stock_count(product['code'])
                    embed.add_field(
                        name=f"{product['name']} ({product['code']})",
                        value=f"Harga: {product['price']:,} WL\nStock: {stock_count}",
                        inline=True
                    )
                
                await ctx.send(embed=embed)
                return True
            
            elif action == "info":
                code = kwargs.get('code')
                if not code:
                    await ctx.send("❌ Kode produk diperlukan.")
                    return False
                
                product = await self.product_service.get_product(code)
                if not product:
                    await ctx.send("❌ Produk tidak ditemukan.")
                    return False
                
                stock_count = await self.product_service.get_product_stock_count(code)
                embed = discord.Embed(title=f"📦 {product['name']}", color=0x0099ff)
                embed.add_field(name="Kode", value=product['code'], inline=True)
                embed.add_field(name="Harga", value=f"{product['price']:,} WL", inline=True)
                embed.add_field(name="Stock", value=stock_count, inline=True)
                if product['description']:
                    embed.add_field(name="Deskripsi", value=product['description'], inline=False)
                
                await ctx.send(embed=embed)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handle product command: {e}")
            await ctx.send("❌ Terjadi error saat memproses command.")
            return False
