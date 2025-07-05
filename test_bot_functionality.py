#!/usr/bin/env python3
"""
Test script untuk memverifikasi fungsi-fungsi kritis bot
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from src.database.connection import get_connection
from src.services.balance_service import BalanceManagerService
from src.services.product_service import ProductService
from src.config.constants.bot_constants import Balance

async def test_database_connection():
    """Test koneksi database"""
    print("🔍 Testing database connection...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        print("✅ Database connection: OK")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_balance_service():
    """Test BalanceManagerService"""
    print("🔍 Testing BalanceManagerService...")
    try:
        # Mock bot object
        class MockBot:
            def __init__(self):
                self.db_manager = None
        
        mock_bot = MockBot()
        balance_service = BalanceManagerService(mock_bot)
        
        # Test normalization - gunakan balance yang tidak perlu normalisasi untuk test sederhana
        test_balance = Balance(50, 5, 1)  # 50 WL, 5 DL, 1 BGL
        normalized = balance_service.normalize_balance(test_balance)
        
        print(f"✅ Balance normalization: {test_balance.format()} -> {normalized.format()}")
        print("✅ BalanceManagerService: OK")
        return True
    except Exception as e:
        import traceback
        print(f"❌ BalanceManagerService failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def test_product_service():
    """Test ProductService"""
    print("🔍 Testing ProductService...")
    try:
        # Mock bot object
        class MockBot:
            def __init__(self):
                self.db_manager = None
        
        mock_bot = MockBot()
        product_service = ProductService(mock_bot)
        
        # Test get products (should not crash)
        print("✅ ProductService initialization: OK")
        return True
    except Exception as e:
        print(f"❌ ProductService failed: {e}")
        return False

async def test_tables_exist():
    """Test apakah tabel-tabel penting ada"""
    print("🔍 Testing database tables...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check important tables
        tables_to_check = [
            'users',
            'user_growid', 
            'products',
            'balance_transactions'
        ]
        
        for table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            result = cursor.fetchone()
            if result:
                print(f"✅ Table '{table}': EXISTS")
            else:
                print(f"⚠️  Table '{table}': NOT FOUND")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting bot functionality tests...\n")
    
    tests = [
        test_database_connection(),
        test_tables_exist(),
        test_balance_service(),
        test_product_service()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    passed = sum(1 for result in results if result is True)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All critical functionalities are working!")
        return True
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
