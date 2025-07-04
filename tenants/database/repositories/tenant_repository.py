"""
Tenant Repository untuk Database Operations
Repository untuk operasi CRUD tenant
"""

import logging
from typing import Optional, List, Dict, Any
from tenants.database.connection import DatabaseManager
from tenants.database.models.tenant import Tenant, TenantStatus, SubscriptionPlan
import json

logger = logging.getLogger(__name__)

class TenantRepository:
    """Repository untuk operasi database tenant"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_tenant(self, tenant: Tenant) -> bool:
        """Buat tenant baru"""
        try:
            query = """
                INSERT INTO tenants 
                (tenant_id, discord_id, guild_id, name, status, plan, features, 
                 channels, permissions, bot_config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                tenant.tenant_id,
                tenant.discord_id,
                tenant.guild_id,
                tenant.name,
                tenant.status.value,
                tenant.plan.value,
                json.dumps(tenant.features),
                json.dumps(tenant.channels),
                json.dumps(tenant.permissions),
                json.dumps(tenant.bot_config),
                tenant.created_at.isoformat(),
                tenant.updated_at.isoformat()
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            logger.error(f"Error creating tenant: {e}")
            return False
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Ambil tenant berdasarkan ID"""
        try:
            query = "SELECT * FROM tenants WHERE tenant_id = ?"
            result = await self.db.execute_query(query, (tenant_id,))
            
            if result:
                return self._row_to_tenant(dict(result[0]))
            return None
            
        except Exception as e:
            logger.error(f"Error getting tenant by ID: {e}")
            return None
    
    async def get_tenant_by_discord_id(self, discord_id: str) -> Optional[Tenant]:
        """Ambil tenant berdasarkan Discord ID"""
        try:
            query = "SELECT * FROM tenants WHERE discord_id = ?"
            result = await self.db.execute_query(query, (discord_id,))
            
            if result:
                return self._row_to_tenant(dict(result[0]))
            return None
            
        except Exception as e:
            logger.error(f"Error getting tenant by Discord ID: {e}")
            return None
    
    async def update_tenant_config(self, tenant_id: str, config_data: Dict[str, Any]) -> bool:
        """Update konfigurasi tenant"""
        try:
            query = """
                UPDATE tenants 
                SET features = ?, channels = ?, permissions = ?, bot_config = ?, updated_at = ?
                WHERE tenant_id = ?
            """
            params = (
                json.dumps(config_data.get('features', {})),
                json.dumps(config_data.get('channels', {})),
                json.dumps(config_data.get('permissions', {})),
                json.dumps(config_data.get('bot_config', {})),
                config_data.get('updated_at'),
                tenant_id
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            logger.error(f"Error updating tenant config: {e}")
            return False
    
    def _row_to_tenant(self, row: Dict[str, Any]) -> Tenant:
        """Convert database row ke Tenant object"""
        return Tenant(
            id=row.get('id'),
            tenant_id=row.get('tenant_id', ''),
            discord_id=row.get('discord_id', ''),
            guild_id=row.get('guild_id', ''),
            name=row.get('name', ''),
            status=TenantStatus(row.get('status', 'active')),
            plan=SubscriptionPlan(row.get('plan', 'basic')),
            features=json.loads(row.get('features', '{}')),
            channels=json.loads(row.get('channels', '{}')),
            permissions=json.loads(row.get('permissions', '{}')),
            bot_config=json.loads(row.get('bot_config', '{}')),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
