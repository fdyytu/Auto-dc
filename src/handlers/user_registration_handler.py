"""
User Registration Handler
Menangani proses registrasi user dengan validasi lengkap
"""

import logging
from typing import Optional, Dict, Any
from discord.ext import commands
import discord
import re

from src.services.user_service import UserService
from src.utils.response_formatter import ResponseFormatter
from src.utils.permission_validator import PermissionValidator

logger = logging.getLogger(__name__)

class UserRegistrationHandler:
    """Handler untuk registrasi user"""
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.formatter = ResponseFormatter()
        self.validator = PermissionValidator()
    
    def validate_growid(self, growid: str) -> tuple[bool, str]:
        """Validasi format GrowID"""
        if not growid or len(growid) < 3:
            return False, "GrowID minimal 3 karakter"
        
        if len(growid) > 18:
            return False, "GrowID maksimal 18 karakter"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', growid):
            return False, "GrowID hanya boleh huruf, angka, dan underscore"
        
        return True, "Valid"
    
    async def register_user(self, ctx: commands.Context, growid: str) -> bool:
        """Registrasi user baru"""
        try:
            # Validasi format GrowID
            is_valid, message = self.validate_growid(growid)
            if not is_valid:
                await ctx.send(self.formatter.error_message(f"❌ {message}"))
                return False
            
            # Cek apakah user sudah terdaftar
            existing_user = await self.user_service.get_user_by_discord_id(str(ctx.author.id))
            if existing_user:
                await ctx.send(self.formatter.error_message("Anda sudah terdaftar"))
                return False
            
            # Proses registrasi
            success = await self.user_service.create_user(growid, str(ctx.author.id))
            if success:
                embed = self.formatter.success_embed(
                    "Registrasi Berhasil",
                    f"GrowID {growid} berhasil didaftarkan!"
                )
                await ctx.send(embed=embed)
                await self.user_service.log_user_activity(str(ctx.author.id), "register", growid)
                return True
            else:
                await ctx.send(self.formatter.error_message("Gagal mendaftarkan user"))
                return False
                
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False
