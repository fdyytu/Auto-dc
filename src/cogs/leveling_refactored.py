"""
Refactored Leveling Cog
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import discord
from discord.ext import commands, tasks
import logging
from typing import Optional

from business.leveling.leveling_service import LevelingService
from business.leveling.reward_handler import LevelingRewardHandler
from config.constants import COLORS
from cogs.utils import Embed

logger = logging.getLogger(__name__)

class Leveling(commands.Cog):
    """⭐ Advanced Leveling System"""
    
    def __init__(self, bot):
        self.bot = bot
        self.leveling_service = LevelingService()
        self.reward_handler = LevelingRewardHandler()
        self.cleanup_task.start()

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.cleanup_task.cancel()

    @tasks.loop(minutes=5)
    async def cleanup_task(self):
        """Periodic cleanup of cooldowns"""
        try:
            self.leveling_service.cleanup_cooldowns()
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")

    @cleanup_task.before_loop
    async def before_cleanup_task(self):
        """Wait until bot is ready"""
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle XP gain from messages"""
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return
        
        try:
            guild_id = message.guild.id
            user_id = message.author.id
            channel_id = message.channel.id
            member_roles = [role.id for role in message.author.roles]
            
            # Process XP gain
            result = self.leveling_service.process_message_xp(
                guild_id, user_id, channel_id, member_roles
            )
            
            if result['success'] and result['level_up']:
                # Handle level up
                await self.reward_handler.process_level_up(
                    message.author, result['new_level']
                )
                
        except Exception as e:
            logger.error(f"Error processing message XP: {e}")

    @commands.group(name='level', aliases=['lvl'], invoke_without_command=True)
    async def level_group(self, ctx, member: Optional[discord.Member] = None):
        """Show level information for a user"""
        target = member or ctx.author
        
        try:
            stats_response = self.leveling_service.get_user_stats(ctx.guild.id, target.id)
            
            if not stats_response['success']:
                await ctx.send(f"❌ Error: {stats_response['error']}")
                return
            
            stats = stats_response['data']
            
            embed = Embed(
                title=f"📊 Level Stats - {target.display_name}",
                color=COLORS.INFO
            )
            
            embed.add_field(
                name="Level", 
                value=f"**{stats['level']}**", 
                inline=True
            )
            embed.add_field(
                name="XP", 
                value=f"**{stats['xp']:,}**", 
                inline=True
            )
            embed.add_field(
                name="Rank", 
                value=f"**#{stats['rank']}**" if stats['rank'] else "**N/A**", 
                inline=True
            )
            
            embed.add_field(
                name="Messages", 
                value=f"**{stats['messages']:,}**", 
                inline=True
            )
            embed.add_field(
                name="Next Level", 
                value=f"**{stats['xp_for_next']:,} XP**", 
                inline=True
            )
            embed.add_field(
                name="Progress", 
                value=f"**{stats['progress_percent']:.1f}%**", 
                inline=True
            )
            
            # Progress bar
            progress_bar_length = 20
            filled_length = int(progress_bar_length * stats['progress_percent'] / 100)
            bar = "█" * filled_length + "░" * (progress_bar_length - filled_length)
            
            embed.add_field(
                name="Progress Bar",
                value=f"`{bar}` {stats['progress_percent']:.1f}%",
                inline=False
            )
            
            embed.set_thumbnail(url=target.display_avatar.url)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in level command: {e}")
            await ctx.send("❌ An error occurred while fetching level information.")

    @level_group.command(name='leaderboard', aliases=['lb', 'top'])
    async def leaderboard(self, ctx, limit: int = 10):
        """Show server leaderboard"""
        if limit > 25:
            limit = 25
        elif limit < 1:
            limit = 10
            
        try:
            lb_response = self.leveling_service.get_leaderboard(ctx.guild.id, limit)
            
            if not lb_response['success']:
                await ctx.send(f"❌ Error: {lb_response['error']}")
                return
            
            leaderboard = lb_response['data']
            
            if not leaderboard:
                await ctx.send("📊 No leveling data found for this server.")
                return
            
            embed = Embed(
                title=f"🏆 Leaderboard - Top {len(leaderboard)}",
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
                    f"{medal} {username} - Level {user_data['level']} ({user_data['xp']:,} XP)"
                )
            
            embed.description = "\n".join(description_lines)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await ctx.send("❌ An error occurred while fetching the leaderboard.")

    @level_group.command(name='rewards')
    @commands.has_permissions(manage_guild=True)
    async def level_rewards(self, ctx):
        """Show level rewards for this server"""
        try:
            rewards_response = self.leveling_service.get_all_level_rewards(ctx.guild.id)
            
            if not rewards_response['success']:
                await ctx.send(f"❌ Error: {rewards_response['error']}")
                return
            
            rewards = rewards_response['data']
            
            if not rewards:
                await ctx.send("🎁 No level rewards configured for this server.")
                return
            
            embed = Embed(
                title="🎁 Level Rewards",
                color=COLORS.INFO
            )
            
            description_lines = []
            for reward in rewards:
                role = ctx.guild.get_role(int(reward['role_id']))
                role_name = role.name if role else f"Deleted Role ({reward['role_id']})"
                description_lines.append(f"Level {reward['level']}: {role_name}")
            
            embed.description = "\n".join(description_lines)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in level rewards command: {e}")
            await ctx.send("❌ An error occurred while fetching level rewards.")

    @level_group.command(name='add_reward')
    @commands.has_permissions(manage_guild=True)
    async def add_level_reward(self, ctx, level: int, role: discord.Role):
        """Add a level reward"""
        if level < 1:
            await ctx.send("❌ Level must be 1 or higher.")
            return
        
        try:
            result = self.leveling_service.add_level_reward(ctx.guild.id, level, role.id)
            
            if result['success']:
                await ctx.send(f"✅ Added {role.mention} as reward for level {level}.")
            else:
                await ctx.send(f"❌ Error: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error adding level reward: {e}")
            await ctx.send("❌ An error occurred while adding the level reward.")

    @level_group.command(name='remove_reward')
    @commands.has_permissions(manage_guild=True)
    async def remove_level_reward(self, ctx, level: int):
        """Remove a level reward"""
        try:
            result = self.leveling_service.remove_level_reward(ctx.guild.id, level)
            
            if result['success']:
                await ctx.send(f"✅ Removed level reward for level {level}.")
            else:
                await ctx.send(f"❌ Error: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error removing level reward: {e}")
            await ctx.send("❌ An error occurred while removing the level reward.")

async def setup(bot):
    await bot.add_cog(Leveling(bot))
