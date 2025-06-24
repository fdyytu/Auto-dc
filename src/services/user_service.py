"""
User Service
Menangani business logic untuk user management
"""

import logging
from typing import Optional, List
from src.database.connection import DatabaseManager
from src.database.models.user import User, UserGrowID
from src.database.models.balance import Balance
from src.services.base_service import BaseService, ServiceResponse

class UserService(BaseService):
    """Service untuk menangani operasi user"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.db = db_manager
    
    async def get_user_by_growid(self, growid: str) -> ServiceResponse:
        """Ambil user berdasarkan growid"""
        try:
            query = "SELECT * FROM users WHERE growid = ?"
            result = await self.db.execute_query(query, (growid,))
            
            if not result:
                return ServiceResponse.error_response(
                    error="User tidak ditemukan",
                    message=f"User dengan GrowID {growid} tidak ditemukan"
                )
            
            user_data = dict(result[0])
            user = User.from_dict(user_data)
            
            return ServiceResponse.success_response(
                data=user.to_dict(),
                message="User berhasil ditemukan"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil user berdasarkan GrowID")
    
    async def get_user_by_discord_id(self, discord_id: str) -> ServiceResponse:
        """Ambil user berdasarkan discord ID"""
        try:
            query = """
                SELECT u.*, ug.discord_id 
                FROM users u 
                JOIN user_growid ug ON u.growid = ug.growid 
                WHERE ug.discord_id = ?
            """
            result = await self.db.execute_query(query, (discord_id,))
            
            if not result:
                return ServiceResponse.error_response(
                    error="User tidak ditemukan",
                    message=f"User dengan Discord ID {discord_id} tidak ditemukan"
                )
            
            user_data = dict(result[0])
            user = User.from_dict(user_data)
            
            return ServiceResponse.success_response(
                data={
                    'user': user.to_dict(),
                    'discord_id': user_data['discord_id']
                },
                message="User berhasil ditemukan"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil user berdasarkan Discord ID")
    
    async def create_user(self, growid: str, discord_id: str) -> ServiceResponse:
        """Buat user baru"""
        try:
            # Cek apakah user sudah ada
            existing_user = await self.get_user_by_growid(growid)
            if existing_user.success:
                return ServiceResponse.error_response(
                    error="User sudah ada",
                    message=f"User dengan GrowID {growid} sudah terdaftar"
                )
            
            # Buat user baru
            user = User(growid=growid)
            user_query = """
                INSERT INTO users (growid, balance_wl, balance_dl, balance_bgl, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?)
            """
            user_params = (
                user.growid, user.balance_wl, user.balance_dl, user.balance_bgl,
                user.created_at.isoformat(), user.updated_at.isoformat()
            )
            
            if not await self.db.execute_update(user_query, user_params):
                return ServiceResponse.error_response(
                    error="Gagal membuat user",
                    message="Gagal menyimpan data user ke database"
                )
            
            # Link dengan discord ID
            user_growid = UserGrowID(discord_id=discord_id, growid=growid)
            link_query = "INSERT INTO user_growid (discord_id, growid, created_at) VALUES (?, ?, ?)"
            link_params = (user_growid.discord_id, user_growid.growid, user_growid.created_at.isoformat())
            
            if not await self.db.execute_update(link_query, link_params):
                return ServiceResponse.error_response(
                    error="Gagal menghubungkan Discord ID",
                    message="User dibuat tapi gagal menghubungkan dengan Discord ID"
                )
            
            return ServiceResponse.success_response(
                data={
                    'user': user.to_dict(),
                    'user_growid': user_growid.to_dict()
                },
                message=f"User {growid} berhasil dibuat dan dihubungkan dengan Discord ID {discord_id}"
            )
            
        except Exception as e:
            return self._handle_exception(e, "membuat user baru")
    
    async def update_balance(self, growid: str, balance_type: str, amount: int) -> ServiceResponse:
        """Update balance user"""
        try:
            if balance_type not in ['balance_wl', 'balance_dl', 'balance_bgl']:
                return ServiceResponse.error_response(
                    error="Tipe balance tidak valid",
                    message=f"Tipe balance {balance_type} tidak dikenali"
                )
            
            # Ambil user terlebih dahulu
            user_response = await self.get_user_by_growid(growid)
            if not user_response.success:
                return user_response
            
            query = f"""
                UPDATE users 
                SET {balance_type} = {balance_type} + ?, updated_at = ? 
                WHERE growid = ?
            """
            from datetime import datetime
            updated_at = datetime.utcnow().isoformat()
            
            success = await self.db.execute_update(query, (amount, updated_at, growid))
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal update balance",
                    message="Gagal mengupdate balance di database"
                )
            
            # Ambil balance terbaru
            updated_user = await self.get_user_by_growid(growid)
            
            return ServiceResponse.success_response(
                data=updated_user.data,
                message=f"Balance {balance_type} berhasil diupdate sebesar {amount}"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengupdate balance user")
    
    async def get_user_balance(self, growid: str) -> ServiceResponse:
        """Ambil balance user"""
        try:
            user_response = await self.get_user_by_growid(growid)
            if not user_response.success:
                return user_response
            
            user_data = user_response.data
            balance = Balance(
                wl=user_data['balance_wl'],
                dl=user_data['balance_dl'],
                bgl=user_data['balance_bgl']
            )
            
            return ServiceResponse.success_response(
                data={
                    'balance': {
                        'wl': balance.wl,
                        'dl': balance.dl,
                        'bgl': balance.bgl,
                        'total_wl': balance.total_wl(),
                        'formatted': balance.format()
                    }
                },
                message="Balance berhasil diambil"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil balance user")
    
    async def get_all_users(self) -> ServiceResponse:
        """Ambil semua user"""
        try:
            query = "SELECT * FROM users ORDER BY created_at DESC"
            result = await self.db.execute_query(query)
            
            if not result:
                return ServiceResponse.success_response(
                    data=[],
                    message="Tidak ada user yang ditemukan"
                )
            
            users = []
            for row in result:
                user_data = dict(row)
                user = User.from_dict(user_data)
                users.append(user.to_dict())
            
            return ServiceResponse.success_response(
                data=users,
                message=f"Berhasil mengambil {len(users)} user"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil semua user")
    
    async def delete_user(self, growid: str) -> ServiceResponse:
        """Hapus user (soft delete)"""
        try:
            # Cek apakah user ada
            user_response = await self.get_user_by_growid(growid)
            if not user_response.success:
                return user_response
            
            # Hapus mapping discord ID terlebih dahulu
            delete_mapping_query = "DELETE FROM user_growid WHERE growid = ?"
            await self.db.execute_update(delete_mapping_query, (growid,))
            
            # Hapus user
            delete_user_query = "DELETE FROM users WHERE growid = ?"
            success = await self.db.execute_update(delete_user_query, (growid,))
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal menghapus user",
                    message="Gagal menghapus user dari database"
                )
            
            return ServiceResponse.success_response(
                data={"growid": growid},
                message=f"User {growid} berhasil dihapus"
            )
            
        except Exception as e:
            return self._handle_exception(e, "menghapus user")
    
    async def log_user_activity(self, discord_id: str, activity_type: str, details: str = None) -> ServiceResponse:
        """Log aktivitas user"""
        try:
            from datetime import datetime
            query = """
                INSERT INTO user_activity (discord_id, activity_type, details, created_at) 
                VALUES (?, ?, ?, ?)
            """
            created_at = datetime.utcnow().isoformat()
            success = await self.db.execute_update(query, (discord_id, activity_type, details, created_at))
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal log aktivitas",
                    message="Gagal menyimpan log aktivitas user"
                )
            
            return ServiceResponse.success_response(
                data={
                    'discord_id': discord_id,
                    'activity_type': activity_type,
                    'details': details
                },
                message="Aktivitas user berhasil dicatat"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mencatat aktivitas user")
