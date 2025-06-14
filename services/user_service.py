"""
User Service
Menangani business logic untuk user management
"""

import logging
from typing import Optional, Dict, Any, List
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)

class UserService:
    """Service untuk menangani operasi user"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_user_by_growid(self, growid: str) -> Optional[Dict[str, Any]]:
        """Ambil user berdasarkan growid"""
        try:
            query = "SELECT * FROM users WHERE growid = ?"
            result = await self.db.execute_query(query, (growid,))
            return dict(result[0]) if result else None
        except Exception as e:
            logger.error(f"Error get user by growid: {e}")
            return None
    
    async def get_user_by_discord_id(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """Ambil user berdasarkan discord ID"""
        try:
            query = """
                SELECT u.*, ug.discord_id 
                FROM users u 
                JOIN user_growid ug ON u.growid = ug.growid 
                WHERE ug.discord_id = ?
            """
            result = await self.db.execute_query(query, (discord_id,))
            return dict(result[0]) if result else None
        except Exception as e:
            logger.error(f"Error get user by discord ID: {e}")
            return None
    
    async def create_user(self, growid: str, discord_id: str) -> bool:
        """Buat user baru"""
        try:
            # Cek apakah user sudah ada
            existing = await self.get_user_by_growid(growid)
            if existing:
                logger.warning(f"User {growid} sudah ada")
                return False
            
            # Buat user baru
            user_query = "INSERT INTO users (growid) VALUES (?)"
            if not await self.db.execute_update(user_query, (growid,)):
                return False
            
            # Link dengan discord ID
            link_query = "INSERT INTO user_growid (discord_id, growid) VALUES (?, ?)"
            return await self.db.execute_update(link_query, (discord_id, growid))
            
        except Exception as e:
            logger.error(f"Error create user: {e}")
            return False
    
    async def update_balance(self, growid: str, balance_type: str, amount: int) -> bool:
        """Update balance user"""
        try:
            if balance_type not in ['balance_wl', 'balance_dl', 'balance_bgl']:
                logger.error(f"Invalid balance type: {balance_type}")
                return False
            
            query = f"UPDATE users SET {balance_type} = {balance_type} + ?, updated_at = CURRENT_TIMESTAMP WHERE growid = ?"
            return await self.db.execute_update(query, (amount, growid))
            
        except Exception as e:
            logger.error(f"Error update balance: {e}")
            return False
    
    async def get_user_balance(self, growid: str) -> Optional[Dict[str, int]]:
        """Ambil balance user"""
        try:
            query = "SELECT balance_wl, balance_dl, balance_bgl FROM users WHERE growid = ?"
            result = await self.db.execute_query(query, (growid,))
            if result:
                row = result[0]
                return {
                    'wl': row['balance_wl'],
                    'dl': row['balance_dl'],
                    'bgl': row['balance_bgl']
                }
            return None
        except Exception as e:
            logger.error(f"Error get user balance: {e}")
            return None
    
    async def log_user_activity(self, discord_id: str, activity_type: str, details: str = None) -> bool:
        """Log aktivitas user"""
        try:
            query = "INSERT INTO user_activity (discord_id, activity_type, details) VALUES (?, ?, ?)"
            return await self.db.execute_update(query, (discord_id, activity_type, details))
        except Exception as e:
            logger.error(f"Error log user activity: {e}")
            return False
