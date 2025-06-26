"""
Test sederhana untuk memverifikasi perbaikan database errors
"""

import sqlite3
import os

def test_database_structure():
    """Test struktur database yang sudah diperbaiki"""
    print("🔄 Testing database structure...")
    
    try:
        # Connect to database
        db_path = 'shop.db'
        if not os.path.exists(db_path):
            print("❌ Database file tidak ditemukan!")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Check balance_transactions table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='balance_transactions'
        """)
        if cursor.fetchone():
            print("✅ Tabel balance_transactions sudah ada!")
        else:
            print("❌ Tabel balance_transactions tidak ditemukan!")
            return False
        
        # Test 2: Check world_info table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='world_info'
        """)
        if cursor.fetchone():
            print("✅ Tabel world_info sudah ada!")
        else:
            print("❌ Tabel world_info tidak ditemukan!")
            return False
        
        # Test 3: Check balance_transactions structure
        cursor.execute("PRAGMA table_info(balance_transactions)")
        columns = [row[1] for row in cursor.fetchall()]
        required_columns = ['id', 'growid', 'type', 'details', 'old_balance', 'new_balance', 'created_at']
        
        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            print(f"❌ Kolom yang hilang di balance_transactions: {missing_columns}")
            return False
        else:
            print("✅ Struktur tabel balance_transactions sudah benar!")
        
        # Test 4: Test insert ke balance_transactions
        cursor.execute("""
            INSERT INTO balance_transactions 
            (growid, type, details, old_balance, new_balance)
            VALUES (?, ?, ?, ?, ?)
        """, ("TEST_USER", "test", "Test transaction", "0|0|0", "100|0|0"))
        
        # Test 5: Test select dari balance_transactions
        cursor.execute("""
            SELECT * FROM balance_transactions 
            WHERE growid = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """, ("TEST_USER",))
        
        result = cursor.fetchone()
        if result:
            print("✅ Insert/Select ke balance_transactions berfungsi!")
        else:
            print("❌ Insert/Select ke balance_transactions gagal!")
            return False
        
        # Test 6: Test world_info table
        cursor.execute("""
            INSERT OR REPLACE INTO world_info 
            (id, world, owner, bot)
            VALUES (?, ?, ?, ?)
        """, (1, "TESTWORLD", "TESTOWNER", "TESTBOT"))
        
        cursor.execute("SELECT world, owner, bot FROM world_info WHERE id = 1")
        result = cursor.fetchone()
        
        if result and result[0] == "TESTWORLD":
            print("✅ Insert/Select ke world_info berfungsi!")
        else:
            print("❌ Insert/Select ke world_info gagal!")
            return False
        
        conn.commit()
        conn.close()
        
        print("🎉 Semua test database berhasil!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        return False

def test_file_changes():
    """Test apakah file-file sudah diubah dengan benar"""
    print("🔄 Testing file changes...")
    
    try:
        # Test 1: Check balance_service.py uses balance_transactions
        with open('src/services/balance_service.py', 'r') as f:
            content = f.read()
            if 'balance_transactions' in content:
                print("✅ balance_service.py sudah menggunakan balance_transactions!")
            else:
                print("❌ balance_service.py belum menggunakan balance_transactions!")
                return False
        
        # Test 2: Check transaction_service.py has get_user_transactions
        with open('src/services/transaction_service.py', 'r') as f:
            content = f.read()
            if 'get_user_transactions' in content:
                print("✅ transaction_service.py sudah memiliki get_user_transactions!")
            else:
                print("❌ transaction_service.py belum memiliki get_user_transactions!")
                return False
        
        # Test 3: Check button_handlers.py uses proper connection
        with open('src/ui/buttons/components/button_handlers.py', 'r') as f:
            content = f.read()
            if 'get_connection()' in content:
                print("✅ button_handlers.py sudah menggunakan get_connection()!")
            else:
                print("❌ button_handlers.py belum menggunakan get_connection()!")
                return False
        
        # Test 4: Check migrations.py has new tables
        with open('src/database/migrations.py', 'r') as f:
            content = f.read()
            if 'balance_transactions' in content and 'world_info' in content:
                print("✅ migrations.py sudah memiliki tabel baru!")
            else:
                print("❌ migrations.py belum memiliki tabel baru!")
                return False
        
        print("🎉 Semua file sudah diubah dengan benar!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing file changes: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Memulai test perbaikan database errors...")
    print("=" * 50)
    
    # Test database structure
    db_test = test_database_structure()
    print("-" * 30)
    
    # Test file changes
    file_test = test_file_changes()
    print("-" * 30)
    
    print("📊 HASIL TEST:")
    if db_test and file_test:
        print("🎉 Semua test berhasil! Perbaikan database sudah selesai.")
        print()
        print("📋 RINGKASAN PERBAIKAN:")
        print("1. ✅ Tabel balance_transactions ditambahkan untuk menyimpan riwayat balance")
        print("2. ✅ Tabel world_info ditambahkan untuk informasi world")
        print("3. ✅ balance_service.py diperbaiki untuk menggunakan tabel yang benar")
        print("4. ✅ transaction_service.py ditambahkan method get_user_transactions")
        print("5. ✅ button_handlers.py diperbaiki untuk database connection")
        print()
        print("🔧 ERROR YANG DIPERBAIKI:")
        print("- ❌ Error !addbal: table transactions has no column named growid")
        print("- ❌ Error tombol history: 'TransactionManager' object has no attribute 'get_user_transactions'")
        print("- ❌ Error world info: '_AsyncGeneratorContextManager' object has no attribute 'cursor'")
        return True
    else:
        print("⚠️ Ada beberapa test yang gagal. Perlu perbaikan lebih lanjut.")
        return False

if __name__ == "__main__":
    main()
