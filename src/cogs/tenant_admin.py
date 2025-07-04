"""
Tenant Admin Cog untuk Dashboard Admin
Cog untuk konfigurasi fitur tenant melalui Discord commands
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
from src.services.tenant_service import TenantService
from src.services.tenant_config_service import TenantConfigService
from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

class TenantAdmin(commands.Cog):
    """Cog untuk administrasi tenant"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_manager = DatabaseManager()
        self.tenant_service = TenantService(self.db_manager)
        self.config_service = TenantConfigService(self.db_manager)
    
    @commands.group(name='tenant-admin', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def tenant_admin_group(self, ctx):
        """Grup command untuk administrasi tenant"""
        embed = discord.Embed(
            title="🏢 Tenant Administration",
            description="Kelola konfigurasi dan fitur tenant",
            color=discord.Color.blue()
        )
        commands_text = (
            "`!tenant-admin create <discord_id> <guild_id> <name> [plan]`\n"
            "`!tenant-admin features <tenant_id> <feature> <enable/disable>`\n"
            "`!tenant-admin channels <tenant_id> <channel_type> <channel_id>`\n"
            "`!tenant-admin permissions <tenant_id> <permission> <true/false>`\n"
            "`!tenant-admin config <tenant_id>`\n"
            "`!tenant-admin sync <tenant_id>`"
        )
        embed.add_field(name="Commands", value=commands_text, inline=False)
        await ctx.send(embed=embed)
    
    @tenant_admin_group.command(name='create')
    @commands.has_permissions(administrator=True)
    async def create_tenant(self, ctx, discord_id: str, guild_id: str, name: str, plan: str = "basic"):
        """Buat tenant baru"""
        try:
            response = await self.tenant_service.create_tenant(discord_id, guild_id, name, plan)
            
            if response.success:
                embed = discord.Embed(
                    title="✅ Tenant Created",
                    description="Tenant berhasil dibuat",
                    color=discord.Color.green()
                )
                embed.add_field(name="Tenant ID", value=response.data['tenant_id'], inline=True)
                embed.add_field(name="Discord ID", value=discord_id, inline=True)
                embed.add_field(name="Plan", value=plan.upper(), inline=True)
                embed.add_field(name="Status", value=response.data['status'], inline=True)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Gagal membuat tenant: {response.message}",
                    color=discord.Color.red()
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error creating tenant: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Terjadi error: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @tenant_admin_group.command(name='features')
    @commands.has_permissions(administrator=True)
    async def update_features(self, ctx, tenant_id: str, feature: str, action: str):
        """Update fitur tenant (enable/disable)"""
        try:
            enable = action.lower() in ['enable', 'true', '1', 'on']
            features = {feature: enable}
            
            response = await self.tenant_service.update_tenant_features(tenant_id, features)
            
            if response.success:
                status = "diaktifkan" if enable else "dinonaktifkan"
                embed = discord.Embed(
                    title="✅ Feature Updated",
                    description=f"Fitur {feature} berhasil {status}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Tenant ID", value=tenant_id, inline=True)
                embed.add_field(name="Feature", value=feature, inline=True)
                embed.add_field(name="Status", value="Enabled" if enable else "Disabled", inline=True)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Gagal update fitur: {response.message}",
                    color=discord.Color.red()
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error updating features: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Terjadi error: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function untuk load cog"""
    await bot.add_cog(TenantAdmin(bot))
