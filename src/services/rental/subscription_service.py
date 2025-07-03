"""
Subscription Service untuk Bot Rental System
Menangani business logic untuk manajemen langganan bot
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from src.database.connection import DatabaseManager
from src.database.models.rental.subscription import Subscription, SubscriptionStatus, SubscriptionPlan
from src.services.base_service import BaseService, ServiceResponse

class SubscriptionService(BaseService):
    """Service untuk menangani operasi subscription bot rental"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.db = db_manager
    
    async def create_subscription(self, discord_id: str, plan: str, duration_days: int = 30) -> ServiceResponse:
        """Buat subscription baru"""
        try:
            # Generate tenant ID unik
            import uuid
            tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
            
            # Buat subscription baru
            subscription = Subscription(
                tenant_id=tenant_id,
                discord_id=discord_id,
                plan=SubscriptionPlan(plan),
                status=SubscriptionStatus.PENDING,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=duration_days)
            )
            
            # Simpan ke database
            query = """
                INSERT INTO subscriptions 
                (tenant_id, discord_id, plan, status, start_date, end_date, auto_renew, features, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                subscription.tenant_id,
                subscription.discord_id,
                subscription.plan.value,
                subscription.status.value,
                subscription.start_date.isoformat(),
                subscription.end_date.isoformat(),
                subscription.auto_renew,
                str(subscription.features),  # Convert dict to string for SQLite
                subscription.created_at.isoformat(),
                subscription.updated_at.isoformat()
            )
            
            if not await self.db.execute_update(query, params):
                return ServiceResponse.error_response(
                    error="Gagal membuat subscription",
                    message="Gagal menyimpan subscription ke database"
                )
            
            return ServiceResponse.success_response(
                data=subscription.to_dict(),
                message=f"Subscription {plan} berhasil dibuat untuk {duration_days} hari"
            )
            
        except Exception as e:
            return self._handle_exception(e, "membuat subscription")
    
    async def get_subscription_by_discord_id(self, discord_id: str) -> ServiceResponse:
        """Ambil subscription berdasarkan Discord ID"""
        try:
            query = "SELECT * FROM subscriptions WHERE discord_id = ? ORDER BY created_at DESC LIMIT 1"
            result = await self.db.execute_query(query, (discord_id,))
            
            if not result:
                return ServiceResponse.error_response(
                    error="Subscription tidak ditemukan",
                    message=f"Tidak ada subscription untuk Discord ID {discord_id}"
                )
            
            subscription_data = dict(result[0])
            # Parse features string back to dict
            import ast
            try:
                subscription_data['features'] = ast.literal_eval(subscription_data['features'])
            except:
                subscription_data['features'] = {}
            
            subscription = Subscription.from_dict(subscription_data)
            
            return ServiceResponse.success_response(
                data=subscription.to_dict(),
                message="Subscription berhasil ditemukan"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil subscription")
    
    async def get_subscription_by_tenant_id(self, tenant_id: str) -> ServiceResponse:
        """Ambil subscription berdasarkan tenant ID"""
        try:
            query = "SELECT * FROM subscriptions WHERE tenant_id = ?"
            result = await self.db.execute_query(query, (tenant_id,))
            
            if not result:
                return ServiceResponse.error_response(
                    error="Subscription tidak ditemukan",
                    message=f"Tidak ada subscription untuk tenant {tenant_id}"
                )
            
            subscription_data = dict(result[0])
            import ast
            try:
                subscription_data['features'] = ast.literal_eval(subscription_data['features'])
            except:
                subscription_data['features'] = {}
            
            subscription = Subscription.from_dict(subscription_data)
            
            return ServiceResponse.success_response(
                data=subscription.to_dict(),
                message="Subscription berhasil ditemukan"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil subscription berdasarkan tenant ID")
    
    async def update_subscription_status(self, tenant_id: str, status: str) -> ServiceResponse:
        """Update status subscription"""
        try:
            query = "UPDATE subscriptions SET status = ?, updated_at = ? WHERE tenant_id = ?"
            updated_at = datetime.utcnow().isoformat()
            
            success = await self.db.execute_update(query, (status, updated_at, tenant_id))
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal update status",
                    message="Gagal mengupdate status subscription"
                )
            
            return ServiceResponse.success_response(
                data={"tenant_id": tenant_id, "new_status": status},
                message=f"Status subscription berhasil diupdate ke {status}"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengupdate status subscription")
    
    async def extend_subscription(self, tenant_id: str, days: int) -> ServiceResponse:
        """Perpanjang subscription"""
        try:
            # Ambil subscription saat ini
            subscription_response = await self.get_subscription_by_tenant_id(tenant_id)
            if not subscription_response.success:
                return subscription_response
            
            subscription_data = subscription_response.data
            current_end_date = datetime.fromisoformat(subscription_data['end_date'])
            new_end_date = current_end_date + timedelta(days=days)
            
            query = "UPDATE subscriptions SET end_date = ?, updated_at = ? WHERE tenant_id = ?"
            updated_at = datetime.utcnow().isoformat()
            
            success = await self.db.execute_update(query, (new_end_date.isoformat(), updated_at, tenant_id))
            
            if not success:
                return ServiceResponse.error_response(
                    error="Gagal perpanjang subscription",
                    message="Gagal memperpanjang subscription"
                )
            
            return ServiceResponse.success_response(
                data={
                    "tenant_id": tenant_id,
                    "extended_days": days,
                    "new_end_date": new_end_date.isoformat()
                },
                message=f"Subscription berhasil diperpanjang {days} hari"
            )
            
        except Exception as e:
            return self._handle_exception(e, "memperpanjang subscription")
    
    async def get_all_subscriptions(self) -> ServiceResponse:
        """Ambil semua subscription"""
        try:
            query = "SELECT * FROM subscriptions ORDER BY created_at DESC"
            result = await self.db.execute_query(query)
            
            if not result:
                return ServiceResponse.success_response(
                    data=[],
                    message="Tidak ada subscription yang ditemukan"
                )
            
            subscriptions = []
            for row in result:
                subscription_data = dict(row)
                import ast
                try:
                    subscription_data['features'] = ast.literal_eval(subscription_data['features'])
                except:
                    subscription_data['features'] = {}
                
                subscription = Subscription.from_dict(subscription_data)
                subscriptions.append(subscription.to_dict())
            
            return ServiceResponse.success_response(
                data=subscriptions,
                message=f"Berhasil mengambil {len(subscriptions)} subscription"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil semua subscription")
    
    async def check_expired_subscriptions(self) -> ServiceResponse:
        """Cek dan update subscription yang expired"""
        try:
            current_time = datetime.utcnow().isoformat()
            
            # Cari subscription yang expired
            query = """
                SELECT tenant_id FROM subscriptions 
                WHERE end_date < ? AND status = 'active'
            """
            result = await self.db.execute_query(query, (current_time,))
            
            expired_count = 0
            if result:
                # Update status ke expired
                for row in result:
                    tenant_id = row['tenant_id']
                    await self.update_subscription_status(tenant_id, SubscriptionStatus.EXPIRED.value)
                    expired_count += 1
            
            return ServiceResponse.success_response(
                data={"expired_count": expired_count},
                message=f"Berhasil memproses {expired_count} subscription yang expired"
            )
            
        except Exception as e:
            return self._handle_exception(e, "memeriksa subscription expired")
    
    async def get_subscription_stats(self) -> ServiceResponse:
        """Ambil statistik subscription"""
        try:
            stats = {}
            
            # Total subscription
            total_query = "SELECT COUNT(*) as total FROM subscriptions"
            total_result = await self.db.execute_query(total_query)
            stats['total'] = total_result[0]['total'] if total_result else 0
            
            # Subscription aktif
            active_query = "SELECT COUNT(*) as active FROM subscriptions WHERE status = 'active'"
            active_result = await self.db.execute_query(active_query)
            stats['active'] = active_result[0]['active'] if active_result else 0
            
            # Subscription per plan
            plan_query = "SELECT plan, COUNT(*) as count FROM subscriptions GROUP BY plan"
            plan_result = await self.db.execute_query(plan_query)
            stats['by_plan'] = {row['plan']: row['count'] for row in plan_result} if plan_result else {}
            
            # Revenue estimation (dummy calculation)
            plan_prices = {'basic': 10, 'premium': 25, 'enterprise': 50}
            estimated_revenue = sum(stats['by_plan'].get(plan, 0) * price for plan, price in plan_prices.items())
            stats['estimated_monthly_revenue'] = estimated_revenue
            
            return ServiceResponse.success_response(
                data=stats,
                message="Statistik subscription berhasil diambil"
            )
            
        except Exception as e:
            return self._handle_exception(e, "mengambil statistik subscription")
