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

    async def get_tenant_configuration(self, tenant_id: str) -> ServiceResponse:
        """Ambil konfigurasi tenant dari database tenant_configurations"""
        try:
            query = "SELECT * FROM tenant_configurations WHERE tenant_id = ?"
            result = await self.db_manager.execute_query(query, (tenant_id,))
            if not result:
                return ServiceResponse.error_response(
                    error="Konfigurasi tenant tidak ditemukan",
                    message=f"Konfigurasi untuk tenant {tenant_id} tidak ditemukan"
                )
            row = result[0]
            config = {
                "tenant_id": row["tenant_id"],
                "bot_token": row["bot_token"],
                "donation_channel_id": row["donation_channel_id"],
                "other_channel_ids": row["other_channel_ids"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            return ServiceResponse.success_response(data=config, message="Konfigurasi tenant berhasil diambil")
        except Exception as e:
            return self._handle_exception(e, "mengambil konfigurasi tenant dari database")

    async def update_tenant_configuration(self, tenant_id: str, config_data: Dict[str, Any]) -> ServiceResponse:
        """Update konfigurasi tenant di database tenant_configurations"""
        try:
            now = datetime.utcnow().isoformat()
            query_check = "SELECT id FROM tenant_configurations WHERE tenant_id = ?"
            result = await self.db_manager.execute_query(query_check, (tenant_id,))
            if result:
                query_update = """
                    UPDATE tenant_configurations
                    SET bot_token = ?, donation_channel_id = ?, other_channel_ids = ?, updated_at = ?
                    WHERE tenant_id = ?
                """
                await self.db_manager.execute_update(query_update, (
                    config_data.get("bot_token"),
                    config_data.get("donation_channel_id"),
                    config_data.get("other_channel_ids"),
                    now,
                    tenant_id
                ))
            else:
                query_insert = """
                    INSERT INTO tenant_configurations
                    (tenant_id, bot_token, donation_channel_id, other_channel_ids, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                await self.db_manager.execute_update(query_insert, (
                    tenant_id,
                    config_data.get("bot_token"),
                    config_data.get("donation_channel_id"),
                    config_data.get("other_channel_ids"),
                    now,
                    now
                ))
            return ServiceResponse.success_response(message="Konfigurasi tenant berhasil diupdate")
        except Exception as e:
            return self._handle_exception(e, "mengupdate konfigurasi tenant di database")
    
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
