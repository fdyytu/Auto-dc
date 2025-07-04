"""
Tenant Service untuk Business Logic
Service untuk menangani operasi tenant dan konfigurasi
"""

import logging
import uuid
import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from src.database.connection import DatabaseManager
from src.database.repositories.tenant_repository import TenantRepository
from src.database.models.tenant import Tenant, TenantStatus, SubscriptionPlan
from src.services.base_service import BaseService, ServiceResponse

logger = logging.getLogger(__name__)

class TenantService(BaseService):
    """Service untuk menangani operasi tenant"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.tenant_repo = TenantRepository(db_manager)
    
    async def create_tenant(self, discord_id: str, guild_id: str, name: str, 
                          plan: str = "basic") -> ServiceResponse:
        """Buat tenant baru"""
        try:
            # Generate tenant ID unik
            tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
            
            # Cek apakah discord_id sudah memiliki tenant
            existing_tenant = await self.tenant_repo.get_tenant_by_discord_id(discord_id)
            if existing_tenant:
                return ServiceResponse.error_response(
                    error="Tenant sudah ada",
                    message=f"Discord ID {discord_id} sudah memiliki tenant"
                )
            
            # Buat tenant baru
            tenant = Tenant(
                tenant_id=tenant_id,
                discord_id=discord_id,
                guild_id=guild_id,
                name=name,
                plan=SubscriptionPlan(plan),
                status=TenantStatus.ACTIVE
            )
            
            # Simpan ke database
            success = await self.tenant_repo.create_tenant(tenant)
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal membuat tenant",
                    message="Gagal menyimpan tenant ke database"
                )
            
            return ServiceResponse.success_response(
                data=tenant.to_dict(),
                message=f"Tenant {tenant_id} berhasil dibuat"
            )
            
        except Exception as e:
            return self._handle_exception(e, "membuat tenant")
    
    async def get_tenant_config(self, tenant_id: str) -> ServiceResponse:
        """Ambil konfigurasi tenant"""
        try:
            tenant = await self.tenant_repo.get_tenant_by_id(tenant_id)
            if not tenant:
                return ServiceResponse.error_response(
                    error="Tenant tidak ditemukan",
                    message=f"Tenant {tenant_id} tidak ditemukan"
                )
            
            return ServiceResponse.success_response(
                data=tenant.to_dict(),
                message="Konfigurasi tenant berhasil diambil"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil konfigurasi tenant")
    
    async def update_tenant_features(self, tenant_id: str, features: Dict[str, bool]) -> ServiceResponse:
        """Update fitur tenant"""
        try:
            tenant = await self.tenant_repo.get_tenant_by_id(tenant_id)
            if not tenant:
                return ServiceResponse.error_response(
                    error="Tenant tidak ditemukan",
                    message=f"Tenant {tenant_id} tidak ditemukan"
                )
            
            # Update features
            tenant.features.update(features)
            tenant.updated_at = datetime.utcnow()
            
            # Simpan ke database
            config_data = {
                'features': tenant.features,
                'channels': tenant.channels,
                'permissions': tenant.permissions,
                'bot_config': tenant.bot_config,
                'updated_at': tenant.updated_at.isoformat()
            }
            
            success = await self.tenant_repo.update_tenant_config(tenant_id, config_data)
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal update fitur",
                    message="Gagal menyimpan perubahan fitur"
                )
            
            return ServiceResponse.success_response(
                data={'features': tenant.features},
                message="Fitur tenant berhasil diupdate"
            )
            
        except Exception as e:
            return self._handle_exception(e, "update fitur tenant")
    
    def _get_tenant_folder_path(self, tenant_id: str) -> Path:
        """Dapatkan path folder tenant"""
        return Path("tenants/active") / tenant_id
    
    def _get_template_folder_path(self) -> Path:
        """Dapatkan path folder template"""
        return Path("tenants/template")
    
    async def create_tenant_folder_structure(self, tenant_id: str, discord_id: str, 
                                           guild_id: str, bot_token: str) -> ServiceResponse:
        """Buat struktur folder untuk tenant baru"""
        try:
            tenant_path = self._get_tenant_folder_path(tenant_id)
            template_path = self._get_template_folder_path()
            
            # Cek apakah folder tenant sudah ada
            if tenant_path.exists():
                return ServiceResponse.error_response(
                    error="Folder tenant sudah ada",
                    message=f"Folder untuk tenant {tenant_id} sudah ada"
                )
            
            # Cek apakah template ada
            if not template_path.exists():
                return ServiceResponse.error_response(
                    error="Template tidak ditemukan",
                    message="Folder template tidak ditemukan"
                )
            
            # Salin struktur dari template
            shutil.copytree(template_path, tenant_path)
            
            # Update konfigurasi tenant
            config_path = tenant_path / "config" / "tenant_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Update informasi tenant
                config['tenant_info']['tenant_id'] = tenant_id
                config['tenant_info']['discord_id'] = discord_id
                config['tenant_info']['guild_id'] = guild_id
                config['tenant_info']['bot_token'] = bot_token
                config['tenant_info']['created_at'] = datetime.utcnow().isoformat()
                config['tenant_info']['status'] = "active"
                
                # Simpan konfigurasi yang sudah diupdate
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"✅ Struktur folder tenant {tenant_id} berhasil dibuat")
            
            return ServiceResponse.success_response(
                data={'tenant_path': str(tenant_path)},
                message=f"Struktur folder tenant {tenant_id} berhasil dibuat"
            )
            
        except Exception as e:
            logger.error(f"Error creating tenant folder structure: {e}")
            return ServiceResponse.error_response(
                error="Gagal membuat struktur folder",
                message=f"Error: {str(e)}"
            )
    
    async def remove_tenant_folder_structure(self, tenant_id: str) -> ServiceResponse:
        """Hapus struktur folder tenant"""
        try:
            tenant_path = self._get_tenant_folder_path(tenant_id)
            
            if not tenant_path.exists():
                return ServiceResponse.error_response(
                    error="Folder tenant tidak ditemukan",
                    message=f"Folder untuk tenant {tenant_id} tidak ditemukan"
                )
            
            # Backup sebelum hapus (opsional)
            backup_path = Path("tenants/backups") / f"{tenant_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(tenant_path), str(backup_path))
            
            logger.info(f"✅ Folder tenant {tenant_id} berhasil dihapus dan dibackup ke {backup_path}")
            
            return ServiceResponse.success_response(
                data={'backup_path': str(backup_path)},
                message=f"Folder tenant {tenant_id} berhasil dihapus dan dibackup"
            )
            
        except Exception as e:
            logger.error(f"Error removing tenant folder structure: {e}")
            return ServiceResponse.error_response(
                error="Gagal menghapus struktur folder",
                message=f"Error: {str(e)}"
            )
    
    async def get_tenant_config_from_file(self, tenant_id: str) -> ServiceResponse:
        """Ambil konfigurasi tenant dari file"""
        try:
            config_path = self._get_tenant_folder_path(tenant_id) / "config" / "tenant_config.json"
            
            if not config_path.exists():
                return ServiceResponse.error_response(
                    error="File konfigurasi tidak ditemukan",
                    message=f"File konfigurasi untuk tenant {tenant_id} tidak ditemukan"
                )
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            return ServiceResponse.success_response(
                data=config,
                message="Konfigurasi tenant berhasil diambil dari file"
            )
            
        except Exception as e:
            logger.error(f"Error getting tenant config from file: {e}")
            return ServiceResponse.error_response(
                error="Gagal membaca konfigurasi",
                message=f"Error: {str(e)}"
            )
