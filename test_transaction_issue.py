#!/usr/bin/env python3
"""
Test script untuk debug masalah transaction
"""

import sys
import os
sys.path.append('/home/user/workspace')

from src.database.models.balance import Balance

def test_transaction_scenario():
    """Test skenario yang sama dengan log"""
    print("=== Testing Transaction Scenario ===")
    
    # Dari log: Balance=100000 WL, Required=10 WL
    balance = Balance(wl=0, dl=1000, bgl=0)
    
    print(f"User balance: {balance.total_wl()} WL")
    print(f"Balance details: WL={balance.wl}, DL={balance.dl}, BGL={balance.bgl}")
    
    # Test dengan berbagai tipe data untuk harga
    product_price = 10.0  # float dari database
    quantity = 1
    
    # Cara 1: seperti di BuyModal (line 332)
    total_price_int = int(float(product_price) * quantity)
    print(f"\nBuyModal calculation:")
    print(f"  product_price = {product_price} (type: {type(product_price)})")
    print(f"  quantity = {quantity}")
    print(f"  total_price = float(product_price) * quantity = {float(product_price) * quantity}")
    print(f"  total_price_int = int(total_price) = {total_price_int} (type: {type(total_price_int)})")
    print(f"  can_afford({total_price_int}) = {balance.can_afford(total_price_int)}")
    
    # Cara 2: seperti di TransactionManager (line 206)
    total_price = product_price * quantity
    print(f"\nTransactionManager calculation:")
    print(f"  total_price = product_price * quantity = {total_price} (type: {type(total_price)})")
    print(f"  can_afford({total_price}) = {balance.can_afford(total_price)}")
    
    # Test edge cases
    print(f"\nEdge case tests:")
    print(f"  can_afford(10) = {balance.can_afford(10)}")
    print(f"  can_afford(10.0) = {balance.can_afford(10.0)}")
    print(f"  can_afford(10.5) = {balance.can_afford(10.5)}")

if __name__ == "__main__":
    test_transaction_scenario()
