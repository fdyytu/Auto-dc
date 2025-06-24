"""
Product Repository
Menangani operasi database untuk produk dan stok
"""

import logging
from typing import Optional, List
from database.connection import DatabaseManager
from database.models import Product, Stock, StockStatus

logger = logging.getLogger(__name__)

class ProductRepository:
    """Repository untuk operasi produk"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logger
    
    async def get_product_by_code(self, code: str) -> Optional[Product]:
        """Ambil produk berdasarkan kode"""
        try:
            query = "SELECT * FROM products WHERE code = ?"
            result = await self.db.execute_query(query, (code,))
            
            if result and len(result) > 0:
                row = result[0]
                return Product(
                    code=row['code'],
                    name=row['name'],
                    price=row['price'],
                    description=row['description'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting product by code: {e}")
            return None
    
    async def create_product(self, product: Product) -> bool:
        """Buat produk baru"""
        try:
            query = """
                INSERT INTO products (code, name, price, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                product.code,
                product.name,
                product.price,
                product.description,
                product.created_at.isoformat() if product.created_at else None,
                product.updated_at.isoformat() if product.updated_at else None
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            self.logger.error(f"Error creating product: {e}")
            return False
    
    async def update_product(self, product: Product) -> bool:
        """Update produk"""
        try:
            query = """
                UPDATE products 
                SET name = ?, price = ?, description = ?, updated_at = ?
                WHERE code = ?
            """
            params = (
                product.name,
                product.price,
                product.description,
                product.updated_at.isoformat() if product.updated_at else None,
                product.code
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            self.logger.error(f"Error updating product: {e}")
            return False
    
    async def delete_product(self, code: str) -> bool:
        """Hapus produk"""
        try:
            query = "DELETE FROM products WHERE code = ?"
            return await self.db.execute_update(query, (code,))
            
        except Exception as e:
            self.logger.error(f"Error deleting product: {e}")
            return False
    
    async def get_all_products(self, limit: int = 100, offset: int = 0) -> List[Product]:
        """Ambil semua produk dengan pagination"""
        try:
            query = "SELECT * FROM products ORDER BY created_at DESC LIMIT ? OFFSET ?"
            result = await self.db.execute_query(query, (limit, offset))
            
            products = []
            if result:
                for row in result:
                    product = Product(
                        code=row['code'],
                        name=row['name'],
                        price=row['price'],
                        description=row['description'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    products.append(product)
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error getting all products: {e}")
            return []
    
    async def search_products(self, search_term: str, limit: int = 50) -> List[Product]:
        """Cari produk berdasarkan nama atau kode"""
        try:
            query = """
                SELECT * FROM products 
                WHERE name LIKE ? OR code LIKE ? 
                ORDER BY name LIMIT ?
            """
            search_pattern = f"%{search_term}%"
            result = await self.db.execute_query(query, (search_pattern, search_pattern, limit))
            
            products = []
            if result:
                for row in result:
                    product = Product(
                        code=row['code'],
                        name=row['name'],
                        price=row['price'],
                        description=row['description'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    products.append(product)
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error searching products: {e}")
            return []

class StockRepository:
    """Repository untuk operasi stok"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logger
    
    async def get_stock_by_id(self, stock_id: int) -> Optional[Stock]:
        """Ambil stok berdasarkan ID"""
        try:
            query = "SELECT * FROM stock WHERE id = ?"
            result = await self.db.execute_query(query, (stock_id,))
            
            if result and len(result) > 0:
                row = result[0]
                return Stock(
                    id=row['id'],
                    product_code=row['product_code'],
                    content=row['content'],
                    status=StockStatus(row['status']),
                    added_by=row['added_by'],
                    buyer_id=row['buyer_id'],
                    seller_id=row['seller_id'],
                    added_at=row['added_at'],
                    updated_at=row['updated_at']
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting stock by ID: {e}")
            return None
    
    async def get_available_stock(self, product_code: str, limit: int = 10) -> List[Stock]:
        """Ambil stok yang tersedia untuk produk"""
        try:
            query = """
                SELECT * FROM stock 
                WHERE product_code = ? AND status = 'available'
                ORDER BY added_at ASC LIMIT ?
            """
            result = await self.db.execute_query(query, (product_code, limit))
            
            stocks = []
            if result:
                for row in result:
                    stock = Stock(
                        id=row['id'],
                        product_code=row['product_code'],
                        content=row['content'],
                        status=StockStatus(row['status']),
                        added_by=row['added_by'],
                        buyer_id=row['buyer_id'],
                        seller_id=row['seller_id'],
                        added_at=row['added_at'],
                        updated_at=row['updated_at']
                    )
                    stocks.append(stock)
            
            return stocks
            
        except Exception as e:
            self.logger.error(f"Error getting available stock: {e}")
            return []
    
    async def add_stock(self, stock: Stock) -> bool:
        """Tambah stok baru"""
        try:
            query = """
                INSERT INTO stock (product_code, content, status, added_by, added_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                stock.product_code,
                stock.content,
                stock.status.value if isinstance(stock.status, StockStatus) else stock.status,
                stock.added_by,
                stock.added_at.isoformat() if stock.added_at else None,
                stock.updated_at.isoformat() if stock.updated_at else None
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            self.logger.error(f"Error adding stock: {e}")
            return False
    
    async def update_stock_status(self, stock_id: int, status: StockStatus, buyer_id: str = None) -> bool:
        """Update status stok"""
        try:
            from datetime import datetime
            query = """
                UPDATE stock 
                SET status = ?, buyer_id = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                status.value if isinstance(status, StockStatus) else status,
                buyer_id,
                datetime.utcnow().isoformat(),
                stock_id
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            self.logger.error(f"Error updating stock status: {e}")
            return False
    
    async def get_stock_count(self, product_code: str, status: StockStatus = None) -> int:
        """Ambil jumlah stok"""
        try:
            if status:
                query = "SELECT COUNT(*) as count FROM stock WHERE product_code = ? AND status = ?"
                params = (product_code, status.value)
            else:
                query = "SELECT COUNT(*) as count FROM stock WHERE product_code = ?"
                params = (product_code,)
            
            result = await self.db.execute_query(query, params)
            
            if result and len(result) > 0:
                return result[0]['count']
            return 0
            
        except Exception as e:
            self.logger.error(f"Error getting stock count: {e}")
            return 0
    
    async def delete_stock(self, stock_id: int) -> bool:
        """Hapus stok"""
        try:
            query = "DELETE FROM stock WHERE id = ?"
            return await self.db.execute_update(query, (stock_id,))
            
        except Exception as e:
            self.logger.error(f"Error deleting stock: {e}")
            return False
