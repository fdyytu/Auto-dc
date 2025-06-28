"""
Product Service
Menangani business logic untuk product management
"""

import logging
from typing import Optional, List
from src.database.connection import DatabaseManager
from src.database.models.product import Product, Stock, StockStatus
from src.services.base_service import BaseService, ServiceResponse

class ProductService(BaseService):
    """Service untuk menangani operasi product"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.db = db_manager
    
    async def get_product(self, code: str) -> ServiceResponse:
        """Ambil product berdasarkan code"""
        try:
            query = "SELECT * FROM products WHERE code = ?"
            result = await self.db.execute_query(query, (code,))
            
            if not result:
                return ServiceResponse.error_response(
                    error="Product tidak ditemukan",
                    message=f"Product dengan code {code} tidak ditemukan"
                )
            
            product_data = dict(result[0])
            product = Product.from_dict(product_data)
            
            return ServiceResponse.success_response(
                data=product.to_dict(),
                message="Product berhasil ditemukan"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil product")
    
    async def get_all_products(self) -> ServiceResponse:
        """Ambil semua products"""
        try:
            query = "SELECT * FROM products ORDER BY name"
            result = await self.db.execute_query(query)
            
            if not result:
                return ServiceResponse.success_response(
                    data=[],
                    message="Tidak ada product yang ditemukan"
                )
            
            products = []
            for row in result:
                product_data = dict(row)
                product = Product.from_dict(product_data)
                products.append(product.to_dict())
            
            return ServiceResponse.success_response(
                data=products,
                message=f"Berhasil mengambil {len(products)} product"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil semua product")
    
    async def create_product(self, code: str, name: str, price: int, description: str = None) -> ServiceResponse:
        """Buat product baru"""
        try:
            # Cek apakah product sudah ada
            existing_product = await self.get_product(code)
            if existing_product.success:
                return ServiceResponse.error_response(
                    error="Product sudah ada",
                    message=f"Product dengan code {code} sudah terdaftar"
                )
            
            # Validasi input
            if not code or not code.strip():
                return ServiceResponse.error_response(
                    error="Code product tidak boleh kosong",
                    message="Code product harus diisi"
                )
            
            if not name or not name.strip():
                return ServiceResponse.error_response(
                    error="Nama product tidak boleh kosong",
                    message="Nama product harus diisi"
                )
            
            if price < 0:
                return ServiceResponse.error_response(
                    error="Harga tidak valid",
                    message="Harga product tidak boleh negatif"
                )
            
            # Buat product baru
            product = Product(
                code=code.strip(),
                name=name.strip(),
                price=price,
                description=description.strip() if description else None
            )
            
            query = """
                INSERT INTO products (code, name, price, description, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                product.code, product.name, product.price, product.description,
                product.created_at.isoformat(), product.updated_at.isoformat()
            )
            
            success = await self.db.execute_update(query, params)
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal membuat product",
                    message="Gagal menyimpan product ke database"
                )
            
            return ServiceResponse.success_response(
                data=product.to_dict(),
                message=f"Product {code} berhasil dibuat"
            )
            
        except Exception as e:
            return self._handle_exception(e, "membuat product")
    
    async def update_product(self, code: str, **kwargs) -> ServiceResponse:
        """Update product"""
        try:
            # Cek apakah product ada
            product_response = await self.get_product(code)
            if not product_response.success:
                return product_response
            
            allowed_fields = ['name', 'price', 'description']
            updates = []
            params = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field == 'price' and value < 0:
                        return ServiceResponse.error_response(
                            error="Harga tidak valid",
                            message="Harga product tidak boleh negatif"
                        )
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
            params.append(code)
            
            query = f"UPDATE products SET {', '.join(updates)} WHERE code = ?"
            success = await self.db.execute_update(query, tuple(params))
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal update product",
                    message="Gagal mengupdate product di database"
                )
            
            # Return updated product
            return await self.get_product(code)
            
        except Exception as e:
            return self._handle_exception(e, "mengupdate product")
    
    async def delete_product(self, code: str) -> ServiceResponse:
        """Hapus product"""
        try:
            # Cek apakah product ada
            product_response = await self.get_product(code)
            if not product_response.success:
                return product_response
            
            # Cek apakah masih ada stock
            stock_count_response = await self.get_product_stock_count(code)
            if stock_count_response.success and stock_count_response.data['count'] > 0:
                return ServiceResponse.error_response(
                    error="Product masih memiliki stock",
                    message="Tidak dapat menghapus product yang masih memiliki stock"
                )
            
            query = "DELETE FROM products WHERE code = ?"
            success = await self.db.execute_update(query, (code,))
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal menghapus product",
                    message="Gagal menghapus product dari database"
                )
            
            return ServiceResponse.success_response(
                data={"code": code},
                message=f"Product {code} berhasil dihapus"
            )
            
        except Exception as e:
            return self._handle_exception(e, "menghapus product")
    
    async def get_product_stock_count(self, code: str) -> ServiceResponse:
        """Ambil jumlah stock product"""
        try:
            query = "SELECT COUNT(*) as count FROM stock WHERE product_code = ? AND status = ?"
            result = await self.db.execute_query(query, (code, StockStatus.AVAILABLE.value))
            
            count = result[0]['count'] if result else 0
            
            return ServiceResponse.success_response(
                data={'count': count},
                message=f"Product {code} memiliki {count} stock tersedia"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil jumlah stock")
    
    async def get_stock_count(self, code: str) -> ServiceResponse:
        """Alias untuk get_product_stock_count untuk backward compatibility"""
        return await self.get_product_stock_count(code)
    
    async def add_stock(self, product_code: str, content: str, added_by: str) -> ServiceResponse:
        """Tambah stock product - setiap baris baru dihitung sebagai 1 stock"""
        try:
            # Cek apakah product ada
            product_response = await self.get_product(product_code)
            if not product_response.success:
                return product_response
            
            # Validasi input
            if not content or not content.strip():
                return ServiceResponse.error_response(
                    error="Content stock tidak boleh kosong",
                    message="Content stock harus diisi"
                )
            
            if not added_by or not added_by.strip():
                return ServiceResponse.error_response(
                    error="Added by tidak boleh kosong",
                    message="Informasi penambah stock harus diisi"
                )
            
            # Split content berdasarkan baris baru dan filter baris kosong
            lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
            
            if not lines:
                return ServiceResponse.error_response(
                    error="Tidak ada stock valid yang ditemukan",
                    message="Content harus berisi minimal satu baris stock yang valid"
                )
            
            # Siapkan query untuk batch insert
            query = """
                INSERT INTO stock (product_code, content, status, added_by, added_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            # Buat stock entries untuk setiap baris
            stock_entries = []
            params_list = []
            
            for line in lines:
                stock = Stock(
                    product_code=product_code,
                    content=line,
                    added_by=added_by.strip(),
                    status=StockStatus.AVAILABLE
                )
                stock_entries.append(stock)
                
                params = (
                    stock.product_code, stock.content, stock.status.value, stock.added_by,
                    stock.added_at.isoformat(), stock.updated_at.isoformat()
                )
                params_list.append(params)
            
            # Execute batch insert
            success_count = 0
            for params in params_list:
                success = await self.db.execute_update(query, params)
                if success:
                    success_count += 1
            
            if success_count == 0:
                return ServiceResponse.error_response(
                    error="Gagal menambah stock",
                    message="Gagal menyimpan stock ke database"
                )
            
            # Return summary
            return ServiceResponse.success_response(
                data={
                    "total_lines": len(lines),
                    "success_count": success_count,
                    "failed_count": len(lines) - success_count,
                    "stock_entries": [stock.to_dict() for stock in stock_entries[:success_count]]
                },
                message=f"Berhasil menambahkan {success_count} stock dari {len(lines)} baris untuk product {product_code}"
            )
            
        except Exception as e:
            return self._handle_exception(e, "menambah stock")
    
    async def get_available_stock(self, product_code: str, limit: int = 1) -> ServiceResponse:
        """Ambil stock yang tersedia"""
        try:
            query = "SELECT * FROM stock WHERE product_code = ? AND status = ? ORDER BY added_at ASC LIMIT ?"
            result = await self.db.execute_query(query, (product_code, StockStatus.AVAILABLE.value, limit))
            
            if not result:
                return ServiceResponse.success_response(
                    data=[],
                    message=f"Tidak ada stock tersedia untuk product {product_code}"
                )
            
            stocks = []
            for row in result:
                stock_data = dict(row)
                stock = Stock.from_dict(stock_data)
                stocks.append(stock.to_dict())
            
            return ServiceResponse.success_response(
                data=stocks,
                message=f"Berhasil mengambil {len(stocks)} stock tersedia"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil stock tersedia")
    
    async def mark_stock_sold(self, stock_id: int, buyer_id: str) -> ServiceResponse:
        """Tandai stock sebagai terjual"""
        try:
            # Cek apakah stock ada dan tersedia
            query = "SELECT * FROM stock WHERE id = ? AND status = ?"
            result = await self.db.execute_query(query, (stock_id, StockStatus.AVAILABLE.value))
            
            if not result:
                return ServiceResponse.error_response(
                    error="Stock tidak ditemukan atau tidak tersedia",
                    message=f"Stock dengan ID {stock_id} tidak ditemukan atau sudah terjual"
                )
            
            # Update status stock
            from datetime import datetime
            update_query = """
                UPDATE stock 
                SET status = ?, buyer_id = ?, updated_at = ? 
                WHERE id = ?
            """
            updated_at = datetime.utcnow().isoformat()
            success = await self.db.execute_update(
                update_query, 
                (StockStatus.SOLD.value, buyer_id, updated_at, stock_id)
            )
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal update status stock",
                    message="Gagal mengupdate status stock di database"
                )
            
            # Ambil data stock yang sudah diupdate
            updated_result = await self.db.execute_query("SELECT * FROM stock WHERE id = ?", (stock_id,))
            if updated_result:
                stock_data = dict(updated_result[0])
                stock = Stock.from_dict(stock_data)
                
                return ServiceResponse.success_response(
                    data=stock.to_dict(),
                    message=f"Stock ID {stock_id} berhasil ditandai sebagai terjual"
                )
            
            return ServiceResponse.success_response(
                data={"stock_id": stock_id, "buyer_id": buyer_id},
                message=f"Stock ID {stock_id} berhasil ditandai sebagai terjual"
            )
            
        except Exception as e:
            return self._handle_exception(e, "menandai stock sebagai terjual")
    
    async def update_stock_status(self, product_code: str, stock_ids: List[int], status: str, buyer_id: str = None) -> ServiceResponse:
        """Update status multiple stock items"""
        try:
            if not stock_ids:
                return ServiceResponse.error_response(
                    error="Tidak ada stock ID yang diberikan",
                    message="Daftar stock ID tidak boleh kosong"
                )
            
            # Validasi status
            valid_statuses = [status.value for status in StockStatus]
            if status not in valid_statuses:
                return ServiceResponse.error_response(
                    error="Status tidak valid",
                    message=f"Status harus salah satu dari: {', '.join(valid_statuses)}"
                )
            
            from datetime import datetime
            updated_at = datetime.utcnow().isoformat()
            
            # Update semua stock sekaligus
            placeholders = ','.join(['?' for _ in stock_ids])
            query = f"""
                UPDATE stock 
                SET status = ?, buyer_id = ?, updated_at = ? 
                WHERE id IN ({placeholders}) AND product_code = ?
            """
            
            params = [status, buyer_id, updated_at] + stock_ids + [product_code]
            success = await self.db.execute_update(query, params)
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal update status stock",
                    message="Gagal mengupdate status stock di database"
                )
            
            # Ambil data stock yang sudah diupdate untuk verifikasi
            updated_query = f"SELECT * FROM stock WHERE id IN ({placeholders})"
            updated_result = await self.db.execute_query(updated_query, stock_ids)
            
            updated_stocks = []
            if updated_result:
                for row in updated_result:
                    stock_data = dict(row)
                    stock = Stock.from_dict(stock_data)
                    updated_stocks.append(stock.to_dict())
            
            return ServiceResponse.success_response(
                data=updated_stocks,
                message=f"Berhasil mengupdate status {len(stock_ids)} stock menjadi {status}"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengupdate status stock")

    async def get_stock_history(self, code: str, limit: int = 10) -> ServiceResponse:
        """Ambil history stock produk"""
        try:
            # Validasi input
            if not code or not code.strip():
                return ServiceResponse.error_response(
                    error="Code product tidak boleh kosong",
                    message="Code product harus diisi"
                )
            
            if limit < 1 or limit > 100:
                return ServiceResponse.error_response(
                    error="Limit tidak valid",
                    message="Limit harus antara 1-100"
                )
            
            # Query untuk mengambil history stock
            query = """
                SELECT 
                    s.id,
                    s.product_code,
                    s.status,
                    s.buyer_id,
                    s.created_at,
                    s.updated_at,
                    'stock_added' as action,
                    1 as quantity,
                    'system' as admin
                FROM stock s
                WHERE s.product_code = ?
                ORDER BY s.created_at DESC
                LIMIT ?
            """
            
            result = await self.db.execute_query(query, (code.upper(), limit))
            
            if not result:
                return ServiceResponse.success_response(
                    data=[],
                    message=f"Tidak ada history stock untuk product {code.upper()}"
                )
            
            # Format data history
            history_data = []
            for row in result:
                row_dict = dict(row)
                history_item = {
                    'action': row_dict.get('action', 'stock_added'),
                    'quantity': row_dict.get('quantity', 1),
                    'admin': row_dict.get('admin', 'system'),
                    'timestamp': row_dict.get('created_at', ''),
                    'status': row_dict.get('status', 'available'),
                    'stock_id': row_dict.get('id', 0)
                }
                history_data.append(history_item)
            
            return ServiceResponse.success_response(
                data=history_data,
                message=f"Berhasil mengambil {len(history_data)} history stock untuk {code.upper()}"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil history stock")

    async def get_product_with_stock_info(self, code: str) -> ServiceResponse:
        """Ambil product beserta informasi stock"""
        try:
            product_response = await self.get_product(code)
            if not product_response.success:
                return product_response
            
            stock_count_response = await self.get_product_stock_count(code)
            
            product_data = product_response.data
            product_data['stock_count'] = stock_count_response.data['count'] if stock_count_response.success else 0
            
            return ServiceResponse.success_response(
                data=product_data,
                message="Product dengan informasi stock berhasil diambil"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil product dengan informasi stock")
