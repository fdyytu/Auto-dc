#!/usr/bin/env python3
"""
Test script to verify the balance verification fix
Tests the exact scenario from the error logs: user with 100 DL trying to buy 1 WL item
"""

import sys
import os
sys.path.append('/home/user/workspace')

from src.database.models.balance import Balance

def test_balance_verification():
    """Test the balance verification with the exact scenario from logs"""
    print("🧪 Testing Balance Verification Fix")
    print("=" * 50)
    
    # Test case 1: Exact scenario from logs - 100 DL balance, 1 WL cost
    print("\n📋 Test Case 1: 100 DL balance, 1 WL cost")
    balance = Balance(wl=0, dl=100, bgl=0)
    cost = 1
    
    print(f"Balance: WL={balance.wl}, DL={balance.dl}, BGL={balance.bgl}")
    print(f"Total WL: {balance.total_wl()}")
    print(f"Cost: {cost} WL")
    
    can_afford = balance.can_afford(cost)
    manual_check = balance.total_wl() >= cost
    
    print(f"can_afford() result: {can_afford}")
    print(f"Manual check: {balance.total_wl()} >= {cost} = {manual_check}")
    
    if can_afford and manual_check:
        print("✅ Test Case 1 PASSED")
    else:
        print("❌ Test Case 1 FAILED")
        return False
    
    # Test case 2: Edge case - exactly enough balance
    print("\n📋 Test Case 2: Exactly enough balance")
    balance2 = Balance(wl=50, dl=0, bgl=0)
    cost2 = 50
    
    print(f"Balance: WL={balance2.wl}, DL={balance2.dl}, BGL={balance2.bgl}")
    print(f"Total WL: {balance2.total_wl()}")
    print(f"Cost: {cost2} WL")
    
    can_afford2 = balance2.can_afford(cost2)
    manual_check2 = balance2.total_wl() >= cost2
    
    print(f"can_afford() result: {can_afford2}")
    print(f"Manual check: {balance2.total_wl()} >= {cost2} = {manual_check2}")
    
    if can_afford2 and manual_check2:
        print("✅ Test Case 2 PASSED")
    else:
        print("❌ Test Case 2 FAILED")
        return False
    
    # Test case 3: Insufficient balance
    print("\n📋 Test Case 3: Insufficient balance")
    balance3 = Balance(wl=10, dl=0, bgl=0)
    cost3 = 50
    
    print(f"Balance: WL={balance3.wl}, DL={balance3.dl}, BGL={balance3.bgl}")
    print(f"Total WL: {balance3.total_wl()}")
    print(f"Cost: {cost3} WL")
    
    can_afford3 = balance3.can_afford(cost3)
    manual_check3 = balance3.total_wl() >= cost3
    
    print(f"can_afford() result: {can_afford3}")
    print(f"Manual check: {balance3.total_wl()} >= {cost3} = {manual_check3}")
    
    if not can_afford3 and not manual_check3:
        print("✅ Test Case 3 PASSED")
    else:
        print("❌ Test Case 3 FAILED")
        return False
    
    # Test case 4: Mixed currency balance
    print("\n📋 Test Case 4: Mixed currency balance")
    balance4 = Balance(wl=50, dl=5, bgl=1)
    cost4 = 10000  # Should be affordable with 1 BGL
    
    print(f"Balance: WL={balance4.wl}, DL={balance4.dl}, BGL={balance4.bgl}")
    print(f"Total WL: {balance4.total_wl()}")
    print(f"Cost: {cost4} WL")
    
    can_afford4 = balance4.can_afford(cost4)
    manual_check4 = balance4.total_wl() >= cost4
    
    print(f"can_afford() result: {can_afford4}")
    print(f"Manual check: {balance4.total_wl()} >= {cost4} = {manual_check4}")
    
    if can_afford4 and manual_check4:
        print("✅ Test Case 4 PASSED")
    else:
        print("❌ Test Case 4 FAILED")
        return False
    
    print("\n🎉 All test cases PASSED!")
    print("✅ Balance verification fix is working correctly")
    return True

if __name__ == "__main__":
    success = test_balance_verification()
    sys.exit(0 if success else 1)
