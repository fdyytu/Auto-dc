"""
Leveling Reward Handler
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import discord
import logging
from typing import List, Optional

from business.leveling.leveling_service import LevelingService

logger = logging.getLogger(__name__)

class LevelingRewardHandler:
    """Handler untuk level rewards"""
    
    def __init__(self):
        self.leveling_service = LevelingService()
        self.logger = logger

    async def handle_level_up(self, member: discord.Member, new_level: int) -> Optional[str]:
        """Handle level up rewards and return announcement message"""
        try:
            guild_id = member.guild.id
            
            # Get settings
            settings_response = self.leveling_service.get_settings(guild_id)
            if not settings_response['success']:
                return None
                
            settings = settings_response['data']
            
            # Get reward roles for this level
            reward_roles = self.leveling_service.get_level_rewards_for_user(guild_id, new_level)
            
            if not reward_roles:
                return None
            
            # Check if rewards should stack
            stack_rewards = settings.get('stack_rewards', True)
            
            roles_to_add = []
            for reward in reward_roles:
                role = member.guild.get_role(int(reward['role_id']))
                if role and role not in member.roles:
                    roles_to_add.append(role)
                    if not stack_rewards:
                        break  # Only add highest level role if not stacking
            
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason=f"Level {new_level} reward")
                
                # Create announcement message
                role_mentions = ' '.join(role.mention for role in roles_to_add)
                announcement = (
                    f"🎉 Congratulations {member.mention}! "
                    f"You reached level {new_level} and earned: {role_mentions}"
                )
                
                return announcement
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error handling level up rewards: {e}")
            return None

    async def send_level_announcement(self, member: discord.Member, new_level: int, announcement: str):
        """Send level up announcement to configured channel"""
        try:
            guild_id = member.guild.id
            
            # Get settings
            settings_response = self.leveling_service.get_settings(guild_id)
            if not settings_response['success']:
                return
                
            settings = settings_response['data']
            announcement_channel_id = settings.get('announcement_channel')
            
            if announcement_channel_id:
                channel = member.guild.get_channel(int(announcement_channel_id))
                if channel:
                    await channel.send(announcement)
                    
        except Exception as e:
            self.logger.error(f"Error sending level announcement: {e}")

    async def process_level_up(self, member: discord.Member, new_level: int):
        """Process complete level up (rewards + announcement)"""
        try:
            # Handle rewards and get announcement
            announcement = await self.handle_level_up(member, new_level)
            
            # Send announcement if we have one
            if announcement:
                await self.send_level_announcement(member, new_level, announcement)
                
        except Exception as e:
            self.logger.error(f"Error processing level up: {e}")
