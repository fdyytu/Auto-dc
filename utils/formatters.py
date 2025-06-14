"""
Formatters
Utility untuk formatting message dan data
"""

import discord
from datetime import datetime
from typing import Dict, Any, List, Optional

class MessageFormatter:
    """Formatter untuk Discord messages"""
    
    @staticmethod
    def create_embed(title: str, description: str = None, color: int = 0x0099ff) -> discord.Embed:
        """Buat embed dasar"""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.timestamp = datetime.utcnow()
        return embed
    
    @staticmethod
    def success_embed(title: str, description: str = None) -> discord.Embed:
        """Embed untuk pesan sukses"""
        return MessageFormatter.create_embed(f"✅ {title}", description, 0x00ff00)
    
    @staticmethod
    def error_embed(title: str, description: str = None) -> discord.Embed:
        """Embed untuk pesan error"""
        return MessageFormatter.create_embed(f"❌ {title}", description, 0xff0000)
    
    @staticmethod
    def warning_embed(title: str, description: str = None) -> discord.Embed:
        """Embed untuk pesan warning"""
        return MessageFormatter.create_embed(f"⚠️ {title}", description, 0xffaa00)
    
    @staticmethod
    def info_embed(title: str, description: str = None) -> discord.Embed:
        """Embed untuk pesan info"""
        return MessageFormatter.create_embed(f"ℹ️ {title}", description, 0x0099ff)
    
    @staticmethod
    def format_balance_embed(user_data: Dict[str, Any]) -> discord.Embed:
        """Format embed untuk balance user"""
        embed = MessageFormatter.create_embed("💰 Balance Anda", color=0x00ff00)
        embed.add_field(name="World Lock", value=f"{user_data.get('balance_wl', 0):,}", inline=True)
        embed.add_field(name="Diamond Lock", value=f"{user_data.get('balance_dl', 0):,}", inline=True)
        embed.add_field(name="Blue Gem Lock", value=f"{user_data.get('balance_bgl', 0):,}", inline=True)
        embed.set_footer(text=f"GrowID: {user_data.get('growid', 'Unknown')}")
        return embed
    
    @staticmethod
    def format_product_list_embed(products: List[Dict[str, Any]], stock_counts: Dict[str, int]) -> discord.Embed:
        """Format embed untuk daftar produk"""
        embed = MessageFormatter.create_embed("🛒 Daftar Produk")
        
        if not products:
            embed.description = "Tidak ada produk tersedia."
            return embed
        
        for product in products[:10]:  # Limit 10 products
            code = product['code']
            stock = stock_counts.get(code, 0)
            status = "✅ Tersedia" if stock > 0 else "❌ Habis"
            
            embed.add_field(
                name=f"{product['name']} ({code})",
                value=f"Harga: {product['price']:,} WL\nStock: {stock} | {status}",
                inline=True
            )
        
        return embed
    
    @staticmethod
    def format_product_detail_embed(product: Dict[str, Any], stock_count: int) -> discord.Embed:
        """Format embed untuk detail produk"""
        embed = MessageFormatter.create_embed(f"📦 {product['name']}")
        embed.add_field(name="Kode", value=product['code'], inline=True)
        embed.add_field(name="Harga", value=f"{product['price']:,} WL", inline=True)
        embed.add_field(name="Stock", value=stock_count, inline=True)
        
        if product.get('description'):
            embed.add_field(name="Deskripsi", value=product['description'], inline=False)
        
        status = "✅ Tersedia" if stock_count > 0 else "❌ Habis"
        embed.add_field(name="Status", value=status, inline=True)
        
        return embed

class DataFormatter:
    """Formatter untuk data processing"""
    
    @staticmethod
    def format_currency(amount: int, currency: str = "WL") -> str:
        """Format currency dengan separator"""
        return f"{amount:,} {currency}"
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """Format percentage"""
        return f"{value:.{decimals}f}%"
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime"""
        return dt.strftime(format_str)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text dengan suffix"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def format_user_mention(user_id: str) -> str:
        """Format user mention"""
        return f"<@{user_id}>"
    
    @staticmethod
    def format_channel_mention(channel_id: str) -> str:
        """Format channel mention"""
        return f"<#{channel_id}>"
    
    @staticmethod
    def format_role_mention(role_id: str) -> str:
        """Format role mention"""
        return f"<@&{role_id}>"

class LogFormatter:
    """Formatter untuk logging"""
    
    @staticmethod
    def format_transaction_log(transaction: Dict[str, Any]) -> str:
        """Format log transaksi"""
        return (
            f"Transaction #{transaction.get('id')} | "
            f"Buyer: {transaction.get('buyer_id')} | "
            f"Product: {transaction.get('product_code')} | "
            f"Qty: {transaction.get('quantity')} | "
            f"Total: {transaction.get('total_price'):,} WL"
        )
    
    @staticmethod
    def format_admin_log(action: str, admin_id: str, target: str = None, details: str = None) -> str:
        """Format log admin"""
        log_parts = [f"Admin: {admin_id}", f"Action: {action}"]
        
        if target:
            log_parts.append(f"Target: {target}")
        if details:
            log_parts.append(f"Details: {details}")
        
        return " | ".join(log_parts)

# Instance global
message_formatter = MessageFormatter()
data_formatter = DataFormatter()
log_formatter = LogFormatter()
