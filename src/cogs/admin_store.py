"""
Admin Store Management - Manajemen produk dan toko
Menangani command untuk mengelola produk
"""

import discord
from discord.ext import commands
import logging

from src.cogs.admin_base import AdminBaseCog
from src.services.product_service import ProductService
from src.utils.formatters import message_formatter
from src.utils.validators import input_validator

logger = logging.getLogger(__name__)

class AdminStoreCog(AdminBaseCog):
    """Cog untuk manajemen store admin"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.product_service = ProductService(bot.db_manager)
    
    @commands.command(name="addproduct")
    async def add_product(self, ctx, code: str, name: str, price: str, *, description: str = None):
        """Tambah produk baru"""
        try:
            # Validasi input
            if not input_validator.validate_product_code(code):
                await ctx.send(embed=message_formatter.error_embed("Kode produk tidak valid"))
                return
            
            validated_price = input_validator.validate_price(price)
            if not validated_price:
                await ctx.send(embed=message_formatter.error_embed("Harga tidak valid"))
                return
            
            # Buat produk
            success = await self.product_service.create_product(
                code.upper(), name, validated_price, description
            )
            
            if success:
                embed = message_formatter.success_embed(
                    f"Produk berhasil ditambahkan!\n"
                    f"Kode: {code.upper()}\n"
                    f"Nama: {name}\n"
                    f"Harga: {validated_price:,} WL"
                )
            else:
                embed = message_formatter.error_embed("Gagal menambahkan produk")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error add product: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat menambah produk"))
    
    @commands.command(name="removeproduct")
    async def remove_product(self, ctx, code: str):
        """Hapus produk"""
        try:
            success = await self.product_service.delete_product(code.upper())
            
            if success:
                embed = message_formatter.success_embed(f"Produk {code.upper()} berhasil dihapus!")
            else:
                embed = message_formatter.error_embed("Gagal menghapus produk atau produk tidak ditemukan")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error remove product: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat menghapus produk"))
    
    @commands.command(name="deleteproduct")
    async def delete_product(self, ctx, code: str):
        """Hapus produk (alias untuk removeproduct)"""
        await self.remove_product(ctx, code)
    
    @commands.command(name="editproduct")
    async def edit_product(self, ctx, code: str, field: str, *, value: str):
        """Edit detail produk"""
        try:
            # Validasi field yang bisa diedit
            valid_fields = ['name', 'price', 'description']
            if field.lower() not in valid_fields:
                await ctx.send(embed=message_formatter.error_embed(
                    f"Field tidak valid. Field yang bisa diedit: {', '.join(valid_fields)}"
                ))
                return
            
            # Validasi input berdasarkan field
            if field.lower() == 'price':
                validated_value = input_validator.validate_price(value)
                if not validated_value:
                    await ctx.send(embed=message_formatter.error_embed("Harga tidak valid"))
                    return
                value = validated_value
            
            # Update produk
            success = await self.product_service.update_product(
                code.upper(), field.lower(), value
            )
            
            if success:
                embed = message_formatter.success_embed(
                    f"Produk {code.upper()} berhasil diupdate!\n"
                    f"Field: {field}\n"
                    f"Nilai baru: {value}"
                )
            else:
                embed = message_formatter.error_embed("Gagal mengupdate produk atau produk tidak ditemukan")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error edit product: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat mengedit produk"))
    
    @commands.command(name="addworld")
    async def add_world(self, ctx, name: str, *, description: str = None):
        """Tambah informasi world"""
        try:
            # Implementasi sederhana untuk menyimpan info world
            # Bisa dikembangkan lebih lanjut sesuai kebutuhan
            embed = message_formatter.success_embed(
                f"World berhasil ditambahkan!\n"
                f"Nama: {name}\n"
                f"Deskripsi: {description or 'Tidak ada deskripsi'}"
            )
            
            await ctx.send(embed=embed)
            logger.info(f"World {name} added by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error add world: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat menambah world"))
    
    @commands.command(name="addstock")
    async def add_stock(self, ctx, code: str, *, content: str = None):
        """Tambah stock untuk produk"""
        try:
            # Validasi input
            if not input_validator.validate_product_code(code):
                await ctx.send(embed=message_formatter.error_embed("Kode produk tidak valid"))
                return
            
            # Jika tidak ada content, cek apakah ada attachment
            if not content and not ctx.message.attachments:
                error_msg = ("Harap berikan content stock atau lampirkan file!\n"
                           "Contoh: `!addstock BUAH content stock disini`\n"
                           "Atau lampirkan file text dengan daftar stock")
                await ctx.send(embed=message_formatter.error_embed(error_msg))
                return
            
            # Jika ada attachment, baca content dari file
            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                if attachment.filename.endswith(('.txt', '.csv')):
                    try:
                        file_content = await attachment.read()
                        content = file_content.decode('utf-8')
                    except Exception as e:
                        await ctx.send(embed=message_formatter.error_embed(f"Gagal membaca file: {e}"))
                        return
                else:
                    await ctx.send(embed=message_formatter.error_embed("File harus berformat .txt atau .csv"))
                    return
            
            if not content or not content.strip():
                await ctx.send(embed=message_formatter.error_embed("Content stock tidak boleh kosong"))
                return
            
            # Tambah stock
            response = await self.product_service.add_stock(
                code.upper(), 
                content.strip(), 
                str(ctx.author.id)
            )
            
            if response.success:
                data = response.data
                success_msg = (f"Stock berhasil ditambahkan!\n"
                             f"Produk: {code.upper()}\n"
                             f"Total baris: {data.get('total_lines', 1)}\n"
                             f"Berhasil ditambahkan: {data.get('success_count', 1)}\n"
                             f"Gagal: {data.get('failed_count', 0)}\n"
                             f"Ditambahkan oleh: {ctx.author.mention}")
                embed = message_formatter.success_embed(success_msg)
                
                # Clear cache stock untuk produk ini agar live display terupdate
                try:
                    live_stock_cog = self.bot.get_cog('LiveStockCog')
                    if live_stock_cog and hasattr(live_stock_cog, 'stock_manager'):
                        await live_stock_cog.stock_manager.clear_stock_cache(code.upper())
                        logger.info(f"✅ Stock cache cleared for product: {code.upper()}")
                except Exception as e:
                    logger.warning(f"Failed to clear stock cache: {e}")
            else:
                embed = message_formatter.error_embed(f"Gagal menambah stock: {response.error}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error add stock: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat menambah stock"))

    @commands.command(name="listproducts")
    async def list_products(self, ctx):
        """Tampilkan daftar semua produk"""
        try:
            products_response = await self.product_service.get_all_products()
            
            if not products_response.success or not products_response.data:
                await ctx.send(embed=message_formatter.info_embed("Tidak ada produk yang tersedia"))
                return
            
            embed = discord.Embed(
                title="📦 Daftar Produk",
                color=0x00ff00
            )
            
            for product in products_response.data[:10]:  # Limit 10 produk
                embed.add_field(
                    name=f"{product['code']} - {product['name']}",
                    value=f"Harga: {product['price']:,} WL",
                    inline=False
                )
            
            if len(products_response.data) > 10:
                embed.set_footer(text=f"Menampilkan 10 dari {len(products_response.data)} produk")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error list products: {e}")
            await ctx.send(embed=message_formatter.error_embed("Terjadi error saat mengambil daftar produk"))

async def setup(bot):
    """Setup admin store cog"""
    try:
        await bot.add_cog(AdminStoreCog(bot))
        logger.info("Admin store cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load admin store cog: {e}")
        raise
