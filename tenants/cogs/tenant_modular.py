"""
Tenant Modular Cog System
Sistem cogs modular yang dapat di-enable/disable per tenant
"""

import discord
from discord.ext import commands
import logging
from typing import Dict, List, Optional
from tenants.services.tenant_service import TenantService
from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

class TenantModular(commands.Cog):
    """Cog untuk sistem modular per tenant"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_manager = DatabaseManager()
        self.tenant_service = TenantService(self.db_manager)
        self.tenant_cogs = {}  # Cache untuk cogs per tenant
    
    async def load_tenant_cogs(self, tenant_id: str) -> bool:
        """Load cogs berdasarkan konfigurasi tenant"""
        try:
            # Ambil konfigurasi tenant
            response = await self.tenant_service.get_tenant_config(tenant_id)
            if not response.success:
                logger.error(f"Gagal mengambil config tenant {tenant_id}")
                return False
            
            tenant_config = response.data
            features = tenant_config.get('features', {})
            
            # Mapping fitur ke cogs
            feature_cog_mapping = {
                'shop': ['live_stock', 'admin_store'],
                'leveling': ['leveling'],
                'reputation': ['reputation'],
                'tickets': ['ticket.ticket_cog'],
                'automod': ['automod'],
                'admin_commands': ['admin', 'admin_system']
            }
            
            # Load cogs berdasarkan fitur yang aktif
            loaded_cogs = []
            for feature, enabled in features.items():
                if enabled and feature in feature_cog_mapping:
                    for cog_name in feature_cog_mapping[feature]:
                        try:
                            if cog_name not in self.bot.extensions:
                                await self.bot.load_extension(f'src.cogs.{cog_name}')
                                loaded_cogs.append(cog_name)
                                logger.info(f"Loaded cog {cog_name} for tenant {tenant_id}")
                        except Exception as e:
                            logger.error(f"Gagal load cog {cog_name}: {e}")
            
            # Cache loaded cogs untuk tenant
            self.tenant_cogs[tenant_id] = loaded_cogs
            return True
            
        except Exception as e:
            logger.error(f"Error loading tenant cogs: {e}")
            return False
    
    async def unload_tenant_cogs(self, tenant_id: str) -> bool:
        """Unload cogs untuk tenant"""
        try:
            if tenant_id not in self.tenant_cogs:
                return True
            
            loaded_cogs = self.tenant_cogs[tenant_id]
            for cog_name in loaded_cogs:
                try:
                    if cog_name in self.bot.extensions:
                        await self.bot.unload_extension(f'src.cogs.{cog_name}')
                        logger.info(f"Unloaded cog {cog_name} for tenant {tenant_id}")
                except Exception as e:
                    logger.error(f"Gagal unload cog {cog_name}: {e}")
            
            # Clear cache
            del self.tenant_cogs[tenant_id]
            return True
            
        except Exception as e:
            logger.error(f"Error unloading tenant cogs: {e}")
            return False
    
    async def reload_tenant_cogs(self, tenant_id: str) -> bool:
        """Reload cogs untuk tenant"""
        try:
            # Unload dulu
            await self.unload_tenant_cogs(tenant_id)
            
            # Load ulang
            return await self.load_tenant_cogs(tenant_id)
            
        except Exception as e:
            logger.error(f"Error reloading tenant cogs: {e}")
            return False
    
    @commands.command(name='reload-tenant')
    @commands.has_permissions(administrator=True)
    async def reload_tenant_command(self, ctx, tenant_id: str):
        """Command untuk reload cogs tenant"""
        try:
            success = await self.reload_tenant_cogs(tenant_id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Tenant Cogs Reloaded",
                    description=f"Cogs untuk tenant {tenant_id} berhasil direload",
                    color=discord.Color.green()
                )
                
                # Tampilkan loaded cogs
                if tenant_id in self.tenant_cogs:
                    loaded_cogs = self.tenant_cogs[tenant_id]
                    embed.add_field(
                        name="Loaded Cogs",
                        value="\n".join(loaded_cogs) if loaded_cogs else "None",
                        inline=False
                    )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Gagal reload cogs untuk tenant {tenant_id}",
                    color=discord.Color.red()
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in reload tenant command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Terjadi error: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function untuk load cog"""
    await bot.add_cog(TenantModular(bot))
