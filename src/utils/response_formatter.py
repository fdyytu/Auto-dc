"""
Response Formatter
Utility untuk formatting response Discord dengan konsisten
"""

import discord
from typing import List, Dict, Any
from datetime import datetime

class ResponseFormatter:
    """Formatter untuk response Discord"""
    
    def __init__(self):
        self.colors = {
            'success': 0x00ff00,
            'error': 0xff0000,
            'warning': 0xffff00,
            'info': 0x0099ff,
            'primary': 0x7289da
        }
    
    def error_message(self, message: str) -> str:
        """Format pesan error sederhana"""
        return f"❌ {message}"
    
    def success_message(self, message: str) -> str:
        """Format pesan sukses sederhana"""
        return f"✅ {message}"
    
    def success_embed(self, title: str, description: str) -> discord.Embed:
        """Buat embed sukses"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=self.colors['success'],
            timestamp=datetime.utcnow()
        )
        return embed
    
    def error_embed(self, title: str, description: str) -> discord.Embed:
        """Buat embed error"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=self.colors['error'],
            timestamp=datetime.utcnow()
        )
        return embed
    
    def transaction_history_embed(self, transactions: List[Dict[str, Any]]) -> discord.Embed:
        """Format riwayat transaksi"""
        embed = discord.Embed(
            title="📋 Riwayat Transaksi",
            color=self.colors['info'],
            timestamp=datetime.utcnow()
        )
        
        if not transactions:
            embed.description = "Tidak ada transaksi"
            return embed
        
        for i, tx in enumerate(transactions[:5], 1):
            value_text = f"Jumlah: {tx.get('quantity', 0)}\nHarga: {tx.get('total_price', 0):,} WL"
            embed.add_field(
                name=f"{i}. {tx.get('product_name', 'Unknown')}",
                value=value_text,
                inline=True
            )
        
        return embed
