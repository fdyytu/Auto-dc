"""
Shop Business Logic Service
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from config.constants import MESSAGES, COLORS
from data.models.balance import Balance
from services.product_service import ProductService
from services.balance_service import BalanceService
from services.transaction_service import TransactionService
from services.admin_service import AdminService

logger = logging.getLogger(__name__)

class ShopService:
    """Business logic untuk shop operations"""
    
    def __init__(self, bot):
        self.bot = bot
        self.product_service = ProductService(bot.db_manager)
        self.balance_service = BalanceService(bot.db_manager)
        self.trx_manager = TransactionService(bot.db_manager)
        self.admin_service = AdminService(bot.db_manager)
        self.logger = logger

    async def get_available_products(self) -> Dict:
        """Get list of available products with stock"""
        try:
            products_response = await self.product_service.get_all_products()
            if not products_response.success:
                return {
                    'success': False,
                    'error': products_response.error,
                    'data': None
                }

            products = []
            for product in products_response.data:
                # Get current stock
                stock_response = await self.product_service.get_stock_count(product['code'])
                if stock_response.success and stock_response.data > 0:
                    product['stock'] = stock_response.data
                    products.append(product)

            return {
                'success': True,
                'error': None,
                'data': products
            }

        except Exception as e:
            self.logger.error(f"Error getting available products: {e}")
            return {
                'success': False,
                'error': MESSAGES.ERROR['TRANSACTION_FAILED'],
                'data': None
            }

    async def validate_purchase(self, user_id: str, product_code: str, quantity: int) -> Dict:
        """Validate if purchase can be made"""
        try:
            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                return {
                    'success': False,
                    'error': MESSAGES.ERROR['MAINTENANCE_MODE'],
                    'data': None
                }

            # Get user's GrowID
            growid_response = await self.balance_service.get_growid(user_id)
            if not growid_response.success:
                return {
                    'success': False,
                    'error': growid_response.error,
                    'data': None
                }

            growid = growid_response.data
            if not growid:
                return {
                    'success': False,
                    'error': MESSAGES.ERROR['USER_NOT_REGISTERED'],
                    'data': None
                }

            # Get product details
            product_response = await self.product_service.get_product(product_code)
            if not product_response.success:
                return {
                    'success': False,
                    'error': product_response.error,
                    'data': None
                }

            product = product_response.data

            # Check stock
            stock_response = await self.product_service.get_stock_count(product_code)
            if not stock_response.success:
                return {
                    'success': False,
                    'error': stock_response.error,
                    'data': None
                }

            if stock_response.data < quantity:
                return {
                    'success': False,
                    'error': MESSAGES.ERROR['OUT_OF_STOCK'].format(
                        product_name=product['name']
                    ),
                    'data': None
                }

            # Check balance
            balance_response = await self.balance_service.get_balance(growid)
            if not balance_response.success:
                return {
                    'success': False,
                    'error': balance_response.error,
                    'data': None
                }

            balance = balance_response.data
            total_price = float(product['price']) * quantity

            if balance.total_wl() < total_price:
                shortage = total_price - balance.total_wl()
                return {
                    'success': False,
                    'error': MESSAGES.ERROR['INSUFFICIENT_BALANCE'].format(
                        required=f"{total_price} WL",
                        current=balance.format(),
                        shortage=f"{shortage} WL"
                    ),
                    'data': None
                }

            return {
                'success': True,
                'error': None,
                'data': {
                    'growid': growid,
                    'product': product,
                    'total_price': total_price,
                    'balance': balance
                }
            }

        except Exception as e:
            self.logger.error(f"Error validating purchase: {e}")
            return {
                'success': False,
                'error': MESSAGES.ERROR['TRANSACTION_FAILED'],
                'data': None
            }

    async def process_purchase(self, user_id: str, product_code: str, quantity: int) -> Dict:
        """Process the actual purchase"""
        try:
            # Validate purchase first
            validation = await self.validate_purchase(user_id, product_code, quantity)
            if not validation['success']:
                return validation

            validation_data = validation['data']
            
            # Process the purchase
            purchase_response = await self.trx_manager.process_purchase(
                growid=validation_data['growid'],
                product_code=product_code,
                quantity=quantity,
                price=validation_data['total_price']
            )

            if not purchase_response.success:
                return {
                    'success': False,
                    'error': purchase_response.error,
                    'data': None
                }

            # Get updated balance
            balance_response = await self.balance_service.get_balance(validation_data['growid'])
            updated_balance = balance_response.data if balance_response.success else validation_data['balance']

            return {
                'success': True,
                'error': None,
                'data': {
                    'product': validation_data['product'],
                    'quantity': quantity,
                    'total_price': validation_data['total_price'],
                    'growid': validation_data['growid'],
                    'remaining_balance': updated_balance,
                    'items': purchase_response.data.get('items', [])
                }
            }

        except Exception as e:
            self.logger.error(f"Error processing purchase: {e}")
            return {
                'success': False,
                'error': MESSAGES.ERROR['TRANSACTION_FAILED'],
                'data': None
            }

    async def get_user_balance_info(self, user_id: str) -> Dict:
        """Get user balance and transaction history"""
        try:
            # Check maintenance mode
            if await self.admin_service.is_maintenance_mode():
                return {
                    'success': False,
                    'error': MESSAGES.ERROR['MAINTENANCE_MODE'],
                    'data': None
                }

            # Get user's GrowID
            growid_response = await self.balance_service.get_growid(user_id)
            if not growid_response.success:
                return {
                    'success': False,
                    'error': growid_response.error,
                    'data': None
                }

            growid = growid_response.data
            if not growid:
                return {
                    'success': False,
                    'error': MESSAGES.ERROR['USER_NOT_REGISTERED'],
                    'data': None
                }

            # Get balance
            balance_response = await self.balance_service.get_balance(growid)
            if not balance_response.success:
                return {
                    'success': False,
                    'error': balance_response.error,
                    'data': None
                }

            balance = balance_response.data

            # Get transaction history
            trx_response = await self.trx_manager.get_transaction_history(growid, limit=5)
            transactions = trx_response.data if trx_response.success else []

            return {
                'success': True,
                'error': None,
                'data': {
                    'growid': growid,
                    'balance': balance,
                    'transactions': transactions
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting user balance info: {e}")
            return {
                'success': False,
                'error': MESSAGES.ERROR['TRANSACTION_FAILED'],
                'data': None
            }
