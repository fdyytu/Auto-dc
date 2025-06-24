"""
World Repository
Menangani operasi database untuk world
"""

import logging
from datetime import datetime
from typing import List, Optional
from database.models.world import World
from database.manager import DatabaseManager

logger = logging.getLogger(__name__)

class WorldRepository:
    """Repository untuk operasi world di database"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_world(self, world: World) -> bool:
        """Tambah world baru"""
        try:
            query = """
                INSERT INTO worlds (world_name, owner_name, bot_name, created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                world.world_name,
                world.owner_name,
                world.bot_name,
                world.created_at.isoformat(),
                world.updated_at.isoformat(),
                world.is_active
            )
            
            return await self.db_manager.execute_update(query, params)
            
        except Exception as e:
            logger.error(f"Error creating world: {e}")
            return False
    
    async def get_world(self, world_name: str) -> Optional[World]:
        """Ambil world berdasarkan nama"""
        try:
            query = "SELECT * FROM worlds WHERE world_name = ? AND is_active = 1"
            result = await self.db_manager.execute_query(query, (world_name,))
            
            if result and len(result) > 0:
                row = result[0]
                return World.from_dict(dict(row))
            return None
            
        except Exception as e:
            logger.error(f"Error getting world {world_name}: {e}")
            return None
    
    async def get_all_worlds(self) -> List[World]:
        """Ambil semua world aktif"""
        try:
            query = "SELECT * FROM worlds WHERE is_active = 1 ORDER BY created_at DESC"
            result = await self.db_manager.execute_query(query)
            
            if result:
                return [World.from_dict(dict(row)) for row in result]
            return []
            
        except Exception as e:
            logger.error(f"Error getting all worlds: {e}")
            return []
    
    async def update_world(self, world_name: str, owner_name: str = None, bot_name: str = None) -> bool:
        """Update world data"""
        try:
            updates = []
            params = []
            
            if owner_name is not None:
                updates.append("owner_name = ?")
                params.append(owner_name)
            
            if bot_name is not None:
                updates.append("bot_name = ?")
                params.append(bot_name)
            
            if not updates:
                return True
            
            updates.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(world_name)
            
            query = f"UPDATE worlds SET {', '.join(updates)} WHERE world_name = ?"
            return await self.db_manager.execute_update(query, tuple(params))
            
        except Exception as e:
            logger.error(f"Error updating world {world_name}: {e}")
            return False
    
    async def delete_world(self, world_name: str) -> bool:
        """Soft delete world (set is_active = 0)"""
        try:
            query = "UPDATE worlds SET is_active = 0, updated_at = ? WHERE world_name = ?"
            params = (datetime.utcnow().isoformat(), world_name)
            
            return await self.db_manager.execute_update(query, params)
            
        except Exception as e:
            logger.error(f"Error deleting world {world_name}: {e}")
            return False
    
    async def world_exists(self, world_name: str) -> bool:
        """Cek apakah world sudah ada"""
        try:
            query = "SELECT 1 FROM worlds WHERE world_name = ? AND is_active = 1"
            result = await self.db_manager.execute_query(query, (world_name,))
            return result is not None and len(result) > 0
            
        except Exception as e:
            logger.error(f"Error checking world existence {world_name}: {e}")
            return False
