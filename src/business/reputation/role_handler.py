"""
Reputation Role Handler
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import discord
import logging
from typing import List, Optional

from src.business.reputation.reputation_service import ReputationService

logger = logging.getLogger(__name__)

class ReputationRoleHandler:
    """Handler untuk reputation roles"""
    
    def __init__(self):
        self.reputation_service = ReputationService()
        self.logger = logger

    async def update_user_roles(self, member: discord.Member, new_reputation: int) -> Optional[str]:
        """Update user roles based on reputation and return announcement message"""
        try:
            guild_id = member.guild.id
            
            # Get settings
            settings_response = self.reputation_service.get_settings(guild_id)
            if not settings_response['success']:
                return None
                
            settings = settings_response['data']
            
            # Get reputation roles for this reputation level
            reputation_roles = self.reputation_service.get_reputation_roles_for_user(guild_id, new_reputation)
            
            if not reputation_roles:
                return None
            
            # Check if roles should stack
            stack_roles = settings.get('stack_roles', False)
            
            roles_to_add = []
            roles_to_remove = []
            
            # Get all reputation roles in guild to manage properly
            all_rep_roles_response = self.reputation_service.get_all_reputation_roles(guild_id)
            if all_rep_roles_response['success']:
                all_rep_roles = all_rep_roles_response['data']
                
                if stack_roles:
                    # Add all roles user qualifies for
                    for rep_role in reputation_roles:
                        role = member.guild.get_role(int(rep_role['role_id']))
                        if role and role not in member.roles:
                            roles_to_add.append(role)
                else:
                    # Remove old reputation roles and add only the highest one
                    for rep_role in all_rep_roles:
                        role = member.guild.get_role(int(rep_role['role_id']))
                        if role and role in member.roles:
                            if rep_role['reputation'] > new_reputation:
                                roles_to_remove.append(role)
                    
                    # Add the highest role user qualifies for
                    if reputation_roles:
                        highest_role = member.guild.get_role(int(reputation_roles[0]['role_id']))
                        if highest_role and highest_role not in member.roles:
                            roles_to_add.append(highest_role)
            
            # Apply role changes
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"Reputation role update")
            
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason=f"Reputation role update")
                
                # Create announcement message
                role_mentions = ' '.join(role.mention for role in roles_to_add)
                announcement = (
                    f"🌟 {member.mention} earned reputation role(s): {role_mentions} "
                    f"(Reputation: {new_reputation})"
                )
                
                return announcement
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating reputation roles: {e}")
            return None

    async def send_role_announcement(self, member: discord.Member, announcement: str):
        """Send role update announcement to configured channel"""
        try:
            guild_id = member.guild.id
            
            # Get settings
            settings_response = self.reputation_service.get_settings(guild_id)
            if not settings_response['success']:
                return
                
            settings = settings_response['data']
            log_channel_id = settings.get('log_channel')
            
            if log_channel_id:
                channel = member.guild.get_channel(int(log_channel_id))
                if channel:
                    await channel.send(announcement)
                    
        except Exception as e:
            self.logger.error(f"Error sending role announcement: {e}")

    async def process_reputation_change(self, member: discord.Member, new_reputation: int):
        """Process complete reputation change (roles + announcement)"""
        try:
            # Update roles and get announcement
            announcement = await self.update_user_roles(member, new_reputation)
            
            # Send announcement if we have one
            if announcement:
                await self.send_role_announcement(member, announcement)
                
        except Exception as e:
            self.logger.error(f"Error processing reputation change: {e}")
