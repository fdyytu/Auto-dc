"""
Admin Backup Management - Manajemen backup dan restore database
"""

import discord
from discord.ext import commands
import logging
import asyncio
import os
import shutil
from datetime import datetime
from src.cogs.admin_base import AdminBaseCog
from src.database.manager import db_manager

logger = logging.getLogger(__name__)

class AdminBackupCog(AdminBaseCog):
    """Cog untuk manajemen backup database"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.db_file = "shop.db"
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)

    @commands.command(name="backup")
    async def backup_database(self, ctx):
        """Membuat dan mengirim backup database"""
        try:
            # Buat nama backup unik dengan timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"shop_backup_{timestamp}.db"
            backup_filepath = os.path.join(self.backup_dir, backup_filename)

            # Buat backup secara asynchronous
            await asyncio.to_thread(shutil.copy2, self.db_file, backup_filepath)

            # Buat embed modern
            embed = discord.Embed(
                title="📤 Backup Database",
                description="Backup database berhasil dibuat. File terlampir.",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="Info Backup",
                value=f"📁 Nama file: {backup_filename}\n"
                      f"⏰ Waktu: {timestamp}",
                inline=False
            )

            # Kirim file backup dengan embed
            await ctx.send(
                embed=embed,
                file=discord.File(backup_filepath, filename=backup_filename)
            )
            logger.info(f"Backup database berhasil: {backup_filename}")

        except Exception as e:
            logger.error(f"Error saat backup database: {e}")
            error_embed = discord.Embed(
                title="❌ Error Backup",
                description=f"Terjadi error saat membuat backup: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

    @commands.command(name="restore")
    async def restore_database(self, ctx):
        """Restore database dari file backup yang dilampirkan"""
        try:
            if not ctx.message.attachments:
                await ctx.send(embed=discord.Embed(
                    title="❌ Error Restore",
                    description="Silakan lampirkan file backup database (.db)",
                    color=0xff0000
                ))
                return

            attachment = ctx.message.attachments[0]
            if not attachment.filename.endswith('.db'):
                await ctx.send(embed=discord.Embed(
                    title="❌ Error Restore",
                    description="File harus berformat .db",
                    color=0xff0000
                ))
                return

            # Konfirmasi restore
            confirm_embed = discord.Embed(
                title="⚠️ Konfirmasi Restore",
                description="Restore akan mengganti database saat ini dengan backup.\n"
                           "Ketik `ya` untuk konfirmasi atau `tidak` untuk batal.",
                color=0xffaa00
            )
            await ctx.send(embed=confirm_embed)

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                response = await self.bot.wait_for('message', check=check, timeout=30.0)
                
                if response.content.lower() not in ['ya', 'yes', 'y']:
                    await ctx.send(embed=discord.Embed(
                        title="❌ Restore Dibatalkan",
                        description="Operasi restore dibatalkan.",
                        color=0xff0000
                    ))
                    return

                # Download file backup ke temp
                temp_filepath = os.path.join(self.backup_dir, f"temp_{attachment.filename}")
                await attachment.save(temp_filepath)

                # Aktifkan maintenance mode
                self.bot.maintenance_mode = True
                
                # Tunggu sebentar agar koneksi database yang ada selesai
                await asyncio.sleep(2)

                # Backup database existing sebagai precaution
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safety_backup = os.path.join(self.backup_dir, f"pre_restore_backup_{timestamp}.db")
                await asyncio.to_thread(shutil.copy2, self.db_file, safety_backup)

                # Replace database dengan file backup
                await asyncio.to_thread(shutil.copy2, temp_filepath, self.db_file)

                # Verifikasi database
                if not await db_manager.verify_database():
                    # Rollback jika verifikasi gagal
                    logger.error("Database verification failed after restore, rolling back")
                    await asyncio.to_thread(shutil.copy2, safety_backup, self.db_file)
                    raise Exception("Verifikasi database gagal setelah restore. Database dikembalikan ke kondisi sebelumnya.")

                # Nonaktifkan maintenance mode
                self.bot.maintenance_mode = False

                # Hapus file temporary
                os.remove(temp_filepath)

                success_embed = discord.Embed(
                    title="📥 Restore Database",
                    description="Database berhasil direstore!",
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                success_embed.add_field(
                    name="Info Restore",
                    value=f"📁 File backup: {attachment.filename}\n"
                          f"⏰ Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    inline=False
                )
                await ctx.send(embed=success_embed)
                logger.info(f"Database berhasil direstore dari {attachment.filename}")

            except asyncio.TimeoutError:
                await ctx.send(embed=discord.Embed(
                    title="⏰ Timeout",
                    description="Konfirmasi restore timeout. Operasi dibatalkan.",
                    color=0xff0000
                ))

        except Exception as e:
            logger.error(f"Error saat restore database: {e}")
            # Pastikan maintenance mode dinonaktifkan jika terjadi error
            self.bot.maintenance_mode = False
            
            error_embed = discord.Embed(
                title="❌ Error Restore",
                description=f"Terjadi error saat restore database: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    """Setup admin backup cog"""
    try:
        await bot.add_cog(AdminBackupCog(bot))
        logger.info("Admin backup cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load admin backup cog: {e}")
        raise
