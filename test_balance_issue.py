#!/usr/bin/env python3
"""
Test script untuk debug masalah balance
"""

import sys
import os
sys.path.append('/home/user/workspace')

from src.database.models.balance import Balance

def test_balance_calculation():
    """Test balance calculation dan can_afford method"""
    print("=== Testing Balance Calculation ===")
    
    # Test case dari log: WL=0, DL=1000, BGL=0
    balance = Balance(wl=0, dl=1000, bgl=0)
    
    print(f"Balance object: WL={balance.wl}, DL={balance.dl}, BGL={balance.bgl}")
    print(f"Total WL calculation: {balance.wl} + ({balance.dl} * 100) + ({balance.bgl} * 10000)")
    print(f"Total WL: {balance.total_wl()}")
    
    # Test can_afford dengan berbagai nilai
    test_costs = [10, 100, 1000, 10000, 100000, 100001]
    
    for cost in test_costs:
        can_afford = balance.can_afford(cost)
        print(f"Can afford {cost} WL: {can_afford}")
        
        if cost == 10:
            print(f"  -> Detailed check for 10 WL:")
            print(f"     balance.total_wl() = {balance.total_wl()}")
            print(f"     cost = {cost}")
            print(f"     balance.total_wl() >= cost = {balance.total_wl() >= cost}")

if __name__ == "__main__":
    test_balance_calculation()
