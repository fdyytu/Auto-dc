"""
Refactored Reputation Cog
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import discord
from discord.ext import commands, tasks
import logging
from typing import Optional

from business.reputation.reputation_service import ReputationService
from business.reputation.role_handler import ReputationRoleHandler
from config.constants import COLORS
from cogs.utils import Embed

logger = logging.getLogger(__name__)

class Reputation(commands.Cog):
    """⭐ Advanced Reputation System"""
    
    def __init__(self, bot):
        self.bot = bot
        self.reputation_service = ReputationService()
        self.role_handler = ReputationRoleHandler()
        self.cleanup_task.start()

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.cleanup_task.cancel()

    @tasks.loop(minutes=10)
    async def cleanup_task(self):
        """Periodic cleanup of cooldowns"""
        try:
            self.reputation_service.cleanup_cooldowns()
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")

    @cleanup_task.before_loop
    async def before_cleanup_task(self):
        """Wait until bot is ready"""
        await self.bot.wait_until_ready()

    @commands.group(name='rep', aliases=['reputation'], invoke_without_command=True)
    async def reputation_group(self, ctx, member: Optional[discord.Member] = None):
        """Show reputation information for a user"""
        target = member or ctx.author
        
        try:
            stats_response = self.reputation_service.get_user_stats(ctx.guild.id, target.id)
            
            if not stats_response['success']:
                await ctx.send(f"❌ Error: {stats_response['error']}")
                return
            
            stats = stats_response['data']
            
            embed = Embed(
                title=f"⭐ Reputation Stats - {target.display_name}",
                color=COLORS.INFO
            )
            
            embed.add_field(
                name="Reputation", 
                value=f"**{stats['reputation']}**", 
                inline=True
            )
            embed.add_field(
                name="Rank", 
                value=f"**#{stats['rank']}**" if stats['rank'] else "**N/A**", 
                inline=True
            )
            embed.add_field(
                name="Given", 
                value=f"**{stats['total_given']}**", 
                inline=True
            )
            embed.add_field(
                name="Received", 
                value=f"**{stats['total_received']}**", 
                inline=True
            )
            
            # Add last activity info
            if stats['last_given']:
                embed.add_field(
                    name="Last Given",
                    value=f"<t:{int(stats['last_given'].timestamp())}:R>",
                    inline=True
                )
            
            if stats['last_received']:
                embed.add_field(
                    name="Last Received", 
                    value=f"<t:{int(stats['last_received'].timestamp())}:R>",
                    inline=True
                )
            
            embed.set_thumbnail(url=target.display_avatar.url)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in reputation command: {e}")
            await ctx.send("❌ An error occurred while fetching reputation information.")

    @reputation_group.command(name='give', aliases=['add', '+'])
    async def give_reputation(self, ctx, member: discord.Member, *, reason: str = None):
        """Give reputation to a user"""
        try:
            giver_roles = [role.id for role in ctx.author.roles]
            receiver_roles = [role.id for role in member.roles]
            
            # Check if user can give reputation
            can_give = self.reputation_service.can_give_reputation(
                ctx.guild.id, ctx.author.id, member.id, giver_roles, receiver_roles
            )
            
            if not can_give['success']:
                await ctx.send(f"❌ {can_give['error']}")
                return
            
            # Give reputation
            result = self.reputation_service.give_reputation(
                ctx.guild.id, ctx.author.id, member.id, 1, reason, ctx.message.id
            )
            
            if result['success']:
                embed = Embed(
                    title="⭐ Reputation Given!",
                    description=f"{ctx.author.mention} gave reputation to {member.mention}",
                    color=COLORS.SUCCESS
                )
                
                embed.add_field(
                    name="New Reputation",
                    value=f"**{result['new_reputation']}**",
                    inline=True
                )
                
                if reason:
                    embed.add_field(
                        name="Reason",
                        value=reason,
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
                # Handle role updates
                await self.role_handler.process_reputation_change(member, result['new_reputation'])
                
            else:
                await ctx.send(f"❌ {result['error']}")
                
        except Exception as e:
            logger.error(f"Error giving reputation: {e}")
            await ctx.send("❌ An error occurred while giving reputation.")

    @reputation_group.command(name='leaderboard', aliases=['lb', 'top'])
    async def reputation_leaderboard(self, ctx, limit: int = 10):
        """Show reputation leaderboard"""
        if limit > 25:
            limit = 25
        elif limit < 1:
            limit = 10
            
        try:
            lb_response = self.reputation_service.get_leaderboard(ctx.guild.id, limit)
            
            if not lb_response['success']:
                await ctx.send(f"❌ Error: {lb_response['error']}")
                return
            
            leaderboard = lb_response['data']
            
            if not leaderboard:
                await ctx.send("⭐ No reputation data found for this server.")
                return
            
            embed = Embed(
                title=f"🏆 Reputation Leaderboard - Top {len(leaderboard)}",
                color=COLORS.INFO
            )
            
            description_lines = []
            for i, user_data in enumerate(leaderboard, 1):
                user = self.bot.get_user(int(user_data['user_id']))
                username = user.display_name if user else f"User {user_data['user_id']}"
                
                # Medal emojis for top 3
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = f"**{i}.**"
                
                description_lines.append(
                    f"{medal} {username} - {user_data['reputation']} reputation"
                )
            
            embed.description = "\n".join(description_lines)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in reputation leaderboard: {e}")
            await ctx.send("❌ An error occurred while fetching the leaderboard.")

    @reputation_group.command(name='history')
    async def reputation_history(self, ctx, member: Optional[discord.Member] = None, limit: int = 5):
        """Show reputation history"""
        target = member or ctx.author
        
        try:
            history_response = self.reputation_service.get_reputation_history(
                ctx.guild.id, target.id, limit
            )
            
            if not history_response['success']:
                await ctx.send(f"❌ Error: {history_response['error']}")
                return
            
            history = history_response['data']
            
            if not history:
                await ctx.send(f"📜 No reputation history found for {target.display_name}.")
                return
            
            embed = Embed(
                title=f"📜 Reputation History - {target.display_name}",
                color=COLORS.INFO
            )
            
            for entry in history:
                giver = self.bot.get_user(int(entry['giver_id']))
                receiver = self.bot.get_user(int(entry['receiver_id']))
                
                giver_name = giver.display_name if giver else f"User {entry['giver_id']}"
                receiver_name = receiver.display_name if receiver else f"User {entry['receiver_id']}"
                
                timestamp = entry['timestamp']
                if isinstance(timestamp, str):
                    from datetime import datetime
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                field_name = f"{'+' if entry['amount'] > 0 else ''}{entry['amount']} reputation"
                field_value = f"From: {giver_name}\nTo: {receiver_name}"
                
                if entry['reason']:
                    field_value += f"\nReason: {entry['reason']}"
                
                field_value += f"\n<t:{int(timestamp.timestamp())}:R>"
                
                embed.add_field(
                    name=field_name,
                    value=field_value,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in reputation history: {e}")
            await ctx.send("❌ An error occurred while fetching reputation history.")

    @reputation_group.command(name='remove', aliases=['take', '-'])
    @commands.has_permissions(manage_guild=True)
    async def remove_reputation(self, ctx, member: discord.Member, amount: int, *, reason: str = None):
        """Remove reputation from a user (Admin only)"""
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.")
            return
        
        try:
            result = self.reputation_service.remove_reputation(
                ctx.guild.id, member.id, amount, reason, ctx.author.id
            )
            
            if result['success']:
                embed = Embed(
                    title="⭐ Reputation Removed",
                    description=f"{ctx.author.mention} removed {amount} reputation from {member.mention}",
                    color=COLORS.WARNING
                )
                
                embed.add_field(
                    name="New Reputation",
                    value=f"**{result['new_reputation']}**",
                    inline=True
                )
                
                if reason:
                    embed.add_field(
                        name="Reason",
                        value=reason,
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
                # Handle role updates
                await self.role_handler.process_reputation_change(member, result['new_reputation'])
                
            else:
                await ctx.send(f"❌ {result['error']}")
                
        except Exception as e:
            logger.error(f"Error removing reputation: {e}")
            await ctx.send("❌ An error occurred while removing reputation.")

    @reputation_group.command(name='roles')
    @commands.has_permissions(manage_guild=True)
    async def reputation_roles(self, ctx):
        """Show reputation roles for this server"""
        try:
            roles_response = self.reputation_service.get_all_reputation_roles(ctx.guild.id)
            
            if not roles_response['success']:
                await ctx.send(f"❌ Error: {roles_response['error']}")
                return
            
            roles = roles_response['data']
            
            if not roles:
                await ctx.send("🎭 No reputation roles configured for this server.")
                return
            
            embed = Embed(
                title="🎭 Reputation Roles",
                color=COLORS.INFO
            )
            
            description_lines = []
            for role_data in roles:
                role = ctx.guild.get_role(int(role_data['role_id']))
                role_name = role.name if role else f"Deleted Role ({role_data['role_id']})"
                description_lines.append(f"{role_data['reputation']} reputation: {role_name}")
            
            embed.description = "\n".join(description_lines)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in reputation roles command: {e}")
            await ctx.send("❌ An error occurred while fetching reputation roles.")

    @reputation_group.command(name='add_role')
    @commands.has_permissions(manage_guild=True)
    async def add_reputation_role(self, ctx, reputation: int, role: discord.Role):
        """Add a reputation role"""
        if reputation < 1:
            await ctx.send("❌ Reputation must be 1 or higher.")
            return
        
        try:
            result = self.reputation_service.add_reputation_role(ctx.guild.id, reputation, role.id)
            
            if result['success']:
                await ctx.send(f"✅ Added {role.mention} as reward for {reputation} reputation.")
            else:
                await ctx.send(f"❌ Error: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error adding reputation role: {e}")
            await ctx.send("❌ An error occurred while adding the reputation role.")

    @reputation_group.command(name='remove_role')
    @commands.has_permissions(manage_guild=True)
    async def remove_reputation_role(self, ctx, reputation: int):
        """Remove a reputation role"""
        try:
            result = self.reputation_service.remove_reputation_role(ctx.guild.id, reputation)
            
            if result['success']:
                await ctx.send(f"✅ Removed reputation role for {reputation} reputation.")
            else:
                await ctx.send(f"❌ Error: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error removing reputation role: {e}")
            await ctx.send("❌ An error occurred while removing the reputation role.")

async def setup(bot):
    await bot.add_cog(Reputation(bot))
