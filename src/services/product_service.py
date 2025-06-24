"""
Product Service
Menangani business logic untuk product management
"""

import logging
from typing import Optional, Dict, Any, List
from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

class ProductService:
    """Service untuk menangani operasi product"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_product(self, code: str) -> Optional[Dict[str, Any]]:
        """Ambil product berdasarkan code"""
        try:
            query = "SELECT * FROM products WHERE code = ?"
            result = await self.db.execute_query(query, (code,))
            return dict(result[0]) if result else None
        except Exception as e:
            logger.error(f"Error get product: {e}")
            return None
    
    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Ambil semua products"""
        try:
            query = "SELECT * FROM products ORDER BY name"
            result = await self.db.execute_query(query)
            return [dict(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error get all products: {e}")
            return []
    
    async def create_product(self, code: str, name: str, price: int, description: str = None) -> bool:
        """Buat product baru"""
        try:
            query = "INSERT INTO products (code, name, price, description) VALUES (?, ?, ?, ?)"
            return await self.db.execute_update(query, (code, name, price, description))
        except Exception as e:
            logger.error(f"Error create product: {e}")
            return False
    
    async def update_product(self, code: str, **kwargs) -> bool:
        """Update product"""
        try:
            allowed_fields = ['name', 'price', 'description']
            updates = []
            params = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = ?")
                    params.append(value)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(code)
            
            query = f"UPDATE products SET {', '.join(updates)} WHERE code = ?"
            return await self.db.execute_update(query, tuple(params))
            
        except Exception as e:
            logger.error(f"Error update product: {e}")
            return False
    
    async def delete_product(self, code: str) -> bool:
        """Hapus product"""
        try:
            query = "DELETE FROM products WHERE code = ?"
            return await self.db.execute_update(query, (code,))
        except Exception as e:
            logger.error(f"Error delete product: {e}")
            return False
    
    async def get_product_stock_count(self, code: str) -> int:
        """Ambil jumlah stock product"""
        try:
            query = "SELECT COUNT(*) as count FROM stock WHERE product_code = ? AND status = 'available'"
            result = await self.db.execute_query(query, (code,))
            return result[0]['count'] if result else 0
        except Exception as e:
            logger.error(f"Error get stock count: {e}")
            return 0
    
    async def add_stock(self, product_code: str, content: str, added_by: str) -> bool:
        """Tambah stock product"""
        try:
            query = "INSERT INTO stock (product_code, content, added_by) VALUES (?, ?, ?)"
            return await self.db.execute_update(query, (product_code, content, added_by))
        except Exception as e:
            logger.error(f"Error add stock: {e}")
            return False
    
    async def get_available_stock(self, product_code: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Ambil stock yang tersedia"""
        try:
            query = "SELECT * FROM stock WHERE product_code = ? AND status = 'available' LIMIT ?"
            result = await self.db.execute_query(query, (product_code, limit))
            return [dict(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error get available stock: {e}")
            return []
    
    async def mark_stock_sold(self, stock_id: int, buyer_id: str) -> bool:
        """Tandai stock sebagai terjual"""
        try:
            query = "UPDATE stock SET status = 'sold', buyer_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            return await self.db.execute_update(query, (buyer_id, stock_id))
        except Exception as e:
            logger.error(f"Error mark stock sold: {e}")
            return False
