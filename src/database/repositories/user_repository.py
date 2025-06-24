"""
User Repository
Menangani operasi database untuk user
"""

import logging
from typing import Optional, List
from database.connection import DatabaseManager
from database.models import User, UserGrowID

logger = logging.getLogger(__name__)

class UserRepository:
    """Repository untuk operasi user"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logger
    
    async def get_user_by_growid(self, growid: str) -> Optional[User]:
        """Ambil user berdasarkan growid"""
        try:
            query = "SELECT * FROM users WHERE growid = ?"
            result = await self.db.execute_query(query, (growid,))
            
            if result and len(result) > 0:
                row = result[0]
                return User(
                    growid=row['growid'],
                    balance_wl=row['balance_wl'],
                    balance_dl=row['balance_dl'],
                    balance_bgl=row['balance_bgl'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting user by growid: {e}")
            return None
    
    async def get_user_by_discord_id(self, discord_id: str) -> Optional[User]:
        """Ambil user berdasarkan discord ID"""
        try:
            # Pertama ambil growid dari mapping
            query = "SELECT growid FROM user_growid WHERE discord_id = ?"
            result = await self.db.execute_query(query, (discord_id,))
            
            if not result or len(result) == 0:
                return None
            
            growid = result[0]['growid']
            return await self.get_user_by_growid(growid)
            
        except Exception as e:
            self.logger.error(f"Error getting user by discord ID: {e}")
            return None
    
    async def create_user(self, user: User) -> bool:
        """Buat user baru"""
        try:
            query = """
                INSERT INTO users (growid, balance_wl, balance_dl, balance_bgl, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                user.growid,
                user.balance_wl,
                user.balance_dl,
                user.balance_bgl,
                user.created_at.isoformat() if user.created_at else None,
                user.updated_at.isoformat() if user.updated_at else None
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            return False
    
    async def update_user(self, user: User) -> bool:
        """Update user"""
        try:
            query = """
                UPDATE users 
                SET balance_wl = ?, balance_dl = ?, balance_bgl = ?, updated_at = ?
                WHERE growid = ?
            """
            params = (
                user.balance_wl,
                user.balance_dl,
                user.balance_bgl,
                user.updated_at.isoformat() if user.updated_at else None,
                user.growid
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            self.logger.error(f"Error updating user: {e}")
            return False
    
    async def delete_user(self, growid: str) -> bool:
        """Hapus user"""
        try:
            query = "DELETE FROM users WHERE growid = ?"
            return await self.db.execute_update(query, (growid,))
            
        except Exception as e:
            self.logger.error(f"Error deleting user: {e}")
            return False
    
    async def link_discord_user(self, discord_id: str, growid: str) -> bool:
        """Link discord ID dengan growid"""
        try:
            query = """
                INSERT OR REPLACE INTO user_growid (discord_id, growid, created_at)
                VALUES (?, ?, ?)
            """
            from datetime import datetime
            params = (discord_id, growid, datetime.utcnow().isoformat())
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            self.logger.error(f"Error linking discord user: {e}")
            return False
    
    async def unlink_discord_user(self, discord_id: str) -> bool:
        """Unlink discord ID"""
        try:
            query = "DELETE FROM user_growid WHERE discord_id = ?"
            return await self.db.execute_update(query, (discord_id,))
            
        except Exception as e:
            self.logger.error(f"Error unlinking discord user: {e}")
            return False
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Ambil semua user dengan pagination"""
        try:
            query = "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?"
            result = await self.db.execute_query(query, (limit, offset))
            
            users = []
            if result:
                for row in result:
                    user = User(
                        growid=row['growid'],
                        balance_wl=row['balance_wl'],
                        balance_dl=row['balance_dl'],
                        balance_bgl=row['balance_bgl'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    users.append(user)
            
            return users
            
        except Exception as e:
            self.logger.error(f"Error getting all users: {e}")
            return []
    
    async def get_user_count(self) -> int:
        """Ambil jumlah total user"""
        try:
            query = "SELECT COUNT(*) as count FROM users"
            result = await self.db.execute_query(query)
            
            if result and len(result) > 0:
                return result[0]['count']
            return 0
            
        except Exception as e:
            self.logger.error(f"Error getting user count: {e}")
            return 0
    
    async def search_users(self, search_term: str, limit: int = 50) -> List[User]:
        """Cari user berdasarkan growid"""
        try:
            query = "SELECT * FROM users WHERE growid LIKE ? ORDER BY growid LIMIT ?"
            search_pattern = f"%{search_term}%"
            result = await self.db.execute_query(query, (search_pattern, limit))
            
            users = []
            if result:
                for row in result:
                    user = User(
                        growid=row['growid'],
                        balance_wl=row['balance_wl'],
                        balance_dl=row['balance_dl'],
                        balance_bgl=row['balance_bgl'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    users.append(user)
            
            return users
            
        except Exception as e:
            self.logger.error(f"Error searching users: {e}")
            return []
