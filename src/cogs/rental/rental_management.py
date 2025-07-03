"""
Rental Management Cog
Commands untuk mengelola subscription bot rental dari Discord
"""

import discord
from discord.ext import commands
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append('/home/user/workspace')
sys.path.append('/home/user/workspace/src')

from src.database.connection import DatabaseManager
from src.services.rental.subscription_service import SubscriptionService
from src.database.models.rental.subscription import SubscriptionPlan, SubscriptionStatus

class RentalManagementCog(commands.Cog):
    """Cog untuk mengelola subscription bot rental"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_manager = None
        self.subscription_service = None
        
    async def cog_load(self):
        """Initialize services saat cog dimuat"""
        try:
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            
            # Create subscription table if not exists
            create_table_query = """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT UNIQUE NOT NULL,
                    discord_id TEXT NOT NULL,
                    plan TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    auto_renew BOOLEAN DEFAULT TRUE,
                    bot_token TEXT,
                    guild_id TEXT,
                    features TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            await self.db_manager.execute_update(create_table_query)
            
            self.subscription_service = SubscriptionService(self.db_manager)
            print("✅ Rental Management Cog loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading Rental Management Cog: {e}")
    
    @commands.group(name='rental', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def rental(self, ctx):
        """Commands untuk mengelola bot rental"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="🤖 Bot Rental Management",
                description="Commands untuk mengelola subscription bot rental",
                color=0x667eea
            )
            embed.add_field(
                name="📋 Commands Available:",
                value="""
                `!rental create <discord_id> <plan> [days]` - Buat subscription baru
                `!rental status <discord_id>` - Cek status subscription
                `!rental extend <tenant_id> <days>` - Perpanjang subscription
                `!rental activate <tenant_id>` - Aktifkan subscription
                `!rental list` - Lihat semua subscription
                `!rental stats` - Lihat statistik
                """,
                inline=False
            )
            embed.add_field(
                name="📦 Available Plans:",
                value="• `basic` - $10/bulan\n• `premium` - $25/bulan\n• `enterprise` - $50/bulan",
                inline=False
            )
            await ctx.send(embed=embed)
    
    @rental.command(name='create')
    @commands.has_permissions(administrator=True)
    async def create_subscription(self, ctx, discord_id: str, plan: str, days: int = 30):
        """Buat subscription baru"""
        try:
            # Validasi plan
            valid_plans = ['basic', 'premium', 'enterprise']
            if plan.lower() not in valid_plans:
                await ctx.send(f"❌ Plan tidak valid. Pilih: {', '.join(valid_plans)}")
                return
            
            # Buat subscription
            response = await self.subscription_service.create_subscription(
                discord_id=discord_id,
                plan=plan.lower(),
                duration_days=days
            )
            
            if response.success:
                subscription = response.data
                embed = discord.Embed(
                    title="✅ Subscription Berhasil Dibuat",
                    color=0x00ff00
                )
                embed.add_field(name="Tenant ID", value=subscription['tenant_id'], inline=True)
                embed.add_field(name="Discord ID", value=subscription['discord_id'], inline=True)
                embed.add_field(name="Plan", value=subscription['plan'].upper(), inline=True)
                embed.add_field(name="Status", value=subscription['status'].upper(), inline=True)
                embed.add_field(name="Durasi", value=f"{days} hari", inline=True)
                embed.add_field(name="Berakhir", value=subscription['end_date'][:10], inline=True)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Gagal membuat subscription: {response.message}")
                
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
    
    @rental.command(name='status')
    async def check_status(self, ctx, discord_id: str):
        """Cek status subscription user"""
        try:
            response = await self.subscription_service.get_subscription_by_discord_id(discord_id)
            
            if response.success:
                subscription = response.data
                embed = discord.Embed(
                    title="📊 Status Subscription",
                    color=0x667eea
                )
                embed.add_field(name="Tenant ID", value=subscription['tenant_id'], inline=True)
                embed.add_field(name="Plan", value=subscription['plan'].upper(), inline=True)
                embed.add_field(name="Status", value=subscription['status'].upper(), inline=True)
                embed.add_field(name="Sisa Hari", value=f"{subscription['days_remaining']} hari", inline=True)
                embed.add_field(name="Auto Renew", value="✅" if subscription['auto_renew'] else "❌", inline=True)
                embed.add_field(name="Berakhir", value=subscription['end_date'][:10], inline=True)
                
                # Status color
                if subscription['is_active']:
                    embed.color = 0x00ff00
                elif subscription['status'] == 'expired':
                    embed.color = 0xff0000
                else:
                    embed.color = 0xffaa00
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ {response.message}")
                
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
    
    @rental.command(name='extend')
    @commands.has_permissions(administrator=True)
    async def extend_subscription(self, ctx, tenant_id: str, days: int):
        """Perpanjang subscription"""
        try:
            response = await self.subscription_service.extend_subscription(tenant_id, days)
            
            if response.success:
                embed = discord.Embed(
                    title="✅ Subscription Diperpanjang",
                    description=f"Subscription {tenant_id} berhasil diperpanjang {days} hari",
                    color=0x00ff00
                )
                embed.add_field(name="Berakhir Baru", value=response.data['new_end_date'][:10], inline=True)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Gagal perpanjang subscription: {response.message}")
                
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
    
    @rental.command(name='activate')
    @commands.has_permissions(administrator=True)
    async def activate_subscription(self, ctx, tenant_id: str):
        """Aktifkan subscription"""
        try:
            response = await self.subscription_service.update_subscription_status(
                tenant_id, SubscriptionStatus.ACTIVE.value
            )
            
            if response.success:
                embed = discord.Embed(
                    title="✅ Subscription Diaktifkan",
                    description=f"Subscription {tenant_id} berhasil diaktifkan",
                    color=0x00ff00
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Gagal aktifkan subscription: {response.message}")
                
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
    
    @rental.command(name='list')
    @commands.has_permissions(administrator=True)
    async def list_subscriptions(self, ctx):
        """Lihat semua subscription"""
        try:
            response = await self.subscription_service.get_all_subscriptions()
            
            if response.success and response.data:
                subscriptions = response.data[:10]  # Limit 10 untuk embed
                
                embed = discord.Embed(
                    title="📋 Daftar Subscription",
                    color=0x667eea
                )
                
                for sub in subscriptions:
                    status_emoji = "🟢" if sub['is_active'] else "🔴" if sub['status'] == 'expired' else "🟡"
                    embed.add_field(
                        name=f"{status_emoji} {sub['tenant_id'][:12]}...",
                        value=f"Plan: {sub['plan'].upper()}\nSisa: {sub['days_remaining']} hari\nDiscord: <@{sub['discord_id']}>",
                        inline=True
                    )
                
                if len(response.data) > 10:
                    embed.set_footer(text=f"Menampilkan 10 dari {len(response.data)} subscription")
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("📭 Tidak ada subscription yang ditemukan")
                
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
    
    @rental.command(name='stats')
    @commands.has_permissions(administrator=True)
    async def subscription_stats(self, ctx):
        """Lihat statistik subscription"""
        try:
            response = await self.subscription_service.get_subscription_stats()
            
            if response.success:
                stats = response.data
                embed = discord.Embed(
                    title="📊 Statistik Subscription",
                    color=0x667eea
                )
                embed.add_field(name="Total Subscription", value=stats['total'], inline=True)
                embed.add_field(name="Aktif", value=stats['active'], inline=True)
                embed.add_field(name="Revenue/Bulan", value=f"${stats['estimated_monthly_revenue']}", inline=True)
                
                # Plan breakdown
                plan_text = ""
                for plan, count in stats['by_plan'].items():
                    plan_text += f"• {plan.upper()}: {count}\n"
                
                if plan_text:
                    embed.add_field(name="Per Plan", value=plan_text, inline=False)
                
                embed.timestamp = datetime.utcnow()
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Gagal mengambil statistik: {response.message}")
                
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
    
    @rental.command(name='check-expired')
    @commands.has_permissions(administrator=True)
    async def check_expired(self, ctx):
        """Cek dan update subscription yang expired"""
        try:
            response = await self.subscription_service.check_expired_subscriptions()
            
            if response.success:
                expired_count = response.data['expired_count']
                embed = discord.Embed(
                    title="🔍 Pengecekan Subscription Expired",
                    description=f"Ditemukan {expired_count} subscription yang expired dan telah diupdate",
                    color=0xffaa00 if expired_count > 0 else 0x00ff00
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Gagal cek expired subscription: {response.message}")
                
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

async def setup(bot):
    """Setup function untuk load cog"""
    await bot.add_cog(RentalManagementCog(bot))
