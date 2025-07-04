"""
Donation Cog
Menangani sistem donasi untuk bot Discord
"""

import discord
from discord.ext import commands
import logging
from src.services.donation_service import DonationManager

class DonationCog(commands.Cog):
    """Cog untuk sistem donasi"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("DonationCog")
        self.donation_manager = DonationManager(bot)
        
    async def cog_load(self):
        """Setup saat cog dimuat"""
        self.logger.info("DonationCog loading...")
        
        # Setup balance manager
        from src.services.balance_service import BalanceManagerService
        self.donation_manager.balance_manager = BalanceManagerService(self.bot)
        
        self.logger.info("DonationCog loaded successfully")
        
    async def cog_unload(self):
        """Cleanup saat cog di-unload"""
        self.logger.info("DonationCog unloaded")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen untuk pesan di channel donation"""
        # Skip jika bukan dari channel donation
        donation_channel_id = self.bot.config.get('id_donation_log')
        if not donation_channel_id or message.channel.id != donation_channel_id:
            return
            
        # Skip jika pesan dari bot sendiri
        if message.author == self.bot.user:
            return
            
        # Proses pesan donation
        await self.donation_manager.process_donation_message(message)

async def setup(bot):
    """Setup donation cog"""
    if not hasattr(bot, 'donation_cog_loaded'):
        cog = DonationCog(bot)
        await bot.add_cog(cog)
        bot.donation_cog_loaded = True
        logging.info('Donation cog loaded successfully')
