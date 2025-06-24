"""
Permission Validator
Utility untuk validasi permission dan role dengan konsisten
"""

import logging
from typing import List, Dict, Any, Optional
from discord.ext import commands
import discord

logger = logging.getLogger(__name__)

class PermissionValidator:
    """Validator untuk permission dan role"""
    
    def __init__(self):
        self.admin_roles = ['Admin', 'Moderator', 'Owner']
        self.staff_roles = ['Staff', 'Helper', 'Support']
        self.vip_roles = ['VIP', 'Premium', 'Donator']
    
    def has_admin_role(self, user: discord.Member) -> bool:
        """Cek apakah user memiliki role admin"""
        user_roles = [role.name for role in user.roles]
        return any(role in self.admin_roles for role in user_roles)
    
    def has_staff_role(self, user: discord.Member) -> bool:
        """Cek apakah user memiliki role staff"""
        user_roles = [role.name for role in user.roles]
        return any(role in self.staff_roles for role in user_roles)
    
    def has_vip_role(self, user: discord.Member) -> bool:
        """Cek apakah user memiliki role VIP"""
        user_roles = [role.name for role in user.roles]
        return any(role in self.vip_roles for role in user_roles)
    
    def can_use_command(self, user: discord.Member, command_level: str) -> bool:
        """Cek apakah user bisa menggunakan command berdasarkan level"""
        if command_level == 'admin':
            return self.has_admin_role(user)
        elif command_level == 'staff':
            return self.has_admin_role(user) or self.has_staff_role(user)
        elif command_level == 'vip':
            return self.has_admin_role(user) or self.has_staff_role(user) or self.has_vip_role(user)
        else:
            return True  # Public command
    
    def validate_channel_permissions(self, ctx: commands.Context, allowed_channels: List[int]) -> bool:
        """Validasi apakah command bisa digunakan di channel ini"""
        if not allowed_channels:
            return True
        return ctx.channel.id in allowed_channels
    
    def get_user_permission_level(self, user: discord.Member) -> str:
        """Dapatkan level permission user"""
        if self.has_admin_role(user):
            return 'admin'
        elif self.has_staff_role(user):
            return 'staff'
        elif self.has_vip_role(user):
            return 'vip'
        else:
            return 'user'
