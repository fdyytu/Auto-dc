"""
Admin System Management - Manajemen sistem bot
Menangani command untuk restart dan maintenance
"""

import discord
from discord.ext import commands
import logging
import asyncio
import os
import sys

from src.cogs.admin_base import AdminBaseCog
from src.utils.formatters import message_formatter

logger = logging.getLogger(__name__)

class AdminSystemCog(AdminBaseCog):
    """Cog untuk manajemen sistem admin"""
    
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.command(name="restart")
    async def restart_bot(self, ctx):
        """Restart bot dengan konfirmasi"""
        try:
            # Konfirmasi restart
            confirm_embed = discord.Embed(
                title="⚠️ Konfirmasi Restart",
                description="Apakah Anda yakin ingin restart bot?\n"
                           "Ketik `ya` untuk konfirmasi atau `tidak` untuk batal.",
                color=0xffaa00
            )
            await ctx.send(embed=confirm_embed)
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            try:
                response = await self.bot.wait_for('message', check=check, timeout=30.0)
                
                if response.content.lower() in ['ya', 'yes', 'y']:
                    restart_embed = discord.Embed(
                        title="🔄 Restarting Bot",
                        description="Bot sedang restart... Mohon tunggu.",
                        color=0x00ff00
                    )
                    await ctx.send(embed=restart_embed)
                    
                    # Cleanup sebelum restart
                    await self._cleanup_before_restart()
                    
                    # Restart menggunakan execv
                    os.execv(sys.executable, ['python'] + sys.argv)
                    
                else:
                    cancel_embed = discord.Embed(
                        title="❌ Restart Dibatalkan",
                        description="Restart bot dibatalkan.",
                        color=0xff0000
                    )
                    await ctx.send(embed=cancel_embed)
                    
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⏰ Timeout",
                    description="Konfirmasi restart timeout. Restart dibatalkan.",
                    color=0xff0000
                )
                await ctx.send(embed=timeout_embed)
                
        except Exception as e:
            logger.error(f"Error restart command: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat restart"))

    async def _cleanup_before_restart(self):
        """Membersihkan cache dan state sebelum restart"""
        try:
            logger.info("🧹 Memulai pembersihan sebelum restart...")
            
            # Cleanup cache dan state
            try:
                from src.services.cache_service import CacheManager
                cache_manager = CacheManager()
                await cache_manager.clear()
                logger.info("✅ Cache system dibersihkan")
            except Exception as e:
                logger.error(f"❌ Error membersihkan cache: {e}")
            
            logger.info("🎉 Pembersihan sebelum restart selesai")
            
        except Exception as e:
            logger.error(f"❌ Error dalam pembersihan sebelum restart: {e}")

async def setup(bot):
    """Setup admin system cog"""
    try:
        await bot.add_cog(AdminSystemCog(bot))
        logger.info("Admin system cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load admin system cog: {e}")
        raise
