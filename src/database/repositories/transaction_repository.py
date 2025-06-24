"""
Transaction Repository
Menangani operasi database untuk transaksi
"""

import logging
from typing import Optional, List
from datetime import datetime
from src.database.connection import DatabaseManager
from src.database.models import Transaction, TransactionStatus, TransactionType

logger = logging.getLogger(__name__)

class TransactionRepository:
    """Repository untuk operasi transaksi"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logger
    
    async def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Ambil transaksi berdasarkan ID"""
        try:
            query = "SELECT * FROM transactions WHERE id = ?"
            result = await self.db.execute_query(query, (transaction_id,))
            
            if result and len(result) > 0:
                row = result[0]
                return Transaction(
                    id=row['id'],
                    buyer_id=row['buyer_id'],
                    seller_id=row.get('seller_id'),
                    product_code=row.get('product_code'),
                    quantity=row['quantity'],
                    total_price=row['total_price'],
                    transaction_type=TransactionType(row.get('transaction_type', 'purchase')),
                    status=TransactionStatus(row['status']),
                    details=row.get('details'),
                    created_at=row['created_at'],
                    updated_at=row.get('updated_at')
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting transaction by ID: {e}")
            return None
    
    async def create_transaction(self, transaction: Transaction) -> Optional[int]:
        """Buat transaksi baru dan return ID"""
        try:
            query = """
                INSERT INTO transactions 
                (buyer_id, seller_id, product_code, quantity, total_price, 
                 transaction_type, status, details, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                transaction.buyer_id,
                transaction.seller_id,
                transaction.product_code,
                transaction.quantity,
                transaction.total_price,
                transaction.transaction_type.value if isinstance(transaction.transaction_type, TransactionType) else transaction.transaction_type,
                transaction.status.value if isinstance(transaction.status, TransactionStatus) else transaction.status,
                transaction.details,
                transaction.created_at.isoformat() if transaction.created_at else None,
                transaction.updated_at.isoformat() if transaction.updated_at else None
            )
            
            success = await self.db.execute_update(query, params)
            if success:
                # Get the last inserted ID
                result = await self.db.execute_query("SELECT last_insert_rowid() as id")
                if result and len(result) > 0:
                    return result[0]['id']
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating transaction: {e}")
            return None
    
    async def update_transaction_status(self, transaction_id: int, status: TransactionStatus, details: str = None) -> bool:
        """Update status transaksi"""
        try:
            query = """
                UPDATE transactions 
                SET status = ?, details = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                status.value if isinstance(status, TransactionStatus) else status,
                details,
                datetime.utcnow().isoformat(),
                transaction_id
            )
            
            return await self.db.execute_update(query, params)
            
        except Exception as e:
            self.logger.error(f"Error updating transaction status: {e}")
            return False
    
    async def get_user_transactions(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Transaction]:
        """Ambil transaksi user"""
        try:
            query = """
                SELECT * FROM transactions 
                WHERE buyer_id = ? OR seller_id = ?
                ORDER BY created_at DESC LIMIT ? OFFSET ?
            """
            result = await self.db.execute_query(query, (user_id, user_id, limit, offset))
            
            transactions = []
            if result:
                for row in result:
                    transaction = Transaction(
                        id=row['id'],
                        buyer_id=row['buyer_id'],
                        seller_id=row.get('seller_id'),
                        product_code=row.get('product_code'),
                        quantity=row['quantity'],
                        total_price=row['total_price'],
                        transaction_type=TransactionType(row.get('transaction_type', 'purchase')),
                        status=TransactionStatus(row['status']),
                        details=row.get('details'),
                        created_at=row['created_at'],
                        updated_at=row.get('updated_at')
                    )
                    transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting user transactions: {e}")
            return []
    
    async def get_transactions_by_status(self, status: TransactionStatus, limit: int = 100) -> List[Transaction]:
        """Ambil transaksi berdasarkan status"""
        try:
            query = """
                SELECT * FROM transactions 
                WHERE status = ?
                ORDER BY created_at DESC LIMIT ?
            """
            result = await self.db.execute_query(query, (status.value, limit))
            
            transactions = []
            if result:
                for row in result:
                    transaction = Transaction(
                        id=row['id'],
                        buyer_id=row['buyer_id'],
                        seller_id=row.get('seller_id'),
                        product_code=row.get('product_code'),
                        quantity=row['quantity'],
                        total_price=row['total_price'],
                        transaction_type=TransactionType(row.get('transaction_type', 'purchase')),
                        status=TransactionStatus(row['status']),
                        details=row.get('details'),
                        created_at=row['created_at'],
                        updated_at=row.get('updated_at')
                    )
                    transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting transactions by status: {e}")
            return []
    
    async def get_product_transactions(self, product_code: str, limit: int = 50) -> List[Transaction]:
        """Ambil transaksi untuk produk tertentu"""
        try:
            query = """
                SELECT * FROM transactions 
                WHERE product_code = ?
                ORDER BY created_at DESC LIMIT ?
            """
            result = await self.db.execute_query(query, (product_code, limit))
            
            transactions = []
            if result:
                for row in result:
                    transaction = Transaction(
                        id=row['id'],
                        buyer_id=row['buyer_id'],
                        seller_id=row.get('seller_id'),
                        product_code=row.get('product_code'),
                        quantity=row['quantity'],
                        total_price=row['total_price'],
                        transaction_type=TransactionType(row.get('transaction_type', 'purchase')),
                        status=TransactionStatus(row['status']),
                        details=row.get('details'),
                        created_at=row['created_at'],
                        updated_at=row.get('updated_at')
                    )
                    transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting product transactions: {e}")
            return []
    
    async def get_transaction_stats(self, start_date: datetime = None, end_date: datetime = None) -> dict:
        """Ambil statistik transaksi"""
        try:
            base_query = "SELECT COUNT(*) as count, SUM(total_price) as total FROM transactions"
            params = []
            
            if start_date and end_date:
                base_query += " WHERE created_at BETWEEN ? AND ?"
                params = [start_date.isoformat(), end_date.isoformat()]
            elif start_date:
                base_query += " WHERE created_at >= ?"
                params = [start_date.isoformat()]
            elif end_date:
                base_query += " WHERE created_at <= ?"
                params = [end_date.isoformat()]
            
            result = await self.db.execute_query(base_query, tuple(params))
            
            stats = {
                'total_transactions': 0,
                'total_value': 0,
                'by_status': {},
                'by_type': {}
            }
            
            if result and len(result) > 0:
                row = result[0]
                stats['total_transactions'] = row['count'] or 0
                stats['total_value'] = row['total'] or 0
            
            # Get stats by status
            status_query = base_query.replace("COUNT(*) as count, SUM(total_price) as total", 
                                            "status, COUNT(*) as count, SUM(total_price) as total") + " GROUP BY status"
            status_result = await self.db.execute_query(status_query, tuple(params))
            
            if status_result:
                for row in status_result:
                    stats['by_status'][row['status']] = {
                        'count': row['count'],
                        'total': row['total'] or 0
                    }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting transaction stats: {e}")
            return {
                'total_transactions': 0,
                'total_value': 0,
                'by_status': {},
                'by_type': {}
            }
    
    async def delete_transaction(self, transaction_id: int) -> bool:
        """Hapus transaksi"""
        try:
            query = "DELETE FROM transactions WHERE id = ?"
            return await self.db.execute_update(query, (transaction_id,))
            
        except Exception as e:
            self.logger.error(f"Error deleting transaction: {e}")
            return False
