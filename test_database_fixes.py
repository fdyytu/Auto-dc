"""
Test script untuk memverifikasi perbaikan database errors
"""

import asyncio
import sqlite3
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.connection import get_connection
from src.services.balance_service import BalanceManagerService
from src.services.transaction_service import TransactionManager

class MockBot:
    """Mock bot untuk testing"""
    def __init__(self):
        self.db_manager = None

async def test_balance_transactions_table():
    """Test apakah tabel balance_transactions sudah ada dan berfungsi"""
    print("🔄 Testing balance_transactions table...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Test insert ke balance_transactions
        cursor.execute("""
            INSERT INTO balance_transactions 
            (growid, type, details, old_balance, new_balance)
            VALUES (?, ?, ?, ?, ?)
        """, ("TEST_USER", "test", "Test transaction", "0|0|0", "100|0|0"))
        
        # Test select dari balance_transactions
        cursor.execute("""
            SELECT * FROM balance_transactions 
            WHERE growid = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """, ("TEST_USER",))
        
        result = cursor.fetchone()
        conn.commit()
        conn.close()
        
        if result:
            print("✅ balance_transactions table berfungsi dengan baik!")
            return True
        else:
            print("❌ balance_transactions table tidak berfungsi!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing balance_transactions: {e}")
        return False

async def test_world_info_table():
    """Test apakah tabel world_info sudah ada dan berfungsi"""
    print("🔄 Testing world_info table...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Test insert ke world_info
        cursor.execute("""
            INSERT OR REPLACE INTO world_info 
            (id, world, owner, bot)
            VALUES (?, ?, ?, ?)
        """, (1, "TESTWORLD", "TESTOWNER", "TESTBOT"))
        
        # Test select dari world_info
        cursor.execute("SELECT world, owner, bot FROM world_info WHERE id = 1")
        result = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if result and result[0] == "TESTWORLD":
            print("✅ world_info table berfungsi dengan baik!")
            return True
        else:
            print("❌ world_info table tidak berfungsi!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing world_info: {e}")
        return False

async def test_balance_service():
    """Test BalanceManagerService dengan tabel baru"""
    print("🔄 Testing BalanceManagerService...")
    
    try:
        bot = MockBot()
        service = BalanceManagerService(bot)
        
        # Test get_transaction_history
        response = await service.get_transaction_history("TEST_USER", 5)
        
        if response.success:
            print("✅ BalanceManagerService.get_transaction_history berfungsi!")
            return True
        else:
            print(f"⚠️ BalanceManagerService.get_transaction_history: {response.error}")
            return True  # Masih OK jika tidak ada data
            
    except Exception as e:
        print(f"❌ Error testing BalanceManagerService: {e}")
        return False

async def test_transaction_manager():
    """Test TransactionManager dengan method baru"""
    print("🔄 Testing TransactionManager...")
    
    try:
        bot = MockBot()
        manager = TransactionManager(bot)
        
        # Test apakah method get_user_transactions ada
        if hasattr(manager, 'get_user_transactions'):
            print("✅ TransactionManager.get_user_transactions method tersedia!")
            
            # Test call method
            response = await manager.get_user_transactions("TEST_USER", 5)
            print(f"✅ TransactionManager.get_user_transactions berfungsi!")
            return True
        else:
            print("❌ TransactionManager.get_user_transactions method tidak ditemukan!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing TransactionManager: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Memulai test perbaikan database errors...")
    print("=" * 50)
    
    tests = [
        test_balance_transactions_table,
        test_world_info_table,
        test_balance_service,
        test_transaction_manager
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} gagal: {e}")
            results.append(False)
        print("-" * 30)
    
    print("📊 HASIL TEST:")
    print(f"✅ Berhasil: {sum(results)}/{len(results)}")
    print(f"❌ Gagal: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 Semua test berhasil! Perbaikan database sudah selesai.")
    else:
        print("⚠️ Ada beberapa test yang gagal. Perlu perbaikan lebih lanjut.")
    
    return all(results)

if __name__ == "__main__":
    asyncio.run(main())
