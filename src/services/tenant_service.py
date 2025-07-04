"""
Tenant Service untuk Business Logic
Service untuk menangani operasi tenant dan konfigurasi
"""

import logging
import uuid
from datetime import datetime
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
