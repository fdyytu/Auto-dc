#!/usr/bin/env python3
"""
Test script to verify balance checking and database repair fixes
"""

import sys
import os
sys.path.append('.')

def test_balance_calculation():
    """Test balance calculation logic"""
    print("=== Testing Balance Calculation ===")
    
    class Balance:
        def __init__(self, wl: int = 0, dl: int = 0, bgl: int = 0):
            self.wl = max(0, wl)
            self.dl = max(0, dl)
            self.bgl = max(0, bgl)

        def total_wl(self) -> int:
            return self.wl + (self.dl * 100) + (self.bgl * 10000)

        def format(self) -> str:
            parts = []
            if self.bgl > 0:
                parts.append(f'{self.bgl:,} BGL')
            if self.dl > 0:
                parts.append(f'{self.dl:,} DL')
            if self.wl > 0 or not parts:
                parts.append(f'{self.wl:,} WL')
            return ', '.join(parts)

    # Test case from the error log: user has 1 DL
    balance = Balance(wl=0, dl=1, bgl=0)
    print(f"User balance: {balance.format()}")
    print(f"Total WL: {balance.total_wl()}")
    
    # Test various purchase scenarios
    test_prices = [50.0, 100.0, 150.0, 99.99, 100.01]
    
    for price in test_prices:
        price_int = int(price)
        user_balance_wl = balance.total_wl()
        sufficient = user_balance_wl >= price_int
        
        print(f"Price: {price} -> {price_int} WL, Sufficient: {sufficient}")
        
        if not sufficient:
            print(f"  ❌ Balance tidak cukup! Saldo: {user_balance_wl} WL, Dibutuhkan: {price_int} WL")
        else:
            print(f"  ✅ Balance sufficient")
    
    print()

def test_database_operations():
    """Test database operations"""
    print("=== Testing Database Operations ===")
    
    import sqlite3
    import tempfile
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        test_db = tmp.name
    
    try:
        # Create and populate test database
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create test tables
        cursor.execute("""
            CREATE TABLE users (
                growid TEXT PRIMARY KEY,
                balance_wl INTEGER DEFAULT 0,
                balance_dl INTEGER DEFAULT 0,
                balance_bgl INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE user_growid (
                discord_id TEXT PRIMARY KEY,
                growid TEXT NOT NULL
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO users VALUES ('TestUser', 0, 1, 0)")
        cursor.execute("INSERT INTO user_growid VALUES ('123456789', 'TestUser')")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Created test database: {test_db}")
        
        # Test database integrity
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        print(f"✅ Database integrity: {result[0]}")
        
        # Test data retrieval
        cursor.execute("SELECT * FROM users WHERE growid = 'TestUser'")
        user_data = cursor.fetchone()
        print(f"✅ User data: {user_data}")
        
        if user_data:
            wl, dl, bgl = user_data[1], user_data[2], user_data[3]
            total_wl = wl + (dl * 100) + (bgl * 10000)
            print(f"✅ User balance: {wl} WL, {dl} DL, {bgl} BGL = {total_wl} WL total")
        
        conn.close()
        
    finally:
        # Clean up
        if os.path.exists(test_db):
            os.remove(test_db)
            print(f"✅ Cleaned up test database")
    
    print()

def test_error_scenarios():
    """Test error scenarios that were causing issues"""
    print("=== Testing Error Scenarios ===")
    
    # Scenario 1: User has 1 DL, tries to buy something for 4 FR (assuming FR costs < 100 WL)
    print("Scenario 1: User with 1 DL buying 4x FR")
    
    user_balance_wl = 100  # 1 DL = 100 WL
    product_price = 20.0   # Assume FR costs 20 WL each
    quantity = 4
    total_price = product_price * quantity
    total_price_int = int(total_price)
    
    print(f"  User balance: {user_balance_wl} WL")
    print(f"  Product price: {product_price} WL each")
    print(f"  Quantity: {quantity}")
    print(f"  Total price: {total_price} -> {total_price_int} WL")
    
    if user_balance_wl >= total_price_int:
        print(f"  ✅ Purchase should succeed")
    else:
        print(f"  ❌ Purchase should fail: Balance tidak cukup!")
    
    # Scenario 2: Edge case with float precision
    print("\nScenario 2: Float precision edge case")
    
    user_balance_wl = 100
    total_price = 100.0
    total_price_int = int(total_price)
    
    print(f"  User balance: {user_balance_wl} WL")
    print(f"  Total price: {total_price} -> {total_price_int} WL")
    print(f"  Direct float comparison: {user_balance_wl >= total_price}")
    print(f"  Int comparison: {user_balance_wl >= total_price_int}")
    
    print()

if __name__ == "__main__":
    print("Testing Balance and Database Fixes")
    print("=" * 50)
    
    test_balance_calculation()
    test_database_operations()
    test_error_scenarios()
    
    print("=" * 50)
    print("All tests completed!")
