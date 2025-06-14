"""
Reputation Business Logic Service
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from data.repositories.reputation_repository import ReputationRepository

logger = logging.getLogger(__name__)

class ReputationService:
    """Business logic untuk reputation system"""
    
    def __init__(self):
        self.repository = ReputationRepository()
        self.cooldowns = {}  # In-memory cooldown tracking
        self.logger = logger

    def is_on_cooldown(self, guild_id: int, user_id: int) -> Tuple[bool, int]:
        """Check if user is on cooldown, return (is_on_cooldown, remaining_seconds)"""
        key = f"{guild_id}_{user_id}"
        if key in self.cooldowns:
            settings = self.repository.get_settings(guild_id)
            cooldown_seconds = settings.get('cooldown', 43200)  # 12 hours default
            
            time_diff = datetime.utcnow() - self.cooldowns[key]
            remaining = cooldown_seconds - time_diff.total_seconds()
            
            if remaining > 0:
                return True, int(remaining)
            else:
                # Cooldown expired, remove it
                del self.cooldowns[key]
                return False, 0
        return False, 0

    def set_cooldown(self, guild_id: int, user_id: int):
        """Set cooldown for user"""
        key = f"{guild_id}_{user_id}"
        self.cooldowns[key] = datetime.utcnow()

    def can_give_reputation(self, guild_id: int, giver_id: int, receiver_id: int, 
                          giver_roles: List[int], receiver_roles: List[int]) -> Dict:
        """Check if user can give reputation"""
        try:
            # Can't give to self
            if giver_id == receiver_id:
                return {
                    'success': False,
                    'error': "You cannot give reputation to yourself."
                }
            
            settings = self.repository.get_settings(guild_id)
            
            # Check if giver has required role
            required_role = settings.get('required_role')
            if required_role and int(required_role) not in giver_roles:
                return {
                    'success': False,
                    'error': "You don't have the required role to give reputation."
                }
            
            # Check if giver has blacklisted role
            blacklisted_roles = settings.get('blacklisted_roles', '')
            if blacklisted_roles:
                blacklisted_role_ids = [int(role_id.strip()) for role_id in blacklisted_roles.split(',') if role_id.strip()]
                if any(role_id in giver_roles for role_id in blacklisted_role_ids):
                    return {
                        'success': False,
                        'error': "You are not allowed to give reputation."
                    }
            
            # Check cooldown
            is_on_cooldown, remaining = self.is_on_cooldown(guild_id, giver_id)
            if is_on_cooldown:
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                return {
                    'success': False,
                    'error': f"You're on cooldown. Try again in {hours}h {minutes}m."
                }
            
            # Check daily limit
            daily_given = self.repository.get_daily_given_count(guild_id, giver_id)
            max_daily = settings.get('max_daily', 3)
            if daily_given >= max_daily:
                return {
                    'success': False,
                    'error': f"You've reached your daily limit of {max_daily} reputation points."
                }
            
            return {
                'success': True,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error checking reputation permissions: {e}")
            return {
                'success': False,
                'error': "An error occurred while checking permissions."
            }

    def give_reputation(self, guild_id: int, giver_id: int, receiver_id: int, 
                       amount: int = 1, reason: str = None, message_id: int = None) -> Dict:
        """Give reputation to a user"""
        try:
            # Update giver's stats (total_given)
            giver_success = self.repository.update_user_reputation(
                guild_id, giver_id, 0, is_giver=True
            )
            
            # Update receiver's reputation
            receiver_success = self.repository.update_user_reputation(
                guild_id, receiver_id, amount, is_giver=False
            )
            
            # Add to history
            history_success = self.repository.add_reputation_history(
                guild_id, giver_id, receiver_id, amount, reason, message_id
            )
            
            if giver_success and receiver_success and history_success:
                # Set cooldown
                self.set_cooldown(guild_id, giver_id)
                
                # Get updated receiver data
                receiver_data = self.repository.get_user_reputation(guild_id, receiver_id)
                new_reputation = receiver_data['reputation'] if receiver_data else amount
                
                return {
                    'success': True,
                    'new_reputation': new_reputation,
                    'amount_given': amount
                }
            else:
                return {
                    'success': False,
                    'error': "Failed to update reputation in database."
                }
                
        except Exception as e:
            self.logger.error(f"Error giving reputation: {e}")
            return {
                'success': False,
                'error': "An error occurred while giving reputation."
            }

    def remove_reputation(self, guild_id: int, user_id: int, amount: int, 
                         reason: str = None, admin_id: int = None) -> Dict:
        """Remove reputation from a user (admin only)"""
        try:
            success = self.repository.update_user_reputation(
                guild_id, user_id, -amount, is_giver=False
            )
            
            if success and admin_id:
                # Add to history
                self.repository.add_reputation_history(
                    guild_id, admin_id, user_id, -amount, reason
                )
            
            if success:
                # Get updated user data
                user_data = self.repository.get_user_reputation(guild_id, user_id)
                new_reputation = user_data['reputation'] if user_data else 0
                
                return {
                    'success': True,
                    'new_reputation': max(0, new_reputation)  # Don't allow negative reputation
                }
            else:
                return {
                    'success': False,
                    'error': "Failed to remove reputation from database."
                }
                
        except Exception as e:
            self.logger.error(f"Error removing reputation: {e}")
            return {
                'success': False,
                'error': "An error occurred while removing reputation."
            }

    def get_user_stats(self, guild_id: int, user_id: int) -> Dict:
        """Get user reputation stats"""
        try:
            user_data = self.repository.get_user_reputation(guild_id, user_id)
            if not user_data:
                return {
                    'success': True,
                    'data': {
                        'reputation': 0,
                        'total_given': 0,
                        'total_received': 0,
                        'rank': None,
                        'last_given': None,
                        'last_received': None
                    }
                }
            
            rank = self.repository.get_user_rank(guild_id, user_id)
            
            return {
                'success': True,
                'data': {
                    'reputation': user_data['reputation'],
                    'total_given': user_data['total_given'],
                    'total_received': user_data['total_received'],
                    'rank': rank,
                    'last_given': user_data.get('last_given'),
                    'last_received': user_data.get('last_received')
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
        """Get reputation leaderboard"""
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

    def get_reputation_history(self, guild_id: int, user_id: int = None, limit: int = 10) -> Dict:
        """Get reputation history"""
        try:
            history_data = self.repository.get_reputation_history(guild_id, user_id, limit)
            
            return {
                'success': True,
                'data': history_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting reputation history: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def get_reputation_roles_for_user(self, guild_id: int, reputation: int) -> List[Dict]:
        """Get reputation roles that user should have"""
        try:
            return self.repository.get_reputation_roles(guild_id, reputation)
        except Exception as e:
            self.logger.error(f"Error getting reputation roles: {e}")
            return []

    def get_all_reputation_roles(self, guild_id: int) -> Dict:
        """Get all reputation roles for guild"""
        try:
            roles = self.repository.get_reputation_roles(guild_id)
            return {
                'success': True,
                'data': roles
            }
        except Exception as e:
            self.logger.error(f"Error getting all reputation roles: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def add_reputation_role(self, guild_id: int, reputation: int, role_id: int) -> Dict:
        """Add reputation role"""
        try:
            success = self.repository.add_reputation_role(guild_id, reputation, role_id)
            return {
                'success': success,
                'error': None if success else "Failed to add reputation role"
            }
        except Exception as e:
            self.logger.error(f"Error adding reputation role: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def remove_reputation_role(self, guild_id: int, reputation: int) -> Dict:
        """Remove reputation role"""
        try:
            success = self.repository.remove_reputation_role(guild_id, reputation)
            return {
                'success': success,
                'error': None if success else "Failed to remove reputation role"
            }
        except Exception as e:
            self.logger.error(f"Error removing reputation role: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_settings(self, guild_id: int) -> Dict:
        """Get reputation settings"""
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
        """Update reputation settings"""
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
            
            for key, timestamp in self.cooldowns.items():
                if (current_time - timestamp).total_seconds() > 43200:  # 12 hours
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cooldowns[key]
                
        except Exception as e:
            self.logger.error(f"Error cleaning up cooldowns: {e}")
