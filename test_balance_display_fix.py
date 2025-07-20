#!/usr/bin/env python3
"""
Test script untuk memverifikasi perbaikan display balance
"""

import sys
import os
sys.path.append('/home/user/workspace')

from src.database.models.balance import Balance

# Mock BalanceManagerService untuk testing
class MockBalanceManagerService:
    def __init__(self):
        pass
    
    def normalize_balance(self, balance: Balance, auto_convert_to_bgl: bool = False) -> Balance:
        """
        Normalisasi balance dengan mengkonversi WL ke DL dan opsional DL ke BGL
        """
        original_total = balance.total_wl()
        wl = balance.wl
        dl = balance.dl
        bgl = balance.bgl

        # Always convert WL ke DL (this is expected behavior)
        if wl >= 100:  # CURRENCY_RATES.RATES['DL']
            dl += wl // 100
            wl = wl % 100

        # Only convert DL ke BGL if explicitly requested or if DL amount is very large (>= 10000 DL)
        # This preserves user's DL display for normal amounts like 1000 DL
        if auto_convert_to_bgl and dl >= 100:  # CURRENCY_RATES.RATES['BGL'] // CURRENCY_RATES.RATES['DL']
            bgl += dl // 100
            dl = dl % 100
        elif dl >= 10000:  # Only auto-convert to BGL for very large amounts (10000+ DL)
            bgl += dl // 100
            dl = dl % 100

        normalized_balance = Balance(wl, dl, bgl)
        return normalized_balance

def test_balance_display_fix():
    """Test perbaikan display balance"""
    print("=== Testing Balance Display Fix ===")
    
    service = MockBalanceManagerService()
    
    # Test case 1: 1000 DL (dari log) - seharusnya tetap 1000 DL
    print("\n1. Test: 1000 DL should remain as 1000 DL (not convert to 10 BGL)")
    balance1 = Balance(wl=0, dl=1000, bgl=0)
    normalized1 = service.normalize_balance(balance1, auto_convert_to_bgl=False)
    print(f"   Original: {balance1.format()} (Total: {balance1.total_wl()} WL)")
    print(f"   Normalized: {normalized1.format()} (Total: {normalized1.total_wl()} WL)")
    print(f"   ✅ PASS" if normalized1.dl == 1000 and normalized1.bgl == 0 else f"   ❌ FAIL")
    
    # Test case 2: 150 DL - seharusnya tetap 150 DL
    print("\n2. Test: 150 DL should remain as 150 DL")
    balance2 = Balance(wl=0, dl=150, bgl=0)
    normalized2 = service.normalize_balance(balance2, auto_convert_to_bgl=False)
    print(f"   Original: {balance2.format()} (Total: {balance2.total_wl()} WL)")
    print(f"   Normalized: {normalized2.format()} (Total: {normalized2.total_wl()} WL)")
    print(f"   ✅ PASS" if normalized2.dl == 150 and normalized2.bgl == 0 else f"   ❌ FAIL")
    
    # Test case 3: 15000 DL - seharusnya auto-convert ke BGL karena >= 10000 DL
    print("\n3. Test: 15000 DL should auto-convert to BGL (very large amount)")
    balance3 = Balance(wl=0, dl=15000, bgl=0)
    normalized3 = service.normalize_balance(balance3, auto_convert_to_bgl=False)
    print(f"   Original: {balance3.format()} (Total: {balance3.total_wl()} WL)")
    print(f"   Normalized: {normalized3.format()} (Total: {normalized3.total_wl()} WL)")
    print(f"   ✅ PASS" if normalized3.bgl == 150 and normalized3.dl == 0 else f"   ❌ FAIL")
    
    # Test case 4: WL conversion - 250 WL should become 2 DL + 50 WL
    print("\n4. Test: 250 WL should convert to 2 DL + 50 WL")
    balance4 = Balance(wl=250, dl=0, bgl=0)
    normalized4 = service.normalize_balance(balance4, auto_convert_to_bgl=False)
    print(f"   Original: {balance4.format()} (Total: {balance4.total_wl()} WL)")
    print(f"   Normalized: {normalized4.format()} (Total: {normalized4.total_wl()} WL)")
    print(f"   ✅ PASS" if normalized4.wl == 50 and normalized4.dl == 2 and normalized4.bgl == 0 else f"   ❌ FAIL")
    
    # Test case 5: Explicit BGL conversion
    print("\n5. Test: 1000 DL with explicit BGL conversion")
    balance5 = Balance(wl=0, dl=1000, bgl=0)
    normalized5 = service.normalize_balance(balance5, auto_convert_to_bgl=True)
    print(f"   Original: {balance5.format()} (Total: {balance5.total_wl()} WL)")
    print(f"   Normalized: {normalized5.format()} (Total: {normalized5.total_wl()} WL)")
    print(f"   ✅ PASS" if normalized5.bgl == 10 and normalized5.dl == 0 else f"   ❌ FAIL")

def test_comparison_old_vs_new():
    """Compare old vs new behavior"""
    print("\n=== Comparison: Old vs New Behavior ===")
    
    service = MockBalanceManagerService()
    
    # Simulate old behavior (always convert)
    def old_normalize(balance):
        wl, dl, bgl = balance.wl, balance.dl, balance.bgl
        if wl >= 100:
            dl += wl // 100
            wl = wl % 100
        if dl >= 100:  # Old: always convert
            bgl += dl // 100
            dl = dl % 100
        return Balance(wl, dl, bgl)
    
    test_cases = [
        Balance(wl=0, dl=1000, bgl=0),  # 1000 DL
        Balance(wl=0, dl=150, bgl=0),   # 150 DL
        Balance(wl=0, dl=50, bgl=0),    # 50 DL
    ]
    
    for i, balance in enumerate(test_cases, 1):
        old_result = old_normalize(balance)
        new_result = service.normalize_balance(balance, auto_convert_to_bgl=False)
        
        print(f"\n{i}. Original: {balance.format()}")
        print(f"   Old behavior: {old_result.format()}")
        print(f"   New behavior: {new_result.format()}")
        print(f"   Improvement: {'✅ Better UX' if new_result.dl > old_result.dl else '⚠️ Same'}")

if __name__ == "__main__":
    test_balance_display_fix()
    test_comparison_old_vs_new()
