"""
Quantity Modal untuk input jumlah pembelian
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import discord
from discord.ui import Modal, TextInput
import logging

from config.constants import COLORS, MESSAGES
from ext.product_manager import ProductManagerService
from ext.balance_manager import BalanceManagerService
from ext.trx import TransactionManager

logger = logging.getLogger(__name__)

class QuantityModal(Modal):
    def __init__(self, product_code: str, max_quantity: int):
        super().__init__(title="🛍️ Jumlah Pembelian")
        self.product_code = product_code

        self.quantity = TextInput(
            label="Masukkan jumlah yang ingin dibeli",
            placeholder=f"Maksimal {max_quantity}",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.quantity)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            quantity = int(self.quantity.value)
            if quantity <= 0:
                raise ValueError(MESSAGES.ERROR['INVALID_AMOUNT'])

            product_service = ProductManagerService(interaction.client)
            balance_service = BalanceManagerService(interaction.client)
            trx_manager = TransactionManager(interaction.client)

            # Get product details
            product_response = await product_service.get_product(self.product_code)
            if not product_response.success:
                raise ValueError(product_response.error)

            product = product_response.data

            # Verify stock
            stock_response = await product_service.get_stock_count(self.product_code)
            if not stock_response.success:
                raise ValueError(stock_response.error)

            if stock_response.data < quantity:
                raise ValueError(MESSAGES.ERROR['INSUFFICIENT_STOCK'])

            # Calculate total price
            total_price = float(product['price']) * quantity

            # Get user's GrowID
            growid_response = await balance_service.get_growid(str(interaction.user.id))
            if not growid_response.success:
                raise ValueError(growid_response.error)

            growid = growid_response.data

            # Verify balance
            balance_response = await balance_service.get_balance(growid)
            if not balance_response.success:
                raise ValueError(balance_response.error)

            balance = balance_response.data
            if balance.total_wl() < total_price:
                raise ValueError(MESSAGES.ERROR['INSUFFICIENT_BALANCE'])

            # Process purchase
            purchase_response = await trx_manager.process_purchase(
                growid=growid,
                product_code=self.product_code,
                quantity=quantity,
                price=total_price
            )

            if not purchase_response.success:
                raise ValueError(purchase_response.error)

            # Create success message
            embed = discord.Embed(
                title="✅ Pembelian Berhasil",
                color=COLORS.SUCCESS
            )

            embed.add_field(
                name="Detail Pembelian",
                value=(
                    f"```yml\n"
                    f"Produk   : {product['name']}\n"
                    f"Jumlah   : {quantity}x\n"
                    f"Harga    : {total_price} WL\n"
                    f"GrowID   : {growid}\n"
                    "```"
                ),
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in QuantityModal: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=MESSAGES.ERROR['TRANSACTION_FAILED'],
                color=COLORS.ERROR
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
