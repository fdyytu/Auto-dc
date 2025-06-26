"""
Admin Base Class - Shared utilities untuk admin commands
Menangani permission check dan base functionality
"""

import discord
from discord.ext import commands
import logging

from src.bot.config import config_manager
from src.utils.formatters import message_formatter

logger = logging.getLogger(__name__)

class AdminBaseCog(commands.Cog):
    """Base class untuk admin cogs dengan shared functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = config_manager
    
    async def cog_check(self, ctx: commands.Context) -> bool:
        """Cek permission admin dengan logging detail"""
        admin_id = self.config.get('admin_id')
        admin_role_id = self.config.get_roles().get('admin')
        
        # Log informasi debug
        logger.info(f"🔍 Admin check untuk user: {ctx.author.name} (ID: {ctx.author.id})")
        logger.info(f"📋 Admin ID dari config: {admin_id} (tipe: {type(admin_id)})")
        logger.info(f"📋 Admin Role ID dari config: {admin_role_id} (tipe: {type(admin_role_id)})")
        
        # Cek admin ID
        if ctx.author.id == admin_id:
            logger.info(f"✅ User {ctx.author.name} dikenali sebagai admin berdasarkan User ID")
            return True
        else:
            logger.info(f"❌ User ID {ctx.author.id} tidak cocok dengan admin ID {admin_id}")
        
        # Cek admin role
        if admin_role_id:
            user_role_ids = [role.id for role in ctx.author.roles]
            logger.info(f"👥 Role user: {[f'{role.name}({role.id})' for role in ctx.author.roles]}")
            logger.info(f"🔍 Mencari admin role ID {admin_role_id} dalam role user: {user_role_ids}")
            
            if admin_role_id in user_role_ids:
                logger.info(f"✅ User {ctx.author.name} dikenali sebagai admin berdasarkan Role")
                return True
            else:
                logger.info(f"❌ Admin role ID {admin_role_id} tidak ditemukan dalam role user")
        else:
            logger.info("⚠️ Admin role ID tidak dikonfigurasi")
        
        logger.warning(f"🚫 User {ctx.author.name} (ID: {ctx.author.id}) TIDAK dikenali sebagai admin")
        
        # Kirim pesan error yang informatif
        embed = discord.Embed(
            title="🚫 Akses Ditolak",
            description="Anda tidak memiliki izin untuk menggunakan command admin.",
            color=0xff0000
        )
        embed.add_field(
            name="ℹ️ Info",
            value=f"Command admin hanya dapat digunakan oleh:\n"
                  f"• User dengan ID: `{admin_id}`\n"
                  f"• User dengan role admin (ID: `{admin_role_id}`)",
            inline=False
        )
        embed.add_field(
            name="🔍 Debug Info",
            value=f"Your ID: `{ctx.author.id}`\n"
                  f"Your Roles: {', '.join([f'`{role.name}`' for role in ctx.author.roles])}",
            inline=False
        )
        
        try:
            await ctx.send(embed=embed, delete_after=10)
        except:
            pass  # Ignore jika gagal kirim pesan
        
        return False

async def setup(bot):
    """Setup function untuk loading cog"""
    await bot.add_cog(AdminBaseCog(bot))
    logger.info("Admin base cog loaded successfully")
