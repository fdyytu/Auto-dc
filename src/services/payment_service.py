"""
Payment Service untuk Bot Rental System
Menangani business logic untuk pembayaran
"""

import logging
from typing import Optional, List
from datetime import datetime
from src.database.connection import DatabaseManager
from src.database.models.payment import Payment, PaymentStatus, PaymentMethod
from src.services.base_service import BaseService, ServiceResponse

class PaymentService(BaseService):
    """Service untuk menangani operasi pembayaran"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.db = db_manager
    
    async def create_payment(self, tenant_id: str, discord_id: str, amount: float, 
                           method: str, description: str = "") -> ServiceResponse:
        """Buat pembayaran baru"""
        try:
            # Generate transaction ID
            import uuid
            transaction_id = f"pay_{uuid.uuid4().hex[:12]}"
            
            payment = Payment(
                tenant_id=tenant_id,
                discord_id=discord_id,
                amount=amount,
                method=PaymentMethod(method),
                status=PaymentStatus.PENDING,
                transaction_id=transaction_id,
                description=description
            )
            
            # Simpan ke database
            query = """
                INSERT INTO payments 
                (tenant_id, discord_id, amount, currency, method, status, transaction_id, description, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                payment.tenant_id,
                payment.discord_id,
                payment.amount,
                payment.currency,
                payment.method.value,
                payment.status.value,
                payment.transaction_id,
                payment.description,
                payment.created_at.isoformat(),
                payment.updated_at.isoformat()
            )
            
            if not await self.db.execute_update(query, params):
                return ServiceResponse.error_response(
                    error="Gagal membuat pembayaran",
                    message="Gagal menyimpan pembayaran ke database"
                )
            
            return ServiceResponse.success_response(
                data=payment.to_dict(),
                message=f"Pembayaran {transaction_id} berhasil dibuat"
            )
            
        except Exception as e:
            return self._handle_exception(e, "membuat pembayaran")
    
    async def update_payment_status(self, transaction_id: str, status: str, 
                                  gateway_response: dict = None) -> ServiceResponse:
        """Update status pembayaran"""
        try:
            updated_at = datetime.utcnow().isoformat()
            
            query = "UPDATE payments SET status = ?, updated_at = ?"
            params = [status, updated_at]
            
            if gateway_response:
                query += ", gateway_response = ?"
                params.append(str(gateway_response))
            
            query += " WHERE transaction_id = ?"
            params.append(transaction_id)
            
            if not await self.db.execute_update(query, tuple(params)):
                return ServiceResponse.error_response(
                    error="Pembayaran tidak ditemukan",
                    message=f"Tidak ada pembayaran dengan ID {transaction_id}"
                )
            
            return ServiceResponse.success_response(
                data={"transaction_id": transaction_id, "status": status},
                message=f"Status pembayaran berhasil diupdate ke {status}"
            )
            
        except Exception as e:
            return self._handle_exception(e, "update status pembayaran")
    
    async def get_payment_by_transaction_id(self, transaction_id: str) -> ServiceResponse:
        """Ambil pembayaran berdasarkan transaction ID"""
        try:
            query = "SELECT * FROM payments WHERE transaction_id = ?"
            result = await self.db.execute_query(query, (transaction_id,))
            
            if not result:
                return ServiceResponse.error_response(
                    error="Pembayaran tidak ditemukan",
                    message=f"Tidak ada pembayaran dengan ID {transaction_id}"
                )
            
            payment_data = dict(result[0])
            payment = Payment.from_dict(payment_data)
            
            return ServiceResponse.success_response(
                data=payment.to_dict(),
                message="Pembayaran berhasil ditemukan"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil pembayaran")
    
    async def get_payments_by_tenant(self, tenant_id: str) -> ServiceResponse:
        """Ambil semua pembayaran untuk tenant"""
        try:
            query = "SELECT * FROM payments WHERE tenant_id = ? ORDER BY created_at DESC"
            result = await self.db.execute_query(query, (tenant_id,))
            
            payments = []
            if result:
                for row in result:
                    payment_data = dict(row)
                    payment = Payment.from_dict(payment_data)
                    payments.append(payment.to_dict())
            
            return ServiceResponse.success_response(
                data=payments,
                message=f"Berhasil mengambil {len(payments)} pembayaran"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil pembayaran tenant")
