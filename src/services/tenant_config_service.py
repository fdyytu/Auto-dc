"""
Tenant Config Service untuk Konfigurasi Fleksibel
Service untuk menangani konfigurasi tenant yang dinamis
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from src.database.connection import DatabaseManager
from src.database.repositories.tenant_repository import TenantRepository
from src.database.repositories.tenant_product_repository import TenantProductRepository
from src.services.base_service import BaseService, ServiceResponse

logger = logging.getLogger(__name__)

class TenantConfigService(BaseService):
    """Service untuk konfigurasi tenant"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.tenant_repo = TenantRepository(db_manager)
        self.product_repo = TenantProductRepository(db_manager)
    
    async def update_channels(self, tenant_id: str, channels: Dict[str, str]) -> ServiceResponse:
        """Update channel configuration untuk tenant"""
        try:
            tenant = await self.tenant_repo.get_tenant_by_id(tenant_id)
            if not tenant:
                return ServiceResponse.error_response(
                    error="Tenant tidak ditemukan",
                    message=f"Tenant {tenant_id} tidak ditemukan"
                )
            
            # Validasi channel IDs
            valid_channels = ['live_stock', 'purchase_log', 'donation_log', 'ticket_category']
            for channel_key in channels.keys():
                if channel_key not in valid_channels:
                    return ServiceResponse.error_response(
                        error="Channel tidak valid",
                        message=f"Channel {channel_key} tidak dikenali"
                    )
            
            # Update channels
            tenant.channels.update(channels)
            tenant.updated_at = datetime.utcnow()
            
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
                    error="Gagal update channels",
                    message="Gagal menyimpan konfigurasi channel"
                )
            
            return ServiceResponse.success_response(
                data={'channels': tenant.channels},
                message="Konfigurasi channel berhasil diupdate"
            )
            
        except Exception as e:
            return self._handle_exception(e, "update channel configuration")
    
    async def update_permissions(self, tenant_id: str, permissions: Dict[str, bool]) -> ServiceResponse:
        """Update permissions untuk tenant"""
        try:
            tenant = await self.tenant_repo.get_tenant_by_id(tenant_id)
            if not tenant:
                return ServiceResponse.error_response(
                    error="Tenant tidak ditemukan",
                    message=f"Tenant {tenant_id} tidak ditemukan"
                )
            
            # Update permissions
            tenant.permissions.update(permissions)
            tenant.updated_at = datetime.utcnow()
            
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
                    error="Gagal update permissions",
                    message="Gagal menyimpan permissions"
                )
            
            return ServiceResponse.success_response(
                data={'permissions': tenant.permissions},
                message="Permissions berhasil diupdate"
            )
            
        except Exception as e:
            return self._handle_exception(e, "update permissions")
    
    async def sync_tenant_data(self, tenant_id: str) -> ServiceResponse:
        """Sinkronisasi data tenant dengan database utama"""
        try:
            # Ambil konfigurasi tenant
            tenant = await self.tenant_repo.get_tenant_by_id(tenant_id)
            if not tenant:
                return ServiceResponse.error_response(
                    error="Tenant tidak ditemukan",
                    message=f"Tenant {tenant_id} tidak ditemukan"
                )
            
            # Ambil produk tenant
            products = await self.product_repo.get_products_by_tenant(tenant_id)
            
            sync_data = {
                'tenant_config': tenant.to_dict(),
                'products_count': len(products),
                'last_sync': datetime.utcnow().isoformat()
            }
            
            return ServiceResponse.success_response(
                data=sync_data,
                message="Data tenant berhasil disinkronisasi"
            )
            
        except Exception as e:
            return self._handle_exception(e, "sinkronisasi data tenant")
