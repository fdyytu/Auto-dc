"""
Balance class dan utility functions
Author: fdyytu
Created at: 2025-03-07 18:04:56 UTC
Last Modified: 2025-03-10 10:09:16 UTC
"""

from typing import Union

# Balance Class yang lengkap
class Balance:
    def __init__(self, wl: int = 0, dl: int = 0, bgl: int = 0):
        self.wl = max(0, wl)
        self.dl = max(0, dl)
        self.bgl = max(0, bgl)
        self.MIN_AMOUNT = 0
        self.MAX_AMOUNT = 1000000  # 1M WLS
        self.DEFAULT_AMOUNT = 0
        self.DONATION_MIN = 10     # 10 WLS minimum donation

    def total_wl(self) -> int:
        """Convert semua balance ke WL"""
        return self.wl + (self.dl * 100) + (self.bgl * 10000)

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

    @classmethod
    def from_wl(cls, total_wl: int) -> 'Balance':
        """Buat Balance object dari total WL"""
        bgl = total_wl // 10000
        remaining = total_wl % 10000
        dl = remaining // 100
        wl = remaining % 100
        return cls(wl, dl, bgl)

    @classmethod
    def from_string(cls, balance_str: str) -> 'Balance':
        """Create Balance object from string representation"""
        try:
            if not balance_str:
                return cls()
            parts = balance_str.split(',')
            wl = dl = bgl = 0
            for part in parts:
                part = part.strip()
                if 'WL' in part:
                    wl = int(part.replace('WL', '').strip())
                elif 'DL' in part:
                    dl = int(part.replace('DL', '').strip())
                elif 'BGL' in part:
                    bgl = int(part.replace('BGL', '').strip())
            return cls(wl, dl, bgl)
        except Exception:
            return cls()

    def __eq__(self, other):
        if not isinstance(other, Balance):
            return False
        return self.total_wl() == other.total_wl()

    def __str__(self):
        return self.format()

    def validate(self) -> bool:
        """Validasi balance"""
        total = self.total_wl()
        return (
            self.MIN_AMOUNT <= total <= self.MAX_AMOUNT and
            all(isinstance(x, int) and x >= 0 for x in [self.wl, self.dl, self.bgl])
        )

    def can_afford(self, cost: Union[int, float, 'Balance']) -> bool:
        """Check if balance can afford the cost"""
        if isinstance(cost, (int, float)):
            # Convert float to int for comparison (WL is always integer)
            cost_int = int(cost)
            return self.total_wl() >= cost_int
        elif isinstance(cost, Balance):
            return self.total_wl() >= cost.total_wl()
        return False

    def subtract(self, amount: Union[int, 'Balance']) -> 'Balance':
        """Subtract amount from balance and return new balance"""
        if isinstance(amount, int):
            new_total = max(0, self.total_wl() - amount)
        elif isinstance(amount, Balance):
            new_total = max(0, self.total_wl() - amount.total_wl())
        else:
            return Balance(self.wl, self.dl, self.bgl)
        
        return Balance.from_wl(new_total)

    def add(self, amount: Union[int, 'Balance']) -> 'Balance':
        """Add amount to balance and return new balance"""
        if isinstance(amount, int):
            new_total = min(self.MAX_AMOUNT, self.total_wl() + amount)
        elif isinstance(amount, Balance):
            new_total = min(self.MAX_AMOUNT, self.total_wl() + amount.total_wl())
        else:
            return Balance(self.wl, self.dl, self.bgl)
        
        return Balance.from_wl(new_total)

    def copy(self) -> 'Balance':
        """Create a copy of this balance"""
        return Balance(self.wl, self.dl, self.bgl)
