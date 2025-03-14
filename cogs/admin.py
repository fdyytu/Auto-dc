"""
Admin Commands Cog
Author: fdyytu
Created at: 2025-03-12 14:08:55 UTC
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime
import json
import asyncio
from typing import Optional, List, Dict, Any
import io
import os
import psutil
import platform

from ext.constants import (
    Status,              
    TransactionType,     
    Balance,            
    COLORS,             
    MESSAGES,           
    CURRENCY_RATES,     
    MAX_STOCK_FILE_SIZE,
    VALID_STOCK_FORMATS,
    Permissions 
)
from ext.admin_service import AdminService
from ext.balance_manager import BalanceManagerService
from ext.product_manager import ProductManagerService
from ext.trx import TransactionManager
from ext.database import get_connection
from ext.cache_manager import CacheManager
from ext.base_handler import BaseLockHandler, BaseResponseHandler

class AdminCog(commands.Cog, BaseLockHandler, BaseResponseHandler):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.logger = logging.getLogger("AdminCog")
        self.PREFIX = "!"
        
        # Initialize services
        self.balance_service = BalanceManagerService(bot)
        self.product_service = ProductManagerService(bot)
        self.trx_manager = TransactionManager(bot)
        self.admin_service = AdminService(bot)
        self.cache_manager = CacheManager()
        
        # Load admin configuration
        try:
            with open('config.json') as f:
                config = json.load(f)
                self.admin_id = int(config.get('admin_id'))
                self.PREFIX = config.get('prefix', '!')
                if not self.admin_id:
                    raise ValueError("admin_id not found in config.json")
                self.logger.info(f"Admin ID loaded: {self.admin_id}")
        except Exception as e:
            self.logger.critical(f"Failed to load admin configuration: {e}")
            raise

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Check if user has admin permission"""
        return await self.admin_service.check_permission(ctx.author.id, Permissions.ADMIN)

    # Product Management Commands
    @commands.command(name="addproduct")
    async def add_product(self, ctx, code: str, name: str, price: int, *, description: str = None):
        """Add new product"""
        async def execute():
            response = await self.product_service.add_product(
                code=code.upper(),
                name=name,
                price=price,
                description=description,
                added_by=str(ctx.author)
            )
            
            if not response.success:
                raise ValueError(response.error)
                
            embed = discord.Embed(
                title="✅ Product Added",
                color=COLORS.SUCCESS,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Details",
                value=(
                    f"```yml\n"
                    f"Code: {code.upper()}\n"
                    f"Name: {name}\n"
                    f"Price: {price:,} WLS\n"
                    f"Description: {description or 'N/A'}\n"
                    f"```"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Added by {ctx.author}")
            await self.send_response_once(ctx, embed=embed)
            
        await self._process_command(ctx, "addproduct", execute)

    @commands.command(name="editproduct")
    async def edit_product(self, ctx, code: str, field: str, *, value: str):
        """Edit product details"""
        async def execute():
            valid_fields = ['name', 'price', 'description']
            field = field.lower()
            
            if field not in valid_fields:
                raise ValueError(f"Invalid field. Use: {', '.join(valid_fields)}")
                
            if field == 'price':
                try:
                    value = int(value)
                except ValueError:
                    raise ValueError("Price must be a number")
                    
            response = await self.product_service.update_product(
                code=code.upper(),
                field=field,
                value=value,
                updated_by=str(ctx.author)
            )
            
            if not response.success:
                raise ValueError(response.error)
                
            embed = discord.Embed(
                title="✅ Product Updated",
                color=COLORS.SUCCESS,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Details",
                value=(
                    f"```yml\n"
                    f"Code: {code.upper()}\n"
                    f"Updated Field: {field}\n"
                    f"New Value: {value}\n"
                    f"```"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Updated by {ctx.author}")
            await self.send_response_once(ctx, embed=embed)
            
        await self._process_command(ctx, "editproduct", execute)

    @commands.command(name="deleteproduct")
    async def delete_product(self, ctx, code: str):
        """Delete product"""
        async def execute():
            if not await self._confirm_action(
                ctx,
                f"Are you sure you want to delete product {code.upper()}?"
            ):
                raise ValueError("Operation cancelled by user")
                
            response = await self.product_service.delete_product(
                code=code.upper(),
                deleted_by=str(ctx.author)
            )
            
            if not response.success:
                raise ValueError(response.error)
                
            embed = discord.Embed(
                title="✅ Product Deleted",
                description=f"Product {code.upper()} has been deleted",
                color=COLORS.SUCCESS,
                timestamp=datetime.utcnow()
            )
            
            embed.set_footer(text=f"Deleted by {ctx.author}")
            await self.send_response_once(ctx, embed=embed)
            
        await self._process_command(ctx, "deleteproduct", execute)

    @commands.command(name="addstock")
    async def add_stock(self, ctx, code: str):
        """Add stock with file attachment"""
        async def execute():
            if not ctx.message.attachments:
                raise ValueError("Please attach a file containing stock items")
                
            attachment = ctx.message.attachments[0]
            if attachment.size > MAX_STOCK_FILE_SIZE:
                raise ValueError(f"File too large. Maximum size: {MAX_STOCK_FILE_SIZE/1024/1024}MB")
                
            if not any(attachment.filename.endswith(ext) for ext in VALID_STOCK_FORMATS):
                raise ValueError(f"Invalid file format. Use: {', '.join(VALID_STOCK_FORMATS)}")
                
            content = await attachment.read()
            content = content.decode('utf-8').strip().split('\n')
            
            response = await self.product_service.add_stock(
                code=code.upper(),
                items=content,
                added_by=str(ctx.author)
            )
            
            if not response.success:
                raise ValueError(response.error)
                
            embed = discord.Embed(
                title="✅ Stock Added",
                color=COLORS.SUCCESS,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Details",
                value=(
                    f"```yml\n"
                    f"Product: {code.upper()}\n"
                    f"Added Items: {len(content)}\n"
                    f"Total Stock: {response.data['total_stock']}\n"
                    f"```"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Added by {ctx.author}")
            await self.send_response_once(ctx, embed=embed)
            
        await self._process_command(ctx, "addstock", execute)

    @commands.command(name="addworld")
    async def add_world(self, ctx, name: str, *, description: str = None):
        """Add world information"""
        async def execute():
            response = await self.product_service.add_world(
                name=name.upper(),
                description=description,
                added_by=str(ctx.author)
            )
            
            if not response.success:
                raise ValueError(response.error)
                
            embed = discord.Embed(
                title="✅ World Added",
                color=COLORS.SUCCESS,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Details",
                value=(
                    f"```yml\n"
                    f"World: {name.upper()}\n"
                    f"Description: {description or 'N/A'}\n"
                    f"```"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Added by {ctx.author}")
            await self.send_response_once(ctx, embed=embed)
            
        await self._process_command(ctx, "addworld", execute)

    # Balance Management Commands
    @commands.command(name="addbal")
    async def add_balance(self, ctx, growid: str, amount: int, currency: str):
        """Add balance to user"""
        async def execute():
            currency = currency.upper()
            if currency not in CURRENCY_RATES:
                raise ValueError(f"Invalid currency. Use: {', '.join(CURRENCY_RATES.keys())}")

            if amount <= 0:
                raise ValueError("Amount must be positive!")

            # Convert to WLS based on currency
            wls = amount if currency == "WL" else amount * CURRENCY_RATES[currency]

            response = await self.balance_service.update_balance(
                growid=growid,
                wl=wls,
                details=f"Added by admin {ctx.author}",
                transaction_type=TransactionType.ADMIN_ADD
            )

            if not response.success:
                raise ValueError(response.error)

            embed = discord.Embed(
                title="✅ Balance Added",
                color=COLORS.SUCCESS,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="💰 Balance Details",
                value=(
                    f"```yml\n"
                    f"GrowID: {growid}\n"
                    f"Added: {amount:,} {currency}\n"
                    f"New Balance: {response.data.format()}\n"
                    f"```"
                ),
                inline=False
            )
            embed.set_footer(text=f"Added by {ctx.author}")

            await self.send_response_once(ctx, embed=embed)

        await self._process_command(ctx, "addbal", execute)

    @commands.command(name="removebal")
    async def remove_balance(self, ctx, growid: str, amount: int, currency: str):
        """Remove balance from user"""
        async def execute():
            currency = currency.upper()
            if currency not in CURRENCY_RATES:
                raise ValueError(f"Invalid currency. Use: {', '.join(CURRENCY_RATES.keys())}")

            if amount <= 0:
                raise ValueError("Amount must be positive!")

            # Convert to negative WLS based on currency
            wls = -(amount if currency == "WL" else amount * CURRENCY_RATES[currency])

            response = await self.balance_service.update_balance(
                growid=growid,
                wl=wls,
                details=f"Removed by admin {ctx.author}",
                transaction_type=TransactionType.ADMIN_REMOVE
            )

            if not response.success:
                raise ValueError(response.error)

            embed = discord.Embed(
                title="✅ Balance Removed",
                color=COLORS.SUCCESS,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="💰 Balance Details",
                value=(
                    f"```yml\n"
                    f"GrowID: {growid}\n"
                    f"Removed: {amount:,} {currency}\n"
                    f"New Balance: {response.data.format()}\n"
                    f"```"
                ),
                inline=False
            )
            embed.set_footer(text=f"Removed by {ctx.author}")

            await self.send_response_once(ctx, embed=embed)

        await self._process_command(ctx, "removebal", execute)

    @commands.command(name="checkbal")
    async def check_balance(self, ctx, growid: str):
        """Check user balance"""
        async def execute():
            balance_response = await self.balance_service.get_balance(growid)
            if not balance_response.success:
                raise ValueError(balance_response.error)

            # Get transaction history
            trx_response = await self.trx_manager.get_transaction_history(growid, limit=5)

            embed = discord.Embed(
                title=f"👤 User Information - {growid}",
                color=COLORS.INFO,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="💰 Current Balance",
                value=f"```yml\n{balance_response.data.format()}\n```",
                inline=False
            )

            if trx_response.success and trx_response.data:
                recent_tx = "\n".join([
                    f"• {tx['type']} - {tx['timestamp']}: {tx['details']}"
                    for tx in trx_response.data[:5]
                ])
                embed.add_field(
                    name="📝 Recent Transactions",
                    value=f"```yml\n{recent_tx}\n```",
                    inline=False
                )

            embed.set_footer(text=f"Checked by {ctx.author}")
            await self.send_response_once(ctx, embed=embed)

        await self._process_command(ctx, "checkbal", execute)

    @commands.command(name="resetuser")
    async def reset_user(self, ctx, growid: str):
        """Reset user balance"""
        async def execute():
            if not await self._confirm_action(
                ctx, 
                f"Are you sure you want to reset {growid}'s balance? This action cannot be undone."
            ):
                raise ValueError("Operation cancelled by user")

            current_balance = await self.balance_service.get_balance(growid)
            if not current_balance.success:
                raise ValueError(current_balance.error)

            # Reset balance
            response = await self.balance_service.update_balance(
                growid=growid,
                wl=-current_balance.data.wl,
                dl=-current_balance.data.dl,
                bgl=-current_balance.data.bgl,
                details=f"Balance reset by admin {ctx.author}",
                transaction_type=TransactionType.ADMIN_RESET
            )

            if not response.success:
                raise ValueError(response.error)

            embed = discord.Embed(
                title="✅ Balance Reset",
                color=COLORS.ERROR,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Previous Balance",
                value=f"```yml\n{current_balance.data.format()}\n```",
                inline=False
            )
            
            embed.add_field(
                name="New Balance",
                value=f"```yml\n{response.data.format()}\n```",
                inline=False
            )
            
            embed.set_footer(text=f"Reset by {ctx.author}")
            await self.send_response_once(ctx, embed=embed)

        await self._process_command(ctx, "resetuser", execute)

    # Transaction Management Commands
    @commands.command(name="trxhistory")
    async def transaction_history(self, ctx, growid: str, limit: int = 10):
        """View transaction history"""
        async def execute():
            if limit < 1 or limit > 50:
                raise ValueError("Limit must be between 1 and 50")

            trx_response = await self.trx_manager.get_transaction_history(
                growid=growid,
                limit=limit
            )

            if not trx_response.success:
                raise ValueError(trx_response.error)

            transactions = trx_response.data
            if not transactions:
                raise ValueError("No transactions found")

            embed = discord.Embed(
                title=f"📜 Transaction History - {growid}",
                color=COLORS.INFO,
                timestamp=datetime.utcnow()
            )

            for tx in transactions:
                embed.add_field(
                    name=f"{tx['type']} - {tx['timestamp']}",
                    value=(
                        f"```yml\n"
                        f"Amount: {tx['amount_display']}\n"
                        f"Details: {tx.get('details', 'No details')}\n"
                        f"```"
                    ),
                    inline=False
                )

            embed.set_footer(text=f"Showing {len(transactions)} transactions")
            await self.send_response_once(ctx, embed=embed)

        await self._process_command(ctx, "trxhistory", execute)

    @commands.command(name="stockhistory")
    async def stock_history(self, ctx, code: str, limit: int = 10):
        """View stock history"""
        async def execute():
            if limit < 1 or limit > 50:
                raise ValueError("Limit must be between 1 and 50")

            response = await self.product_service.get_stock_history(
                code=code.upper(),
                limit=limit
            )

            if not response.success:
                raise ValueError(response.error)

            history = response.data
            if not history:
                raise ValueError("No stock history found")

            embed = discord.Embed(
                title=f"📦 Stock History - {code.upper()}",
                color=COLORS.INFO,
                timestamp=datetime.utcnow()
            )

            for entry in history:
                embed.add_field(
                    name=f"{entry['action']} - {entry['timestamp']}",
                    value=(
                        f"```yml\n"
                        f"Amount: {entry['amount']}\n"
                        f"By: {entry['by']}\n"
                        f"Details: {entry.get('details', 'No details')}\n"
                        f"```"
                    ),
                    inline=False
                )

            embed.set_footer(text=f"Showing {len(history)} entries")
            await self.send_response_once(ctx, embed=embed)

        await self._process_command(ctx, "stockhistory", execute)

    # System Management Commands
    @commands.command(name="systeminfo")
    async def system_info(self, ctx):
        """Show bot system information"""
        async def execute():
            # Get system info
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get bot info
            uptime = datetime.utcnow() - self.bot.startup_time
            
            embed = discord.Embed(
                title="🤖 System Information",
                color=COLORS.INFO,
                timestamp=datetime.utcnow()
            )
            
            # System Stats
            embed.add_field(
                name="💻 System Resources",
                value=(
                    f"```yml\n"
                    f"OS: {platform.system()} {platform.release()}\n"
                    f"CPU Usage: {cpu_usage}%\n"
                    f"Memory: {memory.used/1024/1024/1024:.1f}GB/{memory.total/1024/1024/1024:.1f}GB ({memory.percent}%)\n"
                    f"Disk: {disk.used/1024/1024/1024:.1f}GB/{disk.total/1024/1024/1024:.1f}GB ({disk.percent}%)\n"
                    f"Python: {platform.python_version()}\n"
                    f"```"
                ),
                inline=False
            )
            
            # Bot Stats
            embed.add_field(
                name="🤖 Bot Status",
                value=(
                    f"```yml\n"
                    f"Uptime: {str(uptime).split('.')[0]}\n"
                    f"Latency: {round(self.bot.latency * 1000)}ms\n"
                    f"Servers: {len(self.bot.guilds)}\n"
                    f"Commands: {len(self.bot.commands)}\n"
                    f"```"
                ),
                inline=False
            )
            
            # Cache Stats
            cache_stats = await self.cache_manager.get_stats()
            embed.add_field(
                name="📊 Cache Statistics",
                value=(
                    f"```yml\n"
                    f"Items: {cache_stats.get('items', 0)}\n"
                    f"Hit Rate: {cache_stats.get('hit_rate', 0):.1f}%\n"
                    f"Memory Usage: {cache_stats.get('memory_usage', 0):.1f}MB\n"
                    f"```"
                ),
                inline=False
            )
            
            await self.send_response_once(ctx, embed=embed)

        await self._process_command(ctx, "systeminfo", execute)

    @commands.command(name="maintenance")
    async def maintenance(self, ctx, mode: str):
        """Toggle maintenance mode"""
        async def execute():
            mode_lower = mode.lower()
            if mode_lower not in ['on', 'off']:
                raise ValueError("Please specify 'on' or 'off'")

            enabled = mode_lower == 'on'
            if enabled and not await self._confirm_action(
                ctx,
                "Are you sure you want to enable maintenance mode? This will restrict user access."
            ):
                raise ValueError("Operation cancelled by user")

            response = await self.admin_service.set_maintenance_mode(
                enabled=enabled,
                reason="System maintenance" if enabled else None,
                admin=str(ctx.author)
            )

            if not response.success:
                raise ValueError(response.error)

            embed = discord.Embed(
                title="🔧 Maintenance Mode",
                description=f"Maintenance mode has been turned **{mode_lower.upper()}**",
                color=COLORS.WARNING if enabled else COLORS.SUCCESS,
                timestamp=datetime.utcnow()
            )
            
            embed.set_footer(text=f"Changed by {ctx.author}")
            await self.send_response_once(ctx, embed=embed)

            if enabled:
                # Notify online users
                for guild in self.bot.guilds:
                    for member in guild.members:
                        if not member.bot and member.status != discord.Status.offline:
                            try:
                                await member.send(
                                    embed=discord.Embed(
                                        title="⚠️ Maintenance Mode",
                                        description=(
                                            "The bot is entering maintenance mode. "
                                            "Some features may be unavailable. "
                                            "We'll notify you when service is restored."
                                        ),
                                        color=COLORS.WARNING
                                    )
                                )
                            except Exception as e:
                                self.logger.error(f"Failed to notify member {member.id}: {e}")

        await self._process_command(ctx, "maintenance", execute)

    @commands.command(name="blacklist")
    async def blacklist(self, ctx, action: str, growid: str):
        """Manage blacklisted users"""
        async def execute():
            action_lower = action.lower()
            if action_lower not in ['add', 'remove']:
                raise ValueError("Please specify 'add' or 'remove'")

            if action_lower == 'add':
                if not await self._confirm_action(
                    ctx,
                    f"Are you sure you want to blacklist {growid}?"
                ):
                    raise ValueError("Operation cancelled by user")

                response = await self.admin_service.add_to_blacklist(
                    growid=growid,
                    added_by=str(ctx.author)
                )
            else:
                response = await self.admin_service.remove_from_blacklist(
                    growid=growid,
                    removed_by=str(ctx.author)
                )

            if not response.success:
                raise ValueError(response.error)

            embed = discord.Embed(
                title="⛔ Blacklist Updated",
                description=(
                    f"User {growid} has been "
                    f"{'added to' if action_lower == 'add' else 'removed from'} "
                    f"the blacklist."
                ),
                color=COLORS.ERROR if action_lower == 'add' else COLORS.SUCCESS,
                timestamp=datetime.utcnow()
            )
            
            embed.set_footer(text=f"Updated by {ctx.author}")
            await self.send_response_once(ctx, embed=embed)

        await self._process_command(ctx, "blacklist", execute)

    # Helper Methods
    async def _confirm_action(self, ctx: commands.Context, message: str) -> bool:
        """Ask for confirmation before proceeding with action"""
        embed = discord.Embed(
            title="⚠️ Confirmation Required",
            description=message,
            color=COLORS.WARNING
        )
        embed.set_footer(text="Reply with 'yes' to confirm or 'no' to cancel")
        
        confirm_msg = await ctx.send(embed=embed)
        
        try:
            response = await self.bot.wait_for(
                'message',
                check=lambda m: (
                    m.author == ctx.author and
                    m.channel == ctx.channel and
                    m.content.lower() in ['yes', 'no']
                ),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            await confirm_msg.delete()
            raise ValueError("Confirmation timed out")
            
        await confirm_msg.delete()
        return response.content.lower() == 'yes'

async def setup(bot):
    """Setup the Admin cog"""
    try:
        await bot.add_cog(AdminCog(bot))
        logging.info(
            f'Admin cog loaded successfully at {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC'
        )
    except Exception as e:
        logging.error(f"Failed to load Admin cog: {e}")
        raise