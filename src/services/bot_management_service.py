"""
Bot Management Service untuk Bot Rental System
Menangani business logic untuk manajemen bot instances
"""

import logging
import subprocess
import psutil
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.database.connection import DatabaseManager
from src.database.models.bot_instance import BotInstance, BotStatus
from src.services.base_service import BaseService, ServiceResponse

class BotManagementService(BaseService):
    """Service untuk menangani operasi bot instances"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.db = db_manager
        self.base_port = 8000  # Port dasar untuk bot instances
    
    async def create_bot_instance(self, tenant_id: str, bot_token: str, guild_id: str) -> ServiceResponse:
        """Buat bot instance baru"""
        try:
            # Cari port yang tersedia
            port = await self._find_available_port()
            
            bot_instance = BotInstance(
                tenant_id=tenant_id,
                bot_token=bot_token,
                guild_id=guild_id,
                status=BotStatus.STOPPED,
                port=port
            )
            
            # Simpan ke database
            query = """
                INSERT INTO bot_instances 
                (tenant_id, bot_token, guild_id, status, port, config, restart_count, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                bot_instance.tenant_id,
                bot_instance.bot_token,
                bot_instance.guild_id,
                bot_instance.status.value,
                bot_instance.port,
                str(bot_instance.config),
                bot_instance.restart_count,
                bot_instance.created_at.isoformat(),
                bot_instance.updated_at.isoformat()
            )
            
            if not await self.db.execute_update(query, params):
                return ServiceResponse.error_response(
                    error="Gagal membuat bot instance",
                    message="Gagal menyimpan bot instance ke database"
                )
            
            return ServiceResponse.success_response(
                data=bot_instance.to_dict(),
                message=f"Bot instance untuk tenant {tenant_id} berhasil dibuat"
            )
            
        except Exception as e:
            return self._handle_exception(e, "membuat bot instance")
    
    async def start_bot_instance(self, tenant_id: str) -> ServiceResponse:
        """Start bot instance untuk tenant"""
        try:
            # Ambil bot instance dari database
            instance_response = await self.get_bot_instance_by_tenant(tenant_id)
            if not instance_response.success:
                return instance_response
            
            bot_instance = BotInstance.from_dict(instance_response.data)
            
            if bot_instance.is_running():
                return ServiceResponse.error_response(
                    error="Bot sudah berjalan",
                    message=f"Bot instance untuk tenant {tenant_id} sudah berjalan"
                )
            
            # Update status ke starting
            await self._update_bot_status(tenant_id, BotStatus.STARTING.value)
            
            # Start bot process
            process_id = await self._start_bot_process(bot_instance)
            
            if process_id:
                # Update database dengan process ID dan status running
                query = """
                    UPDATE bot_instances 
                    SET process_id = ?, status = ?, last_heartbeat = ?, updated_at = ? 
                    WHERE tenant_id = ?
                """
                params = (
                    process_id,
                    BotStatus.RUNNING.value,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    tenant_id
                )
                
                await self.db.execute_update(query, params)
                
                return ServiceResponse.success_response(
                    data={"tenant_id": tenant_id, "process_id": process_id},
                    message=f"Bot instance untuk tenant {tenant_id} berhasil distart"
                )
            else:
                await self._update_bot_status(tenant_id, BotStatus.ERROR.value, "Gagal start process")
                return ServiceResponse.error_response(
                    error="Gagal start bot",
                    message="Gagal menjalankan bot process"
                )
            
        except Exception as e:
            await self._update_bot_status(tenant_id, BotStatus.ERROR.value, str(e))
            return self._handle_exception(e, "start bot instance")
    
    async def stop_bot_instance(self, tenant_id: str) -> ServiceResponse:
        """Stop bot instance untuk tenant"""
        try:
            # Ambil bot instance dari database
            instance_response = await self.get_bot_instance_by_tenant(tenant_id)
            if not instance_response.success:
                return instance_response
            
            bot_instance = BotInstance.from_dict(instance_response.data)
            
            if not bot_instance.is_running() or not bot_instance.process_id:
                return ServiceResponse.error_response(
                    error="Bot tidak berjalan",
                    message=f"Bot instance untuk tenant {tenant_id} tidak berjalan"
                )
            
            # Stop bot process
            success = await self._stop_bot_process(bot_instance.process_id)
            
            if success:
                # Update database
                query = """
                    UPDATE bot_instances 
                    SET process_id = NULL, status = ?, updated_at = ? 
                    WHERE tenant_id = ?
                """
                params = (
                    BotStatus.STOPPED.value,
                    datetime.utcnow().isoformat(),
                    tenant_id
                )
                
                await self.db.execute_update(query, params)
                
                return ServiceResponse.success_response(
                    data={"tenant_id": tenant_id},
                    message=f"Bot instance untuk tenant {tenant_id} berhasil dihentikan"
                )
            else:
                return ServiceResponse.error_response(
                    error="Gagal stop bot",
                    message="Gagal menghentikan bot process"
                )
            
        except Exception as e:
            return self._handle_exception(e, "stop bot instance")
    
    async def get_bot_instance_by_tenant(self, tenant_id: str) -> ServiceResponse:
        """Ambil bot instance berdasarkan tenant ID"""
        try:
            query = "SELECT * FROM bot_instances WHERE tenant_id = ?"
            result = await self.db.execute_query(query, (tenant_id,))
            
            if not result:
                return ServiceResponse.error_response(
                    error="Bot instance tidak ditemukan",
                    message=f"Tidak ada bot instance untuk tenant {tenant_id}"
                )
            
            instance_data = dict(result[0])
            # Parse config string back to dict
            import ast
            try:
                instance_data['config'] = ast.literal_eval(instance_data['config'])
            except:
                instance_data['config'] = {}
            
            bot_instance = BotInstance.from_dict(instance_data)
            
            return ServiceResponse.success_response(
                data=bot_instance.to_dict(),
                message="Bot instance berhasil ditemukan"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil bot instance")
    
    async def _find_available_port(self) -> int:
        """Cari port yang tersedia"""
        for port in range(self.base_port, self.base_port + 1000):
            if not self._is_port_in_use(port):
                return port
        raise Exception("Tidak ada port yang tersedia")
    
    def _is_port_in_use(self, port: int) -> bool:
        """Cek apakah port sedang digunakan"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    async def _start_bot_process(self, bot_instance: BotInstance) -> Optional[int]:
        """Start bot process dan return process ID"""
        try:
            # Command untuk menjalankan bot dengan konfigurasi tenant
            cmd = [
                'python3', 'main.py',
                '--tenant-id', bot_instance.tenant_id,
                '--token', bot_instance.bot_token,
                '--guild-id', bot_instance.guild_id,
                '--port', str(bot_instance.port)
            ]
            
            # Start process di background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd='/home/user/workspace'
            )
            
            return process.pid
            
        except Exception as e:
            logging.error(f"Gagal start bot process: {e}")
            return None
    
    async def _stop_bot_process(self, process_id: int) -> bool:
        """Stop bot process"""
        try:
            if psutil.pid_exists(process_id):
                process = psutil.Process(process_id)
                process.terminate()
                process.wait(timeout=10)
                return True
            return True  # Process sudah tidak ada
            
        except Exception as e:
            logging.error(f"Gagal stop bot process {process_id}: {e}")
            return False
    
    async def _update_bot_status(self, tenant_id: str, status: str, error_message: str = None):
        """Update status bot instance"""
        query = "UPDATE bot_instances SET status = ?, updated_at = ?"
        params = [status, datetime.utcnow().isoformat()]
        
        if error_message:
            query += ", error_message = ?"
            params.append(error_message)
        
        query += " WHERE tenant_id = ?"
        params.append(tenant_id)
        
        await self.db.execute_update(query, tuple(params))
