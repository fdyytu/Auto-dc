"""
Live Buttons Cog Wrapper
Wrapper untuk mengintegrasikan LiveButtonsCog ke dalam sistem cogs
"""

import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

class LiveButtonsWrapper(commands.Cog):
    """Wrapper cog untuk live buttons functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("LiveButtonsWrapper")
        
    async def cog_load(self):
        """Called when the cog is loaded"""
        try:
            # Import dan setup live buttons manager langsung
            from src.ui.buttons.live_buttons import LiveButtonsCog
            
            # Cek apakah LiveButtonsCog sudah dimuat
            existing_cog = self.bot.get_cog('LiveButtonsCog')
            if existing_cog:
                self.logger.info("LiveButtonsCog sudah dimuat, skip loading")
                return
            
            live_buttons_cog = LiveButtonsCog(self.bot)
            await self.bot.add_cog(live_buttons_cog)
            self.logger.info("Live buttons cog loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load live buttons cog: {e}", exc_info=True)
            # Jangan raise error, biarkan wrapper tetap dimuat
            self.logger.warning("Continuing without live buttons functionality...")

async def setup(bot):
    """Setup the LiveButtons wrapper cog"""
    if not hasattr(bot, 'live_buttons_wrapper_loaded'):
        await bot.add_cog(LiveButtonsWrapper(bot))
        bot.live_buttons_wrapper_loaded = True
        logger.info('LiveButtons wrapper cog loaded successfully')
