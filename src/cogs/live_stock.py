"""
Live Stock Cog Wrapper
Wrapper untuk mengintegrasikan LiveStockManager ke dalam sistem cogs
"""

import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

class LiveStockWrapper(commands.Cog):
    """Wrapper cog untuk live stock functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("LiveStockWrapper")
        
    async def cog_load(self):
        """Called when the cog is loaded"""
        try:
            # Import dan setup live stock manager langsung
            from src.ui.views.live_stock_view import LiveStockCog
            live_stock_cog = LiveStockCog(self.bot)
            await self.bot.add_cog(live_stock_cog)
            self.logger.info("Live stock cog loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load live stock cog: {e}", exc_info=True)

async def setup(bot):
    """Setup the LiveStock wrapper cog"""
    if not hasattr(bot, 'live_stock_wrapper_loaded'):
        await bot.add_cog(LiveStockWrapper(bot))
        bot.live_stock_wrapper_loaded = True
        logger.info('LiveStock wrapper cog loaded successfully')
