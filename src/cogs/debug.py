"""
Debug Commands Cog
Command untuk debugging tanpa admin check
"""

import discord
from discord.ext import commands
import logging

from src.bot.config import config_manager

logger = logging.getLogger(__name__)

class DebugCog(commands.Cog):
    """Cog untuk debug commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = config_manager
    
    @commands.command(name="debugadmin")
    async def debug_admin(self, ctx):
        """Debug admin detection - dapat digunakan siapa saja"""
        try:
            admin_id = self.config.get('admin_id')
            admin_role_id = self.config.get_roles().get('admin')
            
            embed = discord.Embed(
                title="🔍 Debug Admin Detection",
                description="Informasi debug untuk admin detection:",
                color=0x00ff00
            )
            
            # Info user
            embed.add_field(
                name="👤 User Info",
                value=f"Nama: {ctx.author.name}\nID: {ctx.author.id}\nDiscriminator: {ctx.author.discriminator}",
                inline=False
            )
            
            # Info config
            embed.add_field(
                name="⚙️ Config Info",
                value=f"Admin ID: {admin_id} (tipe: {type(admin_id)})\nAdmin Role ID: {admin_role_id} (tipe: {type(admin_role_id)})",
                inline=False
            )
            
            # Info roles detail
            user_roles = []
            for role in ctx.author.roles:
                user_roles.append(f"{role.name} (ID: {role.id})")
            
            embed.add_field(
                name="👥 User Roles Detail",
                value="\n".join(user_roles) if user_roles else "Tidak ada role",
                inline=False
            )
            
            # Test hasil detail
            is_admin_by_id = ctx.author.id == admin_id
            user_role_ids = [role.id for role in ctx.author.roles]
            is_admin_by_role = admin_role_id in user_role_ids if admin_role_id else False
            
            # Comparison detail
            comparison_text = f"User ID ({ctx.author.id}) == Admin ID ({admin_id}): {is_admin_by_id}\n"
            comparison_text += f"User Role IDs: {user_role_ids}\n"
            comparison_text += f"Admin Role ID in User Roles: {is_admin_by_role}"
            
            embed.add_field(
                name="🔍 Comparison Detail",
                value=comparison_text,
                inline=False
            )
            
            embed.add_field(
                name="✅ Final Results",
                value=f"Admin by ID: {'✅ Ya' if is_admin_by_id else '❌ Tidak'}\n"
                      f"Admin by Role: {'✅ Ya' if is_admin_by_role else '❌ Tidak'}\n"
                      f"Overall Admin: {'✅ Ya' if (is_admin_by_id or is_admin_by_role) else '❌ Tidak'}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
            # Log ke console juga
            logger.info(f"🔍 Debug Admin untuk {ctx.author.name} ({ctx.author.id})")
            logger.info(f"📋 Config Admin ID: {admin_id}, Role ID: {admin_role_id}")
            logger.info(f"👥 User Roles: {user_role_ids}")
            logger.info(f"✅ Result: ID={is_admin_by_id}, Role={is_admin_by_role}")
            
        except Exception as e:
            logger.error(f"Error debug admin: {e}")
            await ctx.send(f"❌ Error saat debug: {e}")

    @commands.command(name="configinfo")
    async def config_info(self, ctx):
        """Tampilkan informasi config"""
        try:
            config_data = self.config._config
            
            embed = discord.Embed(
                title="⚙️ Config Information",
                description="Informasi konfigurasi bot:",
                color=0x0099ff
            )
            
            # Basic config
            basic_info = f"Guild ID: {config_data.get('guild_id')}\n"
            basic_info += f"Admin ID: {config_data.get('admin_id')}\n"
            basic_info += f"Token: {'***' if config_data.get('token') else 'Not set'}"
            
            embed.add_field(
                name="📋 Basic Config",
                value=basic_info,
                inline=False
            )
            
            # Roles
            roles = config_data.get('roles', {})
            if roles:
                roles_text = "\n".join([f"{name}: {role_id}" for name, role_id in roles.items()])
                embed.add_field(
                    name="👥 Roles",
                    value=roles_text,
                    inline=False
                )
            
            # Channels
            channels = config_data.get('channels', {})
            if channels:
                channels_text = "\n".join([f"{name}: {channel_id}" for name, channel_id in channels.items()])
                embed.add_field(
                    name="📺 Channels",
                    value=channels_text[:1024],  # Discord limit
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error config info: {e}")
            await ctx.send(f"❌ Error saat mengambil config: {e}")

async def setup(bot):
    """Setup debug cog"""
    try:
        await bot.add_cog(DebugCog(bot))
        logger.info("Debug cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load debug cog: {e}")
        raise
