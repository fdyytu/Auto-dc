#!/usr/bin/env python3
"""
Test script untuk masalah display balance
"""

import sys
import os
sys.path.append('/home/user/workspace')

from src.database.models.balance import Balance

def test_balance_display_issue():
    """Test masalah display balance yang disebutkan user"""
    print("=== Testing Balance Display Issue ===")
    
    # Test case: User ada 100 DL lebih tapi tidak display jadi BGL
    print("\n1. Test: 100 DL lebih tidak auto-convert ke BGL")
    
    # Scenario A: 150 DL (seharusnya tetap 150 DL, tidak jadi 1 BGL + 50 DL)
    balance_a = Balance(wl=0, dl=150, bgl=0)
    print(f"   150 DL: {balance_a.format()} (Total: {balance_a.total_wl()} WL)")
    
    # Scenario B: 1000 DL (seharusnya tetap 1000 DL, tidak jadi 10 BGL)
    balance_b = Balance(wl=0, dl=1000, bgl=0)
    print(f"   1000 DL: {balance_b.format()} (Total: {balance_b.total_wl()} WL)")
    
    # Scenario C: 10000 DL (ini baru jadi 1 BGL)
    balance_c = Balance(wl=0, dl=10000, bgl=0)
    print(f"   10000 DL: {balance_c.format()} (Total: {balance_c.total_wl()} WL)")
    
    print("\n2. Test normalisasi balance (auto-convert)")
    # Test normalisasi - ini yang mungkin menyebabkan masalah display
    
    # 15000 DL -> seharusnya jadi 1 BGL + 5000 DL
    total_wl = 1500000  # 15000 DL
    normalized = Balance.from_wl(total_wl)
    print(f"   {total_wl} WL -> {normalized.format()}")
    print(f"   Details: WL={normalized.wl}, DL={normalized.dl}, BGL={normalized.bgl}")
    
    # 1000 DL -> seharusnya tetap 1000 DL
    total_wl2 = 100000  # 1000 DL
    normalized2 = Balance.from_wl(total_wl2)
    print(f"   {total_wl2} WL -> {normalized2.format()}")
    print(f"   Details: WL={normalized2.wl}, DL={normalized2.dl}, BGL={normalized2.bgl}")

def test_currency_rates():
    """Test currency rates"""
    print("\n=== Testing Currency Rates ===")
    print("1 DL = 100 WL")
    print("1 BGL = 10000 WL = 100 DL")
    
    # Test konversi
    print("\nKonversi test:")
    print(f"100 WL = {Balance.from_wl(100).format()}")
    print(f"1000 WL = {Balance.from_wl(1000).format()}")
    print(f"10000 WL = {Balance.from_wl(10000).format()}")
    print(f"100000 WL = {Balance.from_wl(100000).format()}")
    print(f"1000000 WL = {Balance.from_wl(1000000).format()}")

if __name__ == "__main__":
    test_balance_display_issue()
    test_currency_rates()
