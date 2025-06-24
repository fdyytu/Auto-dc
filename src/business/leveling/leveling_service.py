"""
Leveling Business Logic Service
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import logging
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from src.database.repositories.leveling_repository import LevelingRepository

logger = logging.getLogger(__name__)

class LevelingService:
    """Business logic untuk leveling system"""
    
    def __init__(self):
        self.repository = LevelingRepository()
        self.xp_cooldown = {}  # In-memory cooldown tracking
        self.logger = logger

    def is_on_cooldown(self, guild_id: int, user_id: int) -> bool:
        """Check if user is on XP cooldown"""
        key = f"{guild_id}_{user_id}"
        if key in self.xp_cooldown:
            settings = self.repository.get_settings(guild_id)
            cooldown_seconds = settings.get('cooldown', 60)
            
            time_diff = datetime.utcnow() - self.xp_cooldown[key]
            return time_diff.total_seconds() < cooldown_seconds
        return False

    def set_cooldown(self, guild_id: int, user_id: int):
        """Set XP cooldown for user"""
        key = f"{guild_id}_{user_id}"
        self.xp_cooldown[key] = datetime.utcnow()

    def calculate_xp_gain(self, guild_id: int, user_id: int, member_roles: List[int]) -> int:
        """Calculate XP gain for a message"""
        settings = self.repository.get_settings(guild_id)
        min_xp = settings.get('min_xp', 15)
        max_xp = settings.get('max_xp', 25)
        
        base_xp = random.randint(min_xp, max_xp)
        
        # Check for double XP roles
        double_xp_roles = settings.get('double_xp_roles', '')
        if double_xp_roles:
            double_xp_role_ids = [int(role_id.strip()) for role_id in double_xp_roles.split(',') if role_id.strip()]
            if any(role_id in member_roles for role_id in double_xp_role_ids):
                base_xp *= 2
        
        return base_xp

    def should_ignore_message(self, guild_id: int, channel_id: int, member_roles: List[int]) -> bool:
        """Check if message should be ignored for XP"""
        settings = self.repository.get_settings(guild_id)
        
        # Check if leveling is disabled
        if not settings.get('enabled', True):
            return True
        
        # Check ignored channels
        ignored_channels = settings.get('ignored_channels', '')
        if ignored_channels:
            ignored_channel_ids = [int(ch_id.strip()) for ch_id in ignored_channels.split(',') if ch_id.strip()]
            if channel_id in ignored_channel_ids:
                return True
        
        # Check ignored roles
        ignored_roles = settings.get('ignored_roles', '')
        if ignored_roles:
            ignored_role_ids = [int(role_id.strip()) for role_id in ignored_roles.split(',') if role_id.strip()]
            if any(role_id in member_roles for role_id in ignored_role_ids):
                return True
        
        return False

    def process_message_xp(self, guild_id: int, user_id: int, channel_id: int, member_roles: List[int]) -> Dict:
        """Process XP gain from a message"""
        try:
            # Check if should ignore
            if self.should_ignore_message(guild_id, channel_id, member_roles):
                return {
                    'success': True,
                    'xp_gained': 0,
                    'level_up': False,
                    'new_level': 0,
                    'new_xp': 0
                }
            
            # Check cooldown
            if self.is_on_cooldown(guild_id, user_id):
                return {
                    'success': True,
                    'xp_gained': 0,
                    'level_up': False,
                    'new_level': 0,
                    'new_xp': 0
                }
            
            # Calculate XP gain
            xp_gain = self.calculate_xp_gain(guild_id, user_id, member_roles)
            
            # Update user XP
            new_xp, new_level, level_up = self.repository.update_user_xp(guild_id, user_id, xp_gain)
            
            # Set cooldown
            self.set_cooldown(guild_id, user_id)
            
            return {
                'success': True,
                'xp_gained': xp_gain,
                'level_up': level_up,
                'new_level': new_level,
                'new_xp': new_xp
            }
            
        except Exception as e:
            self.logger.error(f"Error processing message XP: {e}")
            return {
                'success': False,
                'error': str(e),
                'xp_gained': 0,
                'level_up': False,
                'new_level': 0,
                'new_xp': 0
            }

    def get_user_stats(self, guild_id: int, user_id: int) -> Dict:
        """Get user leveling stats"""
        try:
            user_data = self.repository.get_user_level_data(guild_id, user_id)
            if not user_data:
                return {
                    'success': True,
                    'data': {
                        'xp': 0,
                        'level': 0,
                        'messages': 0,
                        'rank': None,
                        'xp_for_next': 100,
                        'progress_percent': 0
                    }
                }
            
            rank = self.repository.get_user_rank(guild_id, user_id)
            xp_for_next = self.repository.get_xp_for_next_level(user_data['xp'])
            current_level_xp = self.repository.get_xp_for_level(user_data['level'])
            
            # Calculate progress percentage
            if user_data['level'] == 0:
                progress_percent = (user_data['xp'] / 100) * 100
            else:
                xp_in_current_level = user_data['xp'] - current_level_xp
                xp_needed_for_next = xp_for_next - current_level_xp
                progress_percent = (xp_in_current_level / xp_needed_for_next) * 100
            
            return {
                'success': True,
                'data': {
                    'xp': user_data['xp'],
                    'level': user_data['level'],
                    'messages': user_data['messages'],
                    'rank': rank,
                    'xp_for_next': xp_for_next,
                    'progress_percent': min(100, max(0, progress_percent))
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user stats: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }

    def get_leaderboard(self, guild_id: int, limit: int = 10) -> Dict:
        """Get guild leaderboard"""
        try:
            leaderboard_data = self.repository.get_leaderboard(guild_id, limit)
            
            return {
                'success': True,
                'data': leaderboard_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting leaderboard: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def get_level_rewards_for_user(self, guild_id: int, level: int) -> List[Dict]:
        """Get level rewards that user should receive"""
        try:
            return self.repository.get_level_rewards(guild_id, level)
        except Exception as e:
            self.logger.error(f"Error getting level rewards: {e}")
            return []

    def get_all_level_rewards(self, guild_id: int) -> Dict:
        """Get all level rewards for guild"""
        try:
            rewards = self.repository.get_level_rewards(guild_id)
            return {
                'success': True,
                'data': rewards
            }
        except Exception as e:
            self.logger.error(f"Error getting all level rewards: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def add_level_reward(self, guild_id: int, level: int, role_id: int) -> Dict:
        """Add level reward"""
        try:
            success = self.repository.add_level_reward(guild_id, level, role_id)
            return {
                'success': success,
                'error': None if success else "Failed to add level reward"
            }
        except Exception as e:
            self.logger.error(f"Error adding level reward: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def remove_level_reward(self, guild_id: int, level: int) -> Dict:
        """Remove level reward"""
        try:
            success = self.repository.remove_level_reward(guild_id, level)
            return {
                'success': success,
                'error': None if success else "Failed to remove level reward"
            }
        except Exception as e:
            self.logger.error(f"Error removing level reward: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_settings(self, guild_id: int) -> Dict:
        """Get leveling settings"""
        try:
            settings = self.repository.get_settings(guild_id)
            return {
                'success': True,
                'data': settings
            }
        except Exception as e:
            self.logger.error(f"Error getting settings: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }

    def update_settings(self, guild_id: int, settings: Dict) -> Dict:
        """Update leveling settings"""
        try:
            success = self.repository.update_settings(guild_id, settings)
            return {
                'success': success,
                'error': None if success else "Failed to update settings"
            }
        except Exception as e:
            self.logger.error(f"Error updating settings: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup_cooldowns(self):
        """Clean up old cooldown entries"""
        try:
            current_time = datetime.utcnow()
            keys_to_remove = []
            
            for key, timestamp in self.xp_cooldown.items():
                if (current_time - timestamp).total_seconds() > 300:  # 5 minutes
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.xp_cooldown[key]
                
        except Exception as e:
            self.logger.error(f"Error cleaning up cooldowns: {e}")
