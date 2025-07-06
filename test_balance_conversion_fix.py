#!/usr/bin/env python3
"""
Test Balance Conversion Fix
Menguji apakah balance conversion DL ke WL bekerja dengan benar
"""

import sys
import os
sys.path.append('/home/user/workspace')

from src.config.constants.bot_constants import Balance, CURRENCY_RATES

def test_balance_conversion():
    """Test balance conversion logic"""
    print("🧪 Testing Balance Conversion Fix...")
    
    # Test case: User dengan 2 DL, 0 WL, 0 BGL
    print("\n📊 Test Case: User dengan 2 DL")
    balance = Balance(wl=0, dl=2, bgl=0)
    
    print(f"   Raw balance: WL={balance.wl}, DL={balance.dl}, BGL={balance.bgl}")
    print(f"   Total WL calculation: {balance.wl} + ({balance.dl} * 100) + ({balance.bgl} * 10000)")
    print(f"   Total WL: {balance.total_wl()}")
    print(f"   Expected: 200 WL (2 DL * 100)")
    
    # Test can_afford method
    test_amounts = [20, 50, 100, 150, 200, 250]
    print(f"\n💰 Testing can_afford method:")
    for amount in test_amounts:
        can_afford = balance.can_afford(amount)
        print(f"   Can afford {amount} WL: {can_afford}")
    
    # Test currency rates
    print(f"\n🔄 Currency Rates:")
    print(f"   1 WL = {CURRENCY_RATES.RATES['WL']} WL")
    print(f"   1 DL = {CURRENCY_RATES.RATES['DL']} WL")
    print(f"   1 BGL = {CURRENCY_RATES.RATES['BGL']} WL")
    
    # Test various balance scenarios
    print(f"\n🎯 Testing Various Balance Scenarios:")
    
    scenarios = [
        {"wl": 0, "dl": 2, "bgl": 0, "description": "2 DL only"},
        {"wl": 50, "dl": 1, "bgl": 0, "description": "50 WL + 1 DL"},
        {"wl": 0, "dl": 0, "bgl": 1, "description": "1 BGL only"},
        {"wl": 25, "dl": 2, "bgl": 0, "description": "25 WL + 2 DL"},
    ]
    
    for scenario in scenarios:
        test_balance = Balance(scenario["wl"], scenario["dl"], scenario["bgl"])
        total = test_balance.total_wl()
        print(f"   {scenario['description']}: {total} WL")
        print(f"     Can afford 20 WL: {test_balance.can_afford(20)}")
        print(f"     Can afford 100 WL: {test_balance.can_afford(100)}")
        print(f"     Can afford 200 WL: {test_balance.can_afford(200)}")
    
    print("\n✅ Balance conversion test completed!")

if __name__ == "__main__":
    test_balance_conversion()
