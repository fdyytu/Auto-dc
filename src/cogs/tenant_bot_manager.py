"""
Tenant Bot Manager Cog
Cog untuk mengelola bot instances per tenant dari Discord bot utama
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
from src.services.bot_management_service import BotManagementService
from src.services.rental.subscription_service import SubscriptionService
from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

class TenantBotManager(commands.Cog):
    """Cog untuk mengelola bot instances per tenant"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_manager = DatabaseManager()
        self.bot_service = BotManagementService(self.db_manager)
        self.subscription_service = SubscriptionService(self.db_manager)
    
    @commands.group(name='tenant', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def tenant_group(self, ctx):
        """Grup command untuk manajemen tenant bot"""
        embed = discord.Embed(
            title="🤖 Tenant Bot Management",
            description="Kelola bot instances untuk setiap tenant",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Commands",
            value="`!tenant create <discord_id> <bot_token> <guild_id>`\n"
                  "`!tenant start <tenant_id>`\n"
                  "`!tenant stop <tenant_id>`\n"
                  "`!tenant status <tenant_id>`\n"
                  "`!tenant list`",
            inline=False
        )
        await ctx.send(embed=embed)
    
    @tenant_group.command(name='create')
    @commands.has_permissions(administrator=True)
    async def create_bot_instance(self, ctx, discord_id: str, bot_token: str, guild_id: str):
        """Buat bot instance baru untuk tenant"""
        try:
            # Cek apakah user memiliki subscription aktif
            sub_response = await self.subscription_service.get_subscription_by_discord_id(discord_id)
            if not sub_response.success:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"User {discord_id} tidak memiliki subscription aktif",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            subscription = sub_response.data
            tenant_id = subscription['tenant_id']
            
            # Buat bot instance
            response = await self.bot_service.create_bot_instance(tenant_id, bot_token, guild_id)
            
            if response.success:
                embed = discord.Embed(
                    title="✅ Bot Instance Created",
                    description=f"Bot instance berhasil dibuat untuk tenant {tenant_id}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Discord ID", value=discord_id, inline=True)
                embed.add_field(name="Tenant ID", value=tenant_id, inline=True)
                embed.add_field(name="Guild ID", value=guild_id, inline=True)
                embed.add_field(name="Port", value=response.data['port'], inline=True)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Gagal membuat bot instance: {response.message}",
                    color=discord.Color.red()
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error creating bot instance: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Terjadi error: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @tenant_group.command(name='start')
    @commands.has_permissions(administrator=True)
    async def start_bot_instance(self, ctx, tenant_id: str):
        """Start bot instance untuk tenant"""
        try:
            response = await self.bot_service.start_bot_instance(tenant_id)
            
            if response.success:
                embed = discord.Embed(
                    title="✅ Bot Started",
                    description=f"Bot instance untuk tenant {tenant_id} berhasil distart",
                    color=discord.Color.green()
                )
                embed.add_field(name="Process ID", value=response.data['process_id'], inline=True)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Gagal start bot: {response.message}",
                    color=discord.Color.red()
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error starting bot instance: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Terjadi error: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @tenant_group.command(name='stop')
    @commands.has_permissions(administrator=True)
    async def stop_bot_instance(self, ctx, tenant_id: str):
        """Stop bot instance untuk tenant"""
        try:
            response = await self.bot_service.stop_bot_instance(tenant_id)
            
            if response.success:
                embed = discord.Embed(
                    title="✅ Bot Stopped",
                    description=f"Bot instance untuk tenant {tenant_id} berhasil dihentikan",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Gagal stop bot: {response.message}",
                    color=discord.Color.red()
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error stopping bot instance: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Terjadi error: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @tenant_group.command(name='status')
    @commands.has_permissions(administrator=True)
    async def instance_status(self, ctx, tenant_id: str):
        """Cek status bot instance untuk tenant"""
        try:
            response = await self.bot_service.get_bot_instance_by_tenant(tenant_id)
            
            if response.success:
                bot_data = response.data
                
                status_color = {
                    'running': discord.Color.green(),
                    'stopped': discord.Color.red(),
                    'starting': discord.Color.yellow(),
                    'error': discord.Color.dark_red(),
                    'maintenance': discord.Color.orange()
                }.get(bot_data['status'], discord.Color.grey())
                
                embed = discord.Embed(
                    title=f"🤖 Bot Status - {tenant_id}",
                    color=status_color
                )
                embed.add_field(name="Status", value=bot_data['status'].upper(), inline=True)
                embed.add_field(name="Guild ID", value=bot_data['guild_id'], inline=True)
                embed.add_field(name="Port", value=bot_data['port'], inline=True)
                embed.add_field(name="Process ID", value=bot_data['process_id'] or "N/A", inline=True)
                embed.add_field(name="Restart Count", value=bot_data['restart_count'], inline=True)
                
                if bot_data['last_heartbeat']:
                    embed.add_field(name="Last Heartbeat", value=bot_data['last_heartbeat'], inline=True)
                
                if bot_data['error_message']:
                    embed.add_field(name="Error", value=bot_data['error_message'], inline=False)
                
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Bot instance tidak ditemukan: {response.message}",
                    color=discord.Color.red()
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Terjadi error: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function untuk load cog"""
    await bot.add_cog(TenantBotManager(bot))
