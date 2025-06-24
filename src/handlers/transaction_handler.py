"""
Transaction Handler
Menangani processing transaksi dengan validasi lengkap
"""

import logging
from typing import Optional, Dict, Any
from discord.ext import commands
import discord

from src.services.transaction_service import TransactionService
from src.services.user_service import UserService
from src.utils.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)

class TransactionHandler:
    """Handler untuk processing transaksi"""
    
    def __init__(self, transaction_service: TransactionService, user_service: UserService):
        self.transaction_service = transaction_service
        self.user_service = user_service
        self.formatter = ResponseFormatter()
    
    async def process_purchase(self, ctx: commands.Context, product_code: str, quantity: int = 1) -> bool:
        """Process pembelian produk"""
        try:
            user = await self.user_service.get_user_by_discord_id(str(ctx.author.id))
            if not user:
                await ctx.send(self.formatter.error_message("Anda belum terdaftar"))
                return False
            
            result = await self.transaction_service.create_transaction(
                user['growid'], product_code, quantity
            )
            
            if result['success']:
                embed = self.formatter.success_embed(
                    "Transaksi Berhasil",
                    f"Pembelian {quantity}x {product_code} berhasil!"
                )
                await ctx.send(embed=embed)
                return True
            else:
                await ctx.send(self.formatter.error_message(result['message']))
                return False
                
        except Exception as e:
            logger.error(f"Error processing purchase: {e}")
            await ctx.send(self.formatter.error_message("Terjadi error saat memproses transaksi"))
            return False
    
    async def get_transaction_history(self, ctx: commands.Context, limit: int = 10) -> bool:
        """Ambil riwayat transaksi user"""
        try:
            user = await self.user_service.get_user_by_discord_id(str(ctx.author.id))
            if not user:
                await ctx.send(self.formatter.error_message("Anda belum terdaftar"))
                return False
            
            transactions = await self.transaction_service.get_user_transactions(user['growid'], limit)
            embed = self.formatter.transaction_history_embed(transactions)
            await ctx.send(embed=embed)
            return True
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return False
