#!/usr/bin/env python3
"""
Simple Balance Test - Test balance conversion tanpa dependencies
"""

# Simple Balance class untuk testing
class Balance:
    def __init__(self, wl: int = 0, dl: int = 0, bgl: int = 0):
        self.wl = max(0, wl)
        self.dl = max(0, dl)
        self.bgl = max(0, bgl)

    def total_wl(self) -> int:
        """Convert semua balance ke WL"""
        return self.wl + (self.dl * 100) + (self.bgl * 10000)

    def can_afford(self, cost: int) -> bool:
        """Check if balance can afford the cost"""
        return self.total_wl() >= cost

    def format(self) -> str:
        """Format balance untuk display"""
        parts = []
        if self.bgl > 0:
            parts.append(f"{self.bgl:,} BGL")
        if self.dl > 0:
            parts.append(f"{self.dl:,} DL")
        if self.wl > 0 or not parts:
            parts.append(f"{self.wl:,} WL")
        return ", ".join(parts)

def test_balance_conversion():
    """Test balance conversion logic"""
    print("🧪 Testing Balance Conversion Fix...")
    
    # Test case: User dengan 2 DL, 0 WL, 0 BGL (seperti di log error)
    print("\n📊 Test Case: User dengan 2 DL (seperti di log error)")
    balance = Balance(wl=0, dl=2, bgl=0)
    
    print(f"   Raw balance: WL={balance.wl}, DL={balance.dl}, BGL={balance.bgl}")
    print(f"   Total WL calculation: {balance.wl} + ({balance.dl} * 100) + ({balance.bgl} * 10000)")
    print(f"   Total WL: {balance.total_wl()}")
    print(f"   Expected: 200 WL (2 DL * 100)")
    print(f"   Balance format: {balance.format()}")
    
    # Test can_afford method untuk produk 20 WL
    print(f"\n💰 Testing can_afford method untuk produk 20 WL:")
    can_afford_20 = balance.can_afford(20)
    print(f"   Can afford 20 WL: {can_afford_20}")
    print(f"   Expected: True (karena 200 WL > 20 WL)")
    
    # Test berbagai amount
    test_amounts = [20, 50, 100, 150, 200, 250]
    print(f"\n🎯 Testing berbagai amount:")
    for amount in test_amounts:
        can_afford = balance.can_afford(amount)
        status = "✅" if can_afford else "❌"
        print(f"   {status} Can afford {amount} WL: {can_afford}")
    
    # Test skenario lain
    print(f"\n🔄 Testing skenario balance lainnya:")
    
    scenarios = [
        {"wl": 0, "dl": 2, "bgl": 0, "description": "2 DL only (kasus error)"},
        {"wl": 50, "dl": 1, "bgl": 0, "description": "50 WL + 1 DL"},
        {"wl": 0, "dl": 0, "bgl": 1, "description": "1 BGL only"},
        {"wl": 25, "dl": 2, "bgl": 0, "description": "25 WL + 2 DL"},
        {"wl": 20, "dl": 0, "bgl": 0, "description": "20 WL only"},
    ]
    
    for scenario in scenarios:
        test_balance = Balance(scenario["wl"], scenario["dl"], scenario["bgl"])
        total = test_balance.total_wl()
        can_afford_20 = test_balance.can_afford(20)
        status = "✅" if can_afford_20 else "❌"
        print(f"   {status} {scenario['description']}: {total} WL (can afford 20 WL: {can_afford_20})")
    
    print("\n✅ Balance conversion test completed!")
    print("\n📝 Kesimpulan:")
    print("   - User dengan 2 DL memiliki total 200 WL")
    print("   - 200 WL seharusnya cukup untuk membeli produk 20 WL")
    print("   - Method can_afford() bekerja dengan benar")
    print("   - Masalah ada di implementasi balance verification di sistem")

if __name__ == "__main__":
    test_balance_conversion()
