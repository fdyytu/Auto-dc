"""
Balance Manager Service
Author: fdyyuk
Created at: 2025-03-07 18:04:56 UTC
Last Modified: 2025-03-08 14:38:44 UTC

Dependencies:
- database.py: For database connections
- base_handler.py: For lock management
- cache_manager.py: For caching functionality
- constants.py: For configuration and responses
"""

import logging
import asyncio
from typing import Dict, Optional, Union, Callable, Any
from datetime import datetime

import discord
from discord.ext import commands

from src.config.constants.bot_constants import (
    Balance,
    TransactionType,
    CURRENCY_RATES,
    MESSAGES,
    CACHE_TIMEOUT,
    COLORS
)
from src.database.connection import get_connection
from src.utils.base_handler import BaseLockHandler
from src.services.cache_service import CacheManager

class BalanceCallbackManager:
    """Manager untuk mengelola callbacks balance service"""
    def __init__(self):
        self.callbacks = {
            'balance_updated': [],    # Dipanggil setelah balance diupdate
            'balance_checked': [],    # Dipanggil saat balance dicek
            'user_registered': [],    # Dipanggil setelah user register
            'transaction_added': [],  # Dipanggil setelah transaksi baru
            'error': []              # Dipanggil saat terjadi error
        }
    
    def register(self, event_type: str, callback: Callable):
        """Register callback untuk event tertentu"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    async def trigger(self, event_type: str, *args: Any, **kwargs: Any):
        """Trigger semua callback untuk event tertentu"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    await callback(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Error in {event_type} callback: {e}")

class BalanceResponse:
    """Class untuk standarisasi response dari balance service"""
    def __init__(self, success: bool, data: Any = None, message: str = "", error: str = ""):
        self.success = success
        self.data = data
        self.message = message
        self.error = error
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'error': self.error,
            'timestamp': self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @classmethod
    def success(cls, data: Any = None, message: str = "") -> 'BalanceResponse':
        return cls(True, data, message)
    
    @classmethod
    def error(cls, error: str, message: str = "") -> 'BalanceResponse':
        return cls(False, None, message, error)

