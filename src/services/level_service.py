"""
Level Service
Menangani business logic untuk level management
"""

import logging
from typing import Optional, List
from src.database.connection import DatabaseManager
from src.database.models.level import Level, LevelReward, LevelSettings
from src.services.base_service import BaseService, ServiceResponse

class LevelService(BaseService):
    """Service untuk menangani operasi level"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.db = db_manager
    
    # Level Operations
    async def get_user_level(self, user_id: str, guild_id: str) -> ServiceResponse:
        """Ambil level user di guild tertentu"""
        try:
            query = "SELECT * FROM levels WHERE user_id = ? AND guild_id = ?"
            result = await self.db.execute_query(query, (user_id, guild_id))
            
            if not result:
                return ServiceResponse.error_response(
                    error="Level user tidak ditemukan",
                    message=f"Level untuk user {user_id} di guild {guild_id} tidak ditemukan"
                )
            
            level_data = dict(result[0])
            level = Level.from_dict(level_data)
            
            return ServiceResponse.success_response(
                data=level.to_dict(),
                message="Level user berhasil ditemukan"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil level user")
    
    async def create_user_level(self, user_id: str, guild_id: str) -> ServiceResponse:
        """Buat level baru untuk user"""
        try:
            # Cek apakah level user sudah ada
            existing_level = await self.get_user_level(user_id, guild_id)
            if existing_level.success:
                return ServiceResponse.error_response(
                    error="Level user sudah ada",
                    message=f"Level untuk user {user_id} di guild {guild_id} sudah ada"
                )
            
            # Buat level baru
            level = Level(user_id=user_id, guild_id=guild_id)
            
            query = """
                INSERT INTO levels (user_id, guild_id, level, xp, total_xp, messages, last_message, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                level.user_id, level.guild_id, level.level, level.xp, level.total_xp,
                level.messages, level.last_message.isoformat(), 
                level.created_at.isoformat(), level.updated_at.isoformat()
            )
            
            success = await self.db.execute_update(query, params)
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal membuat level user",
                    message="Gagal menyimpan level user ke database"
                )
            
            return ServiceResponse.success_response(
                data=level.to_dict(),
                message=f"Level untuk user {user_id} berhasil dibuat"
            )
            
        except Exception as e:
            return self._handle_exception(e, "membuat level user")
    
    async def update_user_xp(self, user_id: str, guild_id: str, xp_gain: int) -> ServiceResponse:
        """Update XP user dan cek level up"""
        try:
            # Ambil level user saat ini
            level_response = await self.get_user_level(user_id, guild_id)
            if not level_response.success:
                # Buat level baru jika belum ada
                create_response = await self.create_user_level(user_id, guild_id)
                if not create_response.success:
                    return create_response
                level_response = await self.get_user_level(user_id, guild_id)
            
            level_data = level_response.data
            current_level = level_data['level']
            current_xp = level_data['xp']
            current_total_xp = level_data['total_xp']
            current_messages = level_data['messages']
            
            # Hitung XP dan level baru
            new_xp = current_xp + xp_gain
            new_total_xp = current_total_xp + xp_gain
            new_messages = current_messages + 1
            new_level = current_level
            
            # Cek level up (asumsi: 100 XP per level)
            xp_per_level = 100
            while new_xp >= xp_per_level:
                new_xp -= xp_per_level
                new_level += 1
            
            # Update database
            from datetime import datetime
            query = """
                UPDATE levels 
                SET level = ?, xp = ?, total_xp = ?, messages = ?, last_message = ?, updated_at = ?
                WHERE user_id = ? AND guild_id = ?
            """
            now = datetime.utcnow()
            params = (
                new_level, new_xp, new_total_xp, new_messages, 
                now.isoformat(), now.isoformat(), user_id, guild_id
            )
            
            success = await self.db.execute_update(query, params)
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal update XP user",
                    message="Gagal mengupdate XP user di database"
                )
            
            # Return updated level data
            updated_level_response = await self.get_user_level(user_id, guild_id)
            
            # Tambahkan informasi level up
            level_up = new_level > current_level
            updated_level_response.data['level_up'] = level_up
            updated_level_response.data['levels_gained'] = new_level - current_level
            
            return ServiceResponse.success_response(
                data=updated_level_response.data,
                message=f"XP user berhasil diupdate. {'Level up!' if level_up else 'Tidak ada level up.'}"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengupdate XP user")
    
    async def get_guild_leaderboard(self, guild_id: str, limit: int = 10) -> ServiceResponse:
        """Ambil leaderboard guild"""
        try:
            query = """
                SELECT * FROM levels 
                WHERE guild_id = ? 
                ORDER BY total_xp DESC, level DESC 
                LIMIT ?
            """
            result = await self.db.execute_query(query, (guild_id, limit))
            
            if not result:
                return ServiceResponse.success_response(
                    data=[],
                    message="Tidak ada data level di guild ini"
                )
            
            leaderboard = []
            for i, row in enumerate(result, 1):
                level_data = dict(row)
                level = Level.from_dict(level_data)
                level_dict = level.to_dict()
                level_dict['rank'] = i
                leaderboard.append(level_dict)
            
            return ServiceResponse.success_response(
                data=leaderboard,
                message=f"Berhasil mengambil leaderboard top {len(leaderboard)}"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil leaderboard guild")
    
    # Level Reward Operations
    async def get_level_rewards(self, guild_id: str) -> ServiceResponse:
        """Ambil semua level rewards untuk guild"""
        try:
            query = "SELECT * FROM level_rewards WHERE guild_id = ? ORDER BY level ASC"
            result = await self.db.execute_query(query, (guild_id,))
            
            if not result:
                return ServiceResponse.success_response(
                    data=[],
                    message="Tidak ada level reward yang dikonfigurasi"
                )
            
            rewards = []
            for row in result:
                reward_data = dict(row)
                reward = LevelReward.from_dict(reward_data)
                rewards.append(reward.to_dict())
            
            return ServiceResponse.success_response(
                data=rewards,
                message=f"Berhasil mengambil {len(rewards)} level reward"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil level rewards")
    
    async def add_level_reward(self, guild_id: str, level: int, role_id: str) -> ServiceResponse:
        """Tambah level reward"""
        try:
            # Cek apakah reward untuk level ini sudah ada
            query = "SELECT * FROM level_rewards WHERE guild_id = ? AND level = ?"
            result = await self.db.execute_query(query, (guild_id, level))
            
            if result:
                return ServiceResponse.error_response(
                    error="Level reward sudah ada",
                    message=f"Reward untuk level {level} sudah dikonfigurasi"
                )
            
            # Validasi input
            if level < 1:
                return ServiceResponse.error_response(
                    error="Level tidak valid",
                    message="Level harus lebih dari 0"
                )
            
            # Buat level reward baru
            reward = LevelReward(guild_id=guild_id, level=level, role_id=role_id)
            
            insert_query = """
                INSERT INTO level_rewards (guild_id, level, role_id, created_at) 
                VALUES (?, ?, ?, ?)
            """
            params = (reward.guild_id, reward.level, reward.role_id, reward.created_at.isoformat())
            
            success = await self.db.execute_update(insert_query, params)
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal menambah level reward",
                    message="Gagal menyimpan level reward ke database"
                )
            
            return ServiceResponse.success_response(
                data=reward.to_dict(),
                message=f"Level reward untuk level {level} berhasil ditambahkan"
            )
            
        except Exception as e:
            return self._handle_exception(e, "menambah level reward")
    
    async def remove_level_reward(self, guild_id: str, level: int) -> ServiceResponse:
        """Hapus level reward"""
        try:
            # Cek apakah reward ada
            query = "SELECT * FROM level_rewards WHERE guild_id = ? AND level = ?"
            result = await self.db.execute_query(query, (guild_id, level))
            
            if not result:
                return ServiceResponse.error_response(
                    error="Level reward tidak ditemukan",
                    message=f"Reward untuk level {level} tidak ditemukan"
                )
            
            # Hapus reward
            delete_query = "DELETE FROM level_rewards WHERE guild_id = ? AND level = ?"
            success = await self.db.execute_update(delete_query, (guild_id, level))
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal menghapus level reward",
                    message="Gagal menghapus level reward dari database"
                )
            
            return ServiceResponse.success_response(
                data={"guild_id": guild_id, "level": level},
                message=f"Level reward untuk level {level} berhasil dihapus"
            )
            
        except Exception as e:
            return self._handle_exception(e, "menghapus level reward")
    
    # Level Settings Operations
    async def get_level_settings(self, guild_id: str) -> ServiceResponse:
        """Ambil pengaturan level untuk guild"""
        try:
            query = "SELECT * FROM level_settings WHERE guild_id = ?"
            result = await self.db.execute_query(query, (guild_id,))
            
            if not result:
                # Buat pengaturan default jika belum ada
                return await self.create_default_level_settings(guild_id)
            
            settings_data = dict(result[0])
            settings = LevelSettings.from_dict(settings_data)
            
            return ServiceResponse.success_response(
                data=settings.to_dict(),
                message="Pengaturan level berhasil ditemukan"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil pengaturan level")
    
    async def create_default_level_settings(self, guild_id: str) -> ServiceResponse:
        """Buat pengaturan level default"""
        try:
            settings = LevelSettings(guild_id=guild_id)
            
            query = """
                INSERT INTO level_settings (
                    guild_id, enabled, announcement_channel, min_xp, max_xp, cooldown,
                    stack_rewards, ignored_channels, ignored_roles, double_xp_roles,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                settings.guild_id, settings.enabled, settings.announcement_channel,
                settings.min_xp, settings.max_xp, settings.cooldown, settings.stack_rewards,
                settings.ignored_channels, settings.ignored_roles, settings.double_xp_roles,
                settings.created_at.isoformat(), settings.updated_at.isoformat()
            )
            
            success = await self.db.execute_update(query, params)
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal membuat pengaturan level",
                    message="Gagal menyimpan pengaturan level ke database"
                )
            
            return ServiceResponse.success_response(
                data=settings.to_dict(),
                message="Pengaturan level default berhasil dibuat"
            )
            
        except Exception as e:
            return self._handle_exception(e, "membuat pengaturan level default")
    
    async def update_level_settings(self, guild_id: str, **kwargs) -> ServiceResponse:
        """Update pengaturan level"""
        try:
            # Cek apakah settings ada
            settings_response = await self.get_level_settings(guild_id)
            if not settings_response.success:
                return settings_response
            
            allowed_fields = [
                'enabled', 'announcement_channel', 'min_xp', 'max_xp', 'cooldown',
                'stack_rewards', 'ignored_channels', 'ignored_roles', 'double_xp_roles'
            ]
            
            updates = []
            params = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = ?")
                    params.append(value)
            
            if not updates:
                return ServiceResponse.error_response(
                    error="Tidak ada field yang diupdate",
                    message="Tidak ada perubahan yang valid untuk diupdate"
                )
            
            from datetime import datetime
            updates.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(guild_id)
            
            query = f"UPDATE level_settings SET {', '.join(updates)} WHERE guild_id = ?"
            success = await self.db.execute_update(query, tuple(params))
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal update pengaturan level",
                    message="Gagal mengupdate pengaturan level di database"
                )
            
            # Return updated settings
            return await self.get_level_settings(guild_id)
            
        except Exception as e:
            return self._handle_exception(e, "mengupdate pengaturan level")
