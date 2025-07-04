"""
Tenant Product Repository untuk Database Operations
Repository untuk operasi CRUD produk dan stock per tenant
"""

import logging
from typing import Optional, List, Dict, Any
from tenants.database.connection import DatabaseManager
from tenants.database.models.tenant_product import TenantProduct, TenantStock, TenantStockStatus

logger = logging.getLogger(__name__)

class TenantProductRepository:
    """Repository untuk operasi database produk tenant"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_product(self, product: TenantProduct) -> bool:
        """Buat produk baru untuk tenant"""
        try:
            query = """
                INSERT INTO tenant_products 
                (tenant_id, code, name, price, description, category, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                product.tenant_id,
                product.code,
                product.name,
                product.price,
                product.description,
                product.category,
                product.is_active,
                product.created_at.isoformat(),
                product.updated_at.isoformat()
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            logger.error(f"Error creating tenant product: {e}")
            return False
    
    async def get_products_by_tenant(self, tenant_id: str) -> List[TenantProduct]:
        """Ambil semua produk untuk tenant"""
        try:
            query = "SELECT * FROM tenant_products WHERE tenant_id = ? AND is_active = 1"
            result = await self.db.execute_query(query, (tenant_id,))
            
            products = []
            if result:
                for row in result:
                    products.append(self._row_to_product(dict(row)))
            
            return products
            
        except Exception as e:
            logger.error(f"Error getting tenant products: {e}")
            return []
    
    async def add_stock(self, stock: TenantStock) -> bool:
        """Tambah stock untuk produk tenant"""
        try:
            query = """
                INSERT INTO tenant_stocks 
                (tenant_id, product_code, content, status, added_by, added_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                stock.tenant_id,
                stock.product_code,
                stock.content,
                stock.status.value,
                stock.added_by,
                stock.added_at.isoformat(),
                stock.updated_at.isoformat()
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            logger.error(f"Error adding tenant stock: {e}")
            return False
    
    async def get_available_stock(self, tenant_id: str, product_code: str) -> List[TenantStock]:
        """Ambil stock yang tersedia untuk produk tenant"""
        try:
            query = """
                SELECT * FROM tenant_stocks 
                WHERE tenant_id = ? AND product_code = ? AND status = 'available'
                ORDER BY added_at ASC
            """
            result = await self.db.execute_query(query, (tenant_id, product_code))
            
            stocks = []
            if result:
                for row in result:
                    stocks.append(self._row_to_stock(dict(row)))
            
            return stocks
            
        except Exception as e:
            logger.error(f"Error getting available stock: {e}")
            return []
    
    def _row_to_product(self, row: Dict[str, Any]) -> TenantProduct:
        """Convert database row ke TenantProduct object"""
        return TenantProduct(
            id=row.get('id'),
            tenant_id=row.get('tenant_id', ''),
            code=row.get('code', ''),
            name=row.get('name', ''),
            price=row.get('price', 0),
            description=row.get('description'),
            category=row.get('category'),
            is_active=bool(row.get('is_active', True)),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
    
    def _row_to_stock(self, row: Dict[str, Any]) -> TenantStock:
        """Convert database row ke TenantStock object"""
        return TenantStock(
            id=row.get('id'),
            tenant_id=row.get('tenant_id', ''),
            product_code=row.get('product_code', ''),
            content=row.get('content', ''),
            status=TenantStockStatus(row.get('status', 'available')),
            added_by=row.get('added_by', ''),
            buyer_id=row.get('buyer_id'),
            seller_id=row.get('seller_id'),
            purchase_price=row.get('purchase_price'),
            added_at=row.get('added_at'),
            updated_at=row.get('updated_at')
        )
