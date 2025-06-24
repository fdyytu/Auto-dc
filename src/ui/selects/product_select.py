"""
Product Select untuk memilih produk yang akan dibeli
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import discord
from discord.ui import Select
from typing import List, Dict
import logging

from src.config.constants import COLORS, MESSAGES
from src.ui.modals.quantity_modal import QuantityModal

logger = logging.getLogger(__name__)

class ProductSelect(Select):
    def __init__(self, products: List[Dict], balance_service, product_service, trx_manager):
        self.products_cache = {p['code']: p for p in products}
        self.balance_service = balance_service
        self.product_service = product_service
        self.trx_manager = trx_manager

        options = [
            discord.SelectOption(
                label=f"{product['name']}",
                description=f"Stok: {product['stock']} | Harga: {product['price']} WL",
                value=product['code'],
                emoji="🛍️"
            ) for product in products[:25]  # Discord limit 25 options
        ]
        super().__init__(
            placeholder="Pilih produk yang ingin dibeli...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            selected_code = self.values[0]
            product_response = await self.product_service.get_product(selected_code)
            if not product_response.success:
                raise ValueError(product_response.error)

            selected_product = product_response.data

            # Verifikasi stock realtime
            stock_response = await self.product_service.get_stock_count(selected_code)
            if not stock_response.success:
                raise ValueError(stock_response.error)

            current_stock = stock_response.data
            if current_stock <= 0:
                raise ValueError(MESSAGES.ERROR['OUT_OF_STOCK'])

            # Verifikasi user balance
            growid_response = await self.balance_service.get_growid(str(interaction.user.id))
            if not growid_response.success:
                raise ValueError(growid_response.error)

            growid = growid_response.data
            if not growid:
                raise ValueError(MESSAGES.ERROR['NOT_REGISTERED'])

            await interaction.followup.send_modal(
                QuantityModal(selected_code, min(current_stock, 999))
            )

        except Exception as e:
            logger.error(f"Error in ProductSelect: {e}")
            error_msg = str(e) if isinstance(e, ValueError) else MESSAGES.ERROR['TRANSACTION_FAILED']
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=error_msg,
                    color=COLORS.ERROR
                ),
                ephemeral=True
            )
