#!/usr/bin/env python3
"""
Test script untuk memverifikasi perbaikan balance issue
"""

import sys
import os
sys.path.append('/home/user/workspace')

from src.database.models.balance import Balance

def test_balance_scenarios():
    """Test berbagai skenario balance"""
    print("=== Testing Balance Fix Scenarios ===")
    
    # Scenario 1: User dengan 1000 DL (dari log)
    print("\n1. Scenario dari log: 1000 DL, beli produk 10 WL")
    balance1 = Balance(wl=0, dl=1000, bgl=0)
    cost1 = 10
    print(f"   Balance: {balance1.format()} (Total: {balance1.total_wl()} WL)")
    print(f"   Cost: {cost1} WL")
    print(f"   Can afford: {balance1.can_afford(cost1)}")
    print(f"   Manual check: {balance1.total_wl()} >= {cost1} = {balance1.total_wl() >= cost1}")
    
    # Scenario 2: User dengan 100 DL lebih
    print("\n2. Scenario: 100 DL lebih, beli produk 50 WL")
    balance2 = Balance(wl=50, dl=100, bgl=0)
    cost2 = 50
    print(f"   Balance: {balance2.format()} (Total: {balance2.total_wl()} WL)")
    print(f"   Cost: {cost2} WL")
    print(f"   Can afford: {balance2.can_afford(cost2)}")
    
    # Scenario 3: Edge case - exact balance
    print("\n3. Edge case: Exact balance")
    balance3 = Balance(wl=0, dl=1, bgl=0)  # 100 WL
    cost3 = 100
    print(f"   Balance: {balance3.format()} (Total: {balance3.total_wl()} WL)")
    print(f"   Cost: {cost3} WL")
    print(f"   Can afford: {balance3.can_afford(cost3)}")
    
    # Scenario 4: Insufficient balance
    print("\n4. Insufficient balance case")
    balance4 = Balance(wl=50, dl=0, bgl=0)  # 50 WL
    cost4 = 100
    print(f"   Balance: {balance4.format()} (Total: {balance4.total_wl()} WL)")
    print(f"   Cost: {cost4} WL")
    print(f"   Can afford: {balance4.can_afford(cost4)}")
    
    # Test dengan float costs (seperti dari database)
    print("\n5. Float cost test")
    balance5 = Balance(wl=0, dl=1000, bgl=0)
    cost5_float = 10.0
    cost5_int = int(cost5_float)
    print(f"   Balance: {balance5.format()} (Total: {balance5.total_wl()} WL)")
    print(f"   Cost float: {cost5_float} WL")
    print(f"   Cost int: {cost5_int} WL")
    print(f"   Can afford float: {balance5.can_afford(cost5_float)}")
    print(f"   Can afford int: {balance5.can_afford(cost5_int)}")

def test_balance_conversion():
    """Test konversi balance"""
    print("\n=== Testing Balance Conversion ===")
    
    # Test from_wl method
    total_wl = 100000  # 1000 DL
    balance_converted = Balance.from_wl(total_wl)
    print(f"Converting {total_wl} WL:")
    print(f"   Result: {balance_converted.format()}")
    print(f"   WL: {balance_converted.wl}, DL: {balance_converted.dl}, BGL: {balance_converted.bgl}")
    print(f"   Back to total: {balance_converted.total_wl()}")

if __name__ == "__main__":
    test_balance_scenarios()
    test_balance_conversion()
