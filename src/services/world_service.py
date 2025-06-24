"""
World Service
Service untuk mengelola world operations
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from database.models.world import World
from database.repositories.world_repository import WorldRepository
from database.manager import DatabaseManager

logger = logging.getLogger(__name__)

@dataclass
class ServiceResponse:
    """Response wrapper untuk service operations"""
    success: bool
    data: Any = None
    error: str = None
    
    @classmethod
    def success_response(cls, data: Any = None) -> 'ServiceResponse':
        return cls(success=True, data=data)
    
    @classmethod
    def error_response(cls, error: str) -> 'ServiceResponse':
        return cls(success=False, error=error)

class WorldService:
    """Service untuk mengelola world operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.world_repository = WorldRepository(db_manager)
    
    async def add_world(self, world_name: str, owner_name: str, bot_name: str) -> ServiceResponse:
        """Tambah world baru"""
        try:
            # Validasi input
            if not world_name or not world_name.strip():
                return ServiceResponse.error_response("Nama world tidak boleh kosong")
            
            if not owner_name or not owner_name.strip():
                return ServiceResponse.error_response("Nama pemilik tidak boleh kosong")
            
            if not bot_name or not bot_name.strip():
                return ServiceResponse.error_response("Nama bot tidak boleh kosong")
            
            # Normalize input
            world_name = world_name.strip().upper()
            owner_name = owner_name.strip()
            bot_name = bot_name.strip()
            
            # Cek apakah world sudah ada
            if await self.world_repository.world_exists(world_name):
                return ServiceResponse.error_response(f"World {world_name} sudah terdaftar")
            
            # Buat world baru
            world = World(
                world_name=world_name,
                owner_name=owner_name,
                bot_name=bot_name
            )
            
            success = await self.world_repository.create_world(world)
            if not success:
                return ServiceResponse.error_response("Gagal menambahkan world ke database")
            
            logger.info(f"World {world_name} berhasil ditambahkan oleh {owner_name}")
            return ServiceResponse.success_response(world.to_dict())
            
        except Exception as e:
            logger.error(f"Error adding world: {e}")
            return ServiceResponse.error_response("Terjadi error saat menambahkan world")
    
    async def get_world(self, world_name: str) -> ServiceResponse:
        """Ambil data world"""
        try:
            if not world_name or not world_name.strip():
                return ServiceResponse.error_response("Nama world tidak boleh kosong")
            
            world_name = world_name.strip().upper()
            world = await self.world_repository.get_world(world_name)
            
            if not world:
                return ServiceResponse.error_response(f"World {world_name} tidak ditemukan")
            
            return ServiceResponse.success_response(world.to_dict())
            
        except Exception as e:
            logger.error(f"Error getting world {world_name}: {e}")
            return ServiceResponse.error_response("Terjadi error saat mengambil data world")
    
    async def get_all_worlds(self) -> ServiceResponse:
        """Ambil semua world"""
        try:
            worlds = await self.world_repository.get_all_worlds()
            world_data = [world.to_dict() for world in worlds]
            
            return ServiceResponse.success_response(world_data)
            
        except Exception as e:
            logger.error(f"Error getting all worlds: {e}")
            return ServiceResponse.error_response("Terjadi error saat mengambil data worlds")
    
    async def update_world(self, world_name: str, owner_name: str = None, bot_name: str = None) -> ServiceResponse:
        """Update data world"""
        try:
            if not world_name or not world_name.strip():
                return ServiceResponse.error_response("Nama world tidak boleh kosong")
            
            world_name = world_name.strip().upper()
            
            # Cek apakah world ada
            if not await self.world_repository.world_exists(world_name):
                return ServiceResponse.error_response(f"World {world_name} tidak ditemukan")
            
            # Normalize input jika ada
            if owner_name:
                owner_name = owner_name.strip()
            if bot_name:
                bot_name = bot_name.strip()
            
            success = await self.world_repository.update_world(world_name, owner_name, bot_name)
            if not success:
                return ServiceResponse.error_response("Gagal mengupdate world")
            
            logger.info(f"World {world_name} berhasil diupdate")
            
            # Return updated world data
            return await self.get_world(world_name)
            
        except Exception as e:
            logger.error(f"Error updating world {world_name}: {e}")
            return ServiceResponse.error_response("Terjadi error saat mengupdate world")
    
    async def delete_world(self, world_name: str) -> ServiceResponse:
        """Hapus world (soft delete)"""
        try:
            if not world_name or not world_name.strip():
                return ServiceResponse.error_response("Nama world tidak boleh kosong")
            
            world_name = world_name.strip().upper()
            
            # Cek apakah world ada
            if not await self.world_repository.world_exists(world_name):
                return ServiceResponse.error_response(f"World {world_name} tidak ditemukan")
            
            success = await self.world_repository.delete_world(world_name)
            if not success:
                return ServiceResponse.error_response("Gagal menghapus world")
            
            logger.info(f"World {world_name} berhasil dihapus")
            return ServiceResponse.success_response({"message": f"World {world_name} berhasil dihapus"})
            
        except Exception as e:
            logger.error(f"Error deleting world {world_name}: {e}")
            return ServiceResponse.error_response("Terjadi error saat menghapus world")
    
    async def world_exists(self, world_name: str) -> ServiceResponse:
        """Cek apakah world ada"""
        try:
            if not world_name or not world_name.strip():
                return ServiceResponse.error_response("Nama world tidak boleh kosong")
            
            world_name = world_name.strip().upper()
            exists = await self.world_repository.world_exists(world_name)
            
            return ServiceResponse.success_response({"exists": exists})
            
        except Exception as e:
            logger.error(f"Error checking world existence {world_name}: {e}")
            return ServiceResponse.error_response("Terjadi error saat mengecek world")