class BalanceManagerService(BaseLockHandler):
    _instance = None
    _instance_lock = asyncio.Lock()

    def __new__(cls, bot):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, bot):
        if not self.initialized:
            super().__init__()
            self.bot = bot
            self.logger = logging.getLogger("BalanceManagerService")
            self.cache_manager = CacheManager()
            self.callback_manager = BalanceCallbackManager()
            self.setup_default_callbacks()
            self.initialized = True

    def normalize_balance(self, balance: Balance) -> Balance:
        """Normalisasi balance dengan mengkonversi WL ke DL dan DL ke BGL sesuai rate"""
        original_total = balance.total_wl()
        wl = balance.wl
        dl = balance.dl
        bgl = balance.bgl

        # Log original balance
        self.logger.debug(f"[NORMALIZE] Original balance: WL={wl}, DL={dl}, BGL={bgl}, Total={original_total} WL")

        # Konversi WL ke DL
        if wl >= CURRENCY_RATES.RATES['DL']:
            dl += wl // CURRENCY_RATES.RATES['DL']
            wl = wl % CURRENCY_RATES.RATES['DL']

        # Konversi DL ke BGL
        if dl >= CURRENCY_RATES.RATES['BGL']:
            bgl += dl // CURRENCY_RATES.RATES['BGL']
            dl = dl % CURRENCY_RATES.RATES['BGL']

        normalized_balance = Balance(wl, dl, bgl)
        normalized_total = normalized_balance.total_wl()
        
        # Log normalized balance
        self.logger.debug(f"[NORMALIZE] Normalized balance: WL={wl}, DL={dl}, BGL={bgl}, Total={normalized_total} WL")
        
        # Verify total remains the same
        if original_total != normalized_total:
            self.logger.error(f"[NORMALIZE] Balance normalization error: Original={original_total} WL, Normalized={normalized_total} WL")
        
        return normalized_balance

    def setup_default_callbacks(self):
        """Setup default callbacks untuk notifikasi"""
        
        async def notify_balance_updated(growid: str, old_balance: Balance, new_balance: Balance):
            """Callback untuk notifikasi update balance"""
            self.logger.info(f"Balance updated for {growid}: {old_balance.format()} ({old_balance.total_wl()} WL) -> {new_balance.format()} ({new_balance.total_wl()} WL)")
        
        async def notify_user_registered(discord_id: str, growid: str):
            """Callback untuk notifikasi user registration"""
            self.logger.info(f"New user registered: {discord_id} -> {growid}")
        
        # Register default callbacks
        self.callback_manager.register('balance_updated', notify_balance_updated)
        self.callback_manager.register('user_registered', notify_user_registered)

    async def verify_dependencies(self) -> bool:
        """Verify all required dependencies are available"""
        try:
            # Verifikasi koneksi database
            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")  # Simple test query
                cursor.fetchone()
                return True
            finally:
                if conn:
                    conn.close()
        except Exception as e:
            self.logger.error(f"Failed to verify dependencies: {e}")
            return False

    async def cleanup(self):
        """Cleanup resources before unloading"""
        try:
            patterns = [
                "growid_*",
                "discord_id_*", 
                "balance_*",
                "trx_history_*"
            ]
            for pattern in patterns:
                await self.cache_manager.delete_pattern(pattern)
            self.logger.info("BalanceManagerService cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")



    async def get_growid(self, discord_id: str) -> BalanceResponse:
        """Get GrowID for Discord user with proper locking and caching"""
        cache_key = f"growid_{discord_id}"
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return BalanceResponse.success(cached)

        lock = await self.acquire_lock(cache_key)
        if not lock:
            return BalanceResponse.error(MESSAGES.ERROR['LOCK_ACQUISITION_FAILED'])

        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT growid FROM user_growid WHERE discord_id = ? COLLATE binary",
                (str(discord_id),)
            )
            result = cursor.fetchone()
            
            if result:
                growid = result['growid']
                await self.cache_manager.set(
                    cache_key, 
                    growid,
                    expires_in=CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.LONG)
                )
                return BalanceResponse.success(growid)
            return BalanceResponse.error(MESSAGES.ERROR['NOT_REGISTERED'])

        except Exception as e:
            self.logger.error(f"Error getting GrowID: {e}")
            await self.callback_manager.trigger('error', 'get_growid', str(e))
            return BalanceResponse.error(MESSAGES.ERROR['DATABASE_ERROR'])
        finally:
            if conn:
                conn.close()
            self.release_lock(cache_key)

    async def register_user(self, discord_id: str, growid: str) -> BalanceResponse:
        """Register user with proper locking"""
        if not growid or len(growid) < 3:
            return BalanceResponse.error(MESSAGES.ERROR['INVALID_GROWID'])
            
        lock = await self.acquire_lock(f"register_{discord_id}")
        if not lock:
            return BalanceResponse.error(MESSAGES.ERROR['LOCK_ACQUISITION_FAILED'])

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check for existing GrowID
            cursor.execute(
                "SELECT growid FROM users WHERE growid = ? COLLATE binary",
                (growid,)
            )
            existing = cursor.fetchone()
            if existing and existing['growid'] != growid:
                return BalanceResponse.error(MESSAGES.ERROR['GROWID_EXISTS'])
            
            conn.execute("BEGIN TRANSACTION")
            
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (growid, balance_wl, balance_dl, balance_bgl) 
                VALUES (?, 0, 0, 0)
                """,
                (growid,)
            )
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_growid (discord_id, growid) 
                VALUES (?, ?)
                """,
                (str(discord_id), growid)
            )
            
            conn.commit()
            
            # Update caches
            await self.cache_manager.set(
                f"growid_{discord_id}", 
                growid,
                expires_in=CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.LONG)
            )
            await self.cache_manager.set(
                f"discord_id_{growid}", 
                discord_id,
                expires_in=CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.LONG)
            )
            await self.cache_manager.delete(f"balance_{growid}")
            
            # Trigger callback
            await self.callback_manager.trigger('user_registered', discord_id, growid)
            
            return BalanceResponse.success(
                {'discord_id': discord_id, 'growid': growid},
                MESSAGES.SUCCESS['REGISTRATION'].format(growid=growid)
            )

        except Exception as e:
            self.logger.error(f"Error registering user: {e}")
            if conn:
                conn.rollback()
            await self.callback_manager.trigger('error', 'register_user', str(e))
            return BalanceResponse.error(MESSAGES.ERROR['REGISTRATION_FAILED'])
        finally:
            if conn:
                conn.close()
            self.release_lock(f"register_{discord_id}")

    async def update_growid(self, discord_id: str, new_growid: str) -> BalanceResponse:
        """Update GrowID for existing user"""
        if not new_growid or len(new_growid) < 3:
            return BalanceResponse.error(MESSAGES.ERROR['INVALID_GROWID'])
            
        lock = await self.acquire_lock(f"update_growid_{discord_id}")
        if not lock:
            return BalanceResponse.error(MESSAGES.ERROR['LOCK_ACQUISITION_FAILED'])

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get current GrowID
            cursor.execute(
                "SELECT growid FROM user_growid WHERE discord_id = ? COLLATE binary",
                (str(discord_id),)
            )
            current_result = cursor.fetchone()
            if not current_result:
                return BalanceResponse.error(MESSAGES.ERROR['NOT_REGISTERED'])
            
            old_growid = current_result['growid']
            
            # Check if new GrowID already exists for another user
            cursor.execute(
                "SELECT discord_id FROM user_growid WHERE growid = ? COLLATE binary AND discord_id != ?",
                (new_growid, str(discord_id))
            )
            existing = cursor.fetchone()
            if existing:
                return BalanceResponse.error("❌ GrowID sudah digunakan oleh user lain!")
            
            conn.execute("BEGIN TRANSACTION")
            
            # First, get current balance data
            cursor.execute(
                "SELECT balance_wl, balance_dl, balance_bgl FROM users WHERE growid = ? COLLATE binary",
                (old_growid,)
            )
            balance_data = cursor.fetchone()
            
            if balance_data:
                # Create new user entry with current balance
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO users (growid, balance_wl, balance_dl, balance_bgl) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (new_growid, balance_data['balance_wl'], balance_data['balance_dl'], balance_data['balance_bgl'])
                )
            else:
                # Create new user entry with default balance
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO users (growid, balance_wl, balance_dl, balance_bgl) 
                    VALUES (?, 0, 0, 0)
                    """,
                    (new_growid,)
                )
            
            # Update user_growid table (this should work now since new_growid exists in users table)
            cursor.execute(
                "UPDATE user_growid SET growid = ? WHERE discord_id = ?",
                (new_growid, str(discord_id))
            )
            
            # Copy balance transactions to new growid if needed
            cursor.execute(
                "UPDATE balance_transactions SET growid = ? WHERE growid = ?",
                (new_growid, old_growid)
            )
            
            # Remove old user entry if it exists and is different from new one
            if old_growid != new_growid:
                cursor.execute(
                    "DELETE FROM users WHERE growid = ? COLLATE binary",
                    (old_growid,)
                )
            
            conn.commit()
            
            # Update caches
            await self.cache_manager.delete(f"growid_{discord_id}")
            await self.cache_manager.delete(f"discord_id_{old_growid}")
            await self.cache_manager.delete(f"balance_{old_growid}")
            await self.cache_manager.delete(f"balance_{new_growid}")
            
            await self.cache_manager.set(
                f"growid_{discord_id}", 
                new_growid,
                expires_in=CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.LONG)
            )
            await self.cache_manager.set(
                f"discord_id_{new_growid}", 
                discord_id,
                expires_in=CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.LONG)
            )
            
            self.logger.info(f"GrowID updated for user {discord_id}: {old_growid} -> {new_growid}")
            
            return BalanceResponse.success(
                {'discord_id': discord_id, 'old_growid': old_growid, 'new_growid': new_growid},
                f"GrowID berhasil diperbarui dari {old_growid} ke {new_growid}"
            )

        except Exception as e:
            self.logger.error(f"Error updating GrowID: {e}")
            if conn:
                conn.rollback()
            await self.callback_manager.trigger('error', 'update_growid', str(e))
            return BalanceResponse.error("Gagal memperbarui GrowID. Silakan coba lagi.")
        finally:
            if conn:
                conn.close()
            self.release_lock(f"update_growid_{discord_id}")

    async def get_balance(self, growid: str) -> BalanceResponse:
        """Get user balance with proper locking and caching"""
        cache_key = f"balance_{growid}"
        cached = await self.cache_manager.get(cache_key)
        if cached:
            if isinstance(cached, dict):
                balance = Balance(cached['wl'], cached['dl'], cached['bgl'])
            else:
                balance = cached
            normalized_balance = self.normalize_balance(balance)
            return BalanceResponse.success(normalized_balance)

        lock = await self.acquire_lock(cache_key)
        if not lock:
            return BalanceResponse.error(MESSAGES.ERROR['LOCK_ACQUISITION_FAILED'])

        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT balance_wl, balance_dl, balance_bgl 
                FROM users 
                WHERE growid = ? COLLATE binary
                """,
                (growid,)
            )
            result = cursor.fetchone()
            
            if result:
                balance = Balance(
                    result['balance_wl'],
                    result['balance_dl'],
                    result['balance_bgl']
                )
                
                # Log raw balance from database
                self.logger.info(f"[GET_BALANCE] Raw balance from DB for {growid}: WL={balance.wl}, DL={balance.dl}, BGL={balance.bgl}, Total={balance.total_wl()} WL")
                
                normalized_balance = self.normalize_balance(balance)
                
                # Log normalized balance
                self.logger.info(f"[GET_BALANCE] Normalized balance for {growid}: WL={normalized_balance.wl}, DL={normalized_balance.dl}, BGL={normalized_balance.bgl}, Total={normalized_balance.total_wl()} WL")
                
                await self.cache_manager.set(
                    cache_key, 
                    normalized_balance,
                    expires_in=CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.SHORT)
                )
                
                # Trigger callback
                await self.callback_manager.trigger('balance_checked', growid, normalized_balance)
                
                return BalanceResponse.success(normalized_balance)
            return BalanceResponse.error(MESSAGES.ERROR['BALANCE_NOT_FOUND'])

        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            await self.callback_manager.trigger('error', 'get_balance', str(e))
            return BalanceResponse.error(MESSAGES.ERROR['BALANCE_FAILED'])
        finally:
            if conn:
                conn.close()
            self.release_lock(cache_key)

    async def update_balance(
        self, 
        growid: str, 
        wl: int = 0, 
        dl: int = 0, 
        bgl: int = 0,
        details: str = "", 
        transaction_type: TransactionType = TransactionType.DEPOSIT,
        bypass_validation: bool = False
    ) -> BalanceResponse:
        """Update balance with proper locking and validation"""
        lock = await self.acquire_lock(f"balance_update_{growid}")
        if not lock:
            return BalanceResponse.error(MESSAGES.ERROR['LOCK_ACQUISITION_FAILED'])

        conn = None
        try:
            # Get current balance
            balance_response = await self.get_balance(growid)
            if not balance_response.success:
                return balance_response
            
            current_balance = balance_response.data
            
            # Calculate new balance
            new_wl = max(0, current_balance.wl + wl)
            new_dl = max(0, current_balance.dl + dl)
            new_bgl = max(0, current_balance.bgl + bgl)
            
            new_balance = Balance(new_wl, new_dl, new_bgl)
            normalized_new_balance = self.normalize_balance(new_balance)
            
            if not normalized_new_balance.validate():
                return BalanceResponse.error(MESSAGES.ERROR['INVALID_AMOUNT'])

            # Validate withdrawals (skip for admin operations)
            if not bypass_validation:
                if wl < 0 and abs(wl) > current_balance.wl:
                    return BalanceResponse.error(MESSAGES.ERROR['INSUFFICIENT_BALANCE'])
                if dl < 0 and abs(dl) > current_balance.dl:
                    return BalanceResponse.error(MESSAGES.ERROR['INSUFFICIENT_BALANCE'])
                if bgl < 0 and abs(bgl) > current_balance.bgl:
                    return BalanceResponse.error(MESSAGES.ERROR['INSUFFICIENT_BALANCE'])
            
            # For admin operations, allow negative balances to be set to 0
            if bypass_validation:
                new_wl = max(0, current_balance.wl + wl)
                new_dl = max(0, current_balance.dl + dl)
                new_bgl = max(0, current_balance.bgl + bgl)
                new_balance = Balance(new_wl, new_dl, new_bgl)
                normalized_new_balance = self.normalize_balance(new_balance)
            
            # Always normalize the final balance to ensure proper currency conversion
            normalized_new_balance = self.normalize_balance(normalized_new_balance)

            conn = get_connection()
            cursor = conn.cursor()
            
            try:
                conn.execute("BEGIN TRANSACTION")
                
                cursor.execute(
                    """
                    UPDATE users 
                    SET balance_wl = ?, balance_dl = ?, balance_bgl = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE growid = ? COLLATE binary
                    """,
                    (normalized_new_balance.wl, normalized_new_balance.dl, normalized_new_balance.bgl, growid)
                )
                
                # Handle both enum and string transaction types
                if isinstance(transaction_type, TransactionType):
                    transaction_type_value = transaction_type.value
                else:
                    transaction_type_value = str(transaction_type)
                
                cursor.execute(
                    """
                    INSERT INTO balance_transactions 
                    (growid, type, details, old_balance, new_balance, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        growid,
                        transaction_type_value, 
                        details,
                        current_balance.format(),
                        normalized_new_balance.format()
                    )
                )
                
                conn.commit()
                
                # Update cache
                await self.cache_manager.set(
                    f"balance_{growid}", 
                    normalized_new_balance,
                    expires_in=CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.SHORT)
                )
                
                # Invalidate transaction history cache
                await self.cache_manager.delete(f"trx_history_{growid}")
                
                # Trigger callbacks
                await self.callback_manager.trigger(
                    'balance_updated', 
                    growid, 
                    current_balance, 
                    normalized_new_balance
                )
                await self.callback_manager.trigger(
                    'transaction_added',
                    growid,
                    transaction_type,
                    details
                )
                
                return BalanceResponse.success(
                    normalized_new_balance,
                    MESSAGES.SUCCESS['BALANCE_UPDATE']
                )

            except Exception as e:
                conn.rollback()
                raise Exception(str(e))
        
        except Exception as e:
            self.logger.error(f"Error updating balance: {e}")
            await self.callback_manager.trigger('error', 'update_balance', str(e))
            return BalanceResponse.error(MESSAGES.ERROR['TRANSACTION_FAILED'])
        finally:
            if conn:
                conn.close()
            self.release_lock(f"balance_update_{growid}")

    async def get_transaction_history(self, growid: str, limit: int = 10) -> BalanceResponse:
        """Get transaction history with caching"""
        cache_key = f"trx_history_{growid}"
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return BalanceResponse.success(cached[:limit])

        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM balance_transactions 
                WHERE growid = ? COLLATE binary
                ORDER BY created_at DESC
                LIMIT ?
            """, (growid, limit))
            
            transactions = [dict(row) for row in cursor.fetchall()]
            
            await self.cache_manager.set(
                cache_key, 
                transactions,
                expires_in=CACHE_TIMEOUT.get_seconds(CACHE_TIMEOUT.SHORT)
            )
            
            if not transactions:
                return BalanceResponse.error(MESSAGES.ERROR['NO_HISTORY'])
                
            return BalanceResponse.success(transactions)

        except Exception as e:
            self.logger.error(f"Error getting transaction history: {e}")
            await self.callback_manager.trigger('error', 'get_transaction_history', str(e))
            return BalanceResponse.error(MESSAGES.ERROR['DATABASE_ERROR'])
        finally:
            if conn:
                conn.close()

class BalanceManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.balance_service = BalanceManagerService(bot)
        self.logger = logging.getLogger("BalanceManagerCog")

    async def cog_load(self):
        self.logger.info("BalanceManagerCog loading...")
        
    async def cog_unload(self):
        await self.balance_service.cleanup()
        self.logger.info("BalanceManagerCog unloaded")

    async def setup_notifications(self):
        """Setup additional notification callbacks"""
        async def notify_low_balance(growid: str, balance: Balance):
            """Notify when balance is low"""
            if balance.total_wl() < 1000:  # Example threshold
                self.logger.warning(f"Low balance alert for {growid}: {balance}")
        
        async def notify_large_transaction(growid: str, old_balance: Balance, new_balance: Balance):
            """Notify for large transactions"""
            diff = abs(new_balance.total_wl() - old_balance.total_wl())
            if diff > 100000:  # Example threshold: 100K WLS
                self.logger.warning(f"Large transaction alert for {growid}: {old_balance} -> {new_balance} (diff: {diff:,} WLS)")
        
        # Register additional callbacks
        self.balance_service.callback_manager.register('balance_checked', notify_low_balance)
        self.balance_service.callback_manager.register('balance_updated', notify_large_transaction)

async def setup(bot):
    if not hasattr(bot, 'balance_manager_loaded'):
        cog = BalanceManagerCog(bot)
        
        # Verify dependencies before loading
        if not await cog.balance_service.verify_dependencies():
            raise Exception("BalanceManager dependencies verification failed")
        
        # Setup notifications
        await cog.setup_notifications()
            
        await bot.add_cog(cog)
        bot.balance_manager_loaded = True
        logging.info(
            f'BalanceManager cog loaded successfully at '
            f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC'
        )

# Alias untuk backward compatibility
BalanceService = BalanceManagerService
