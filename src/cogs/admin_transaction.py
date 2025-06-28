"""
Admin Transaction Management - Manajemen transaksi dan history
Menangani command untuk melihat history transaksi dan stock
"""

import discord
from discord.ext import commands
import logging

from src.cogs.admin_base import AdminBaseCog
from src.services.transaction_service import TransactionService
from src.services.product_service import ProductService
from src.utils.formatters import message_formatter
from src.utils.validators import input_validator

logger = logging.getLogger(__name__)

class AdminTransactionCog(AdminBaseCog):
    """Cog untuk manajemen transaksi admin"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.transaction_service = TransactionService(bot.db_manager)
        self.product_service = ProductService(bot.db_manager)
    
    @commands.command(name="trxhistory")
    async def transaction_history(self, ctx, growid: str, limit: int = 10):
        """Lihat history transaksi user"""
        try:
            # Validasi limit
            if limit < 1 or limit > 50:
                await ctx.send(embed=message_formatter.error_embed("Limit harus antara 1-50"))
                return
            
            # Ambil history transaksi
            response = await self.transaction_service.get_user_transactions(growid, limit)
            
            if not response.success or not response.data:
                await ctx.send(embed=message_formatter.info_embed(f"Tidak ada history transaksi untuk {growid}"))
                return
            
            embed = discord.Embed(
                title=f"📊 History Transaksi - {growid}",
                description=f"Menampilkan {len(response.data)} transaksi terakhir",
                color=0x00ff00
            )
            
            for i, trx in enumerate(response.data[:10], 1):  # Limit display to 10
                trx_type = trx.get('type', 'Unknown')
                amount = trx.get('amount', 0)
                currency = trx.get('currency', 'WL')
                timestamp = trx.get('timestamp', 'Unknown')
                
                embed.add_field(
                    name=f"{i}. {trx_type}",
                    value=f"Amount: {amount:,} {currency}\nWaktu: {timestamp}",
                    inline=True
                )
            
            if len(response.data) > 10:
                embed.set_footer(text=f"Menampilkan 10 dari {len(response.data)} transaksi")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error transaction history: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat mengambil history transaksi"))
    
    @commands.command(name="stockhistory")
    async def stock_history(self, ctx, code: str, limit: int = 10):
        """Lihat history stock produk"""
        try:
            # Validasi input
            if not input_validator.validate_product_code(code):
                await ctx.send(embed=message_formatter.error_embed("Kode produk tidak valid"))
                return
            
            # Validasi limit
            if limit < 1 or limit > 50:
                await ctx.send(embed=message_formatter.error_embed("Limit harus antara 1-50"))
                return
            
            # Ambil history stock
            response = await self.product_service.get_stock_history(code.upper(), limit)
            
            if not response.success or not response.data:
                await ctx.send(embed=message_formatter.info_embed(f"Tidak ada history stock untuk {code.upper()}"))
                return
            
            embed = discord.Embed(
                title=f"📦 History Stock - {code.upper()}",
                description=f"Menampilkan {len(response.data)} aktivitas stock terakhir",
                color=0x00ff00
            )
            
            for i, stock in enumerate(response.data[:10], 1):  # Limit display to 10
                action = stock.get('action', 'Unknown')
                quantity = stock.get('quantity', 0)
                admin = stock.get('admin', 'Unknown')
                timestamp = stock.get('timestamp', 'Unknown')
                
                embed.add_field(
                    name=f"{i}. {action}",
                    value=f"Quantity: {quantity}\nAdmin: {admin}\nWaktu: {timestamp}",
                    inline=True
                )
            
            if len(response.data) > 10:
                embed.set_footer(text=f"Menampilkan 10 dari {len(response.data)} aktivitas")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error stock history: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat mengambil history stock"))
    
    @commands.command(name="reducestock")
    async def reduce_stock(self, ctx, code: str, amount: int):
        """Kurangi stock produk"""
        try:
            # Validasi input
            if not input_validator.validate_product_code(code):
                await ctx.send(embed=message_formatter.error_embed("Kode produk tidak valid"))
                return
            
            if amount <= 0:
                await ctx.send(embed=message_formatter.error_embed("Jumlah harus lebih dari 0"))
                return
            
            # Kurangi stock
            response = await self.product_service.reduce_stock(
                code.upper(), 
                amount, 
                str(ctx.author.id)
            )
            
            if response.success:
                embed = message_formatter.success_embed(
                    f"Stock berhasil dikurangi!\n"
                    f"Produk: {code.upper()}\n"
                    f"Dikurangi: {amount}\n"
                    f"Stock tersisa: {response.data.get('remaining_stock', 'Unknown')}"
                )
            else:
                embed = message_formatter.error_embed(f"Gagal mengurangi stock: {response.error}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error reduce stock: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat mengurangi stock"))

async def setup(bot):
    """Setup admin transaction cog"""
    try:
        await bot.add_cog(AdminTransactionCog(bot))
        logger.info("Admin transaction cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load admin transaction cog: {e}")
        raise
