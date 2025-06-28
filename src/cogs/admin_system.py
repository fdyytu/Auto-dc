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
    
    @commands.command(name="systeminfo")
    async def system_info(self, ctx):
        """Tampilkan informasi sistem bot"""
        try:
            import psutil
            import platform
            from datetime import datetime, timedelta
            
            # Informasi sistem
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Informasi bot
            bot_uptime = datetime.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
            
            embed = discord.Embed(
                title="🖥️ Informasi Sistem Bot",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            # Sistem
            embed.add_field(
                name="💻 Sistem",
                value=f"OS: {platform.system()} {platform.release()}\n"
                      f"Python: {platform.python_version()}\n"
                      f"Discord.py: {discord.__version__}",
                inline=False
            )
            
            # Performa
            embed.add_field(
                name="📊 Performa",
                value=f"CPU: {cpu_percent}%\n"
                      f"RAM: {memory.percent}% ({memory.used // 1024 // 1024} MB / {memory.total // 1024 // 1024} MB)\n"
                      f"Disk: {disk.percent}% ({disk.used // 1024 // 1024 // 1024} GB / {disk.total // 1024 // 1024 // 1024} GB)",
                inline=False
            )
            
            # Bot Stats
            if bot_uptime:
                uptime_str = str(bot_uptime).split('.')[0]  # Remove microseconds
            else:
                uptime_str = "Tidak diketahui"
                
            embed.add_field(
                name="🤖 Bot Stats",
                value=f"Uptime: {uptime_str}\n"
                      f"Guilds: {len(self.bot.guilds)}\n"
                      f"Users: {len(self.bot.users)}\n"
                      f"Commands: {len(self.bot.commands)}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error system info: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat mengambil info sistem"))
    
    @commands.command(name="maintenance")
    async def maintenance_mode(self, ctx, mode: str):
        """Toggle maintenance mode"""
        try:
            if mode.lower() not in ['on', 'off']:
                await ctx.send(embed=message_formatter.error_embed("Mode harus 'on' atau 'off'"))
                return
            
            # Set maintenance mode
            if mode.lower() == 'on':
                # Enable maintenance mode
                self.bot.maintenance_mode = True
                embed = message_formatter.info_embed(
                    "🔧 Mode Maintenance Diaktifkan\n"
                    "Bot sekarang dalam mode maintenance. Hanya admin yang dapat menggunakan commands."
                )
            else:
                # Disable maintenance mode
                self.bot.maintenance_mode = False
                embed = message_formatter.success_embed(
                    "✅ Mode Maintenance Dinonaktifkan\n"
                    "Bot kembali normal dan dapat digunakan semua user."
                )
            
            await ctx.send(embed=embed)
            logger.info(f"Maintenance mode {mode} by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error maintenance mode: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat mengatur maintenance mode"))
    
    @commands.command(name="blacklist")
    async def blacklist_user(self, ctx, action: str, growid: str):
        """Manage blacklisted users"""
        try:
            if action.lower() not in ['add', 'remove']:
                await ctx.send(embed=message_formatter.error_embed("Action harus 'add' atau 'remove'"))
                return
            
            # Initialize blacklist if not exists
            if not hasattr(self.bot, 'blacklisted_users'):
                self.bot.blacklisted_users = set()
            
            if action.lower() == 'add':
                self.bot.blacklisted_users.add(growid.lower())
                embed = message_formatter.success_embed(
                    f"User {growid} berhasil ditambahkan ke blacklist"
                )
                logger.info(f"User {growid} blacklisted by {ctx.author}")
            else:
                if growid.lower() in self.bot.blacklisted_users:
                    self.bot.blacklisted_users.remove(growid.lower())
                    embed = message_formatter.success_embed(
                        f"User {growid} berhasil dihapus dari blacklist"
                    )
                    logger.info(f"User {growid} removed from blacklist by {ctx.author}")
                else:
                    embed = message_formatter.error_embed(
                        f"User {growid} tidak ada dalam blacklist"
                    )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error blacklist: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat mengelola blacklist"))

async def setup(bot):
    """Setup admin system cog"""
    try:
        await bot.add_cog(AdminSystemCog(bot))
        logger.info("Admin system cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load admin system cog: {e}")
        raise
