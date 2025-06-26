"""
Validators
Utility untuk validasi input dan data
"""

import re
import logging
from typing import Optional, Union, List

logger = logging.getLogger(__name__)

class InputValidator:
    """Validator untuk input user"""
    
    @staticmethod
    def validate_growid(growid: str) -> bool:
        """Validasi format growid"""
        if not growid or not isinstance(growid, str):
            return False
        
        # Growid harus 3-18 karakter, alphanumeric
        if not re.match(r'^[a-zA-Z0-9]{3,18}$', growid):
            return False
        
        return True
    
    @staticmethod
    def validate_discord_id(discord_id: Union[str, int]) -> bool:
        """Validasi Discord ID"""
        try:
            discord_id = str(discord_id)
            return discord_id.isdigit() and len(discord_id) >= 17
        except:
            return False
    
    @staticmethod
    def validate_product_code(code: str) -> bool:
        """Validasi kode produk"""
        if not code or not isinstance(code, str):
            return False
        
        # Kode produk harus 2-10 karakter, alphanumeric dan underscore
        return re.match(r'^[a-zA-Z0-9_]{2,10}$', code) is not None
    
    @staticmethod
    def validate_price(price: Union[str, int]) -> Optional[int]:
        """Validasi dan konversi harga"""
        try:
            price_int = int(price)
            return price_int if price_int > 0 else None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def validate_quantity(quantity: Union[str, int]) -> Optional[int]:
        """Validasi dan konversi quantity"""
        try:
            qty_int = int(quantity)
            return qty_int if 1 <= qty_int <= 100 else None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def validate_amount(amount: Union[str, int]) -> Optional[int]:
        """Validasi dan konversi amount untuk balance"""
        try:
            amount_int = int(amount)
            return amount_int if amount_int > 0 else None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 500) -> str:
        """Sanitize text input"""
        if not text or not isinstance(text, str):
            return ""
        
        # Remove dangerous characters
        text = re.sub(r'[<>@&]', '', text)
        
        # Limit length
        return text[:max_length].strip()
    
    @staticmethod
    def validate_channel_id(channel_id: Union[str, int]) -> bool:
        """Validasi Channel ID"""
        try:
            channel_id = str(channel_id)
            return channel_id.isdigit() and len(channel_id) >= 17
        except:
            return False

class DataValidator:
    """Validator untuk data dari database"""
    
    @staticmethod
    def validate_user_data(user_data: dict) -> bool:
        """Validasi data user"""
        required_fields = ['growid', 'balance_wl', 'balance_dl', 'balance_bgl']
        
        if not isinstance(user_data, dict):
            return False
        
        for field in required_fields:
            if field not in user_data:
                return False
        
        return True
    
    @staticmethod
    def validate_product_data(product_data: dict) -> bool:
        """Validasi data produk"""
        required_fields = ['code', 'name', 'price']
        
        if not isinstance(product_data, dict):
            return False
        
        for field in required_fields:
            if field not in product_data:
                return False
        
        return True
    
    @staticmethod
    def validate_transaction_data(transaction_data: dict) -> bool:
        """Validasi data transaksi"""
        required_fields = ['buyer_id', 'product_code', 'quantity', 'total_price']
        
        if not isinstance(transaction_data, dict):
            return False
        
        for field in required_fields:
            if field not in transaction_data:
                return False
        
        return True

# Instance global untuk kemudahan akses
input_validator = InputValidator()
data_validator = DataValidator()
