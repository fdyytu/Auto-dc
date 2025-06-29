"""
Admin Commands - Main entry point
Mengatur loading semua admin cogs yang sudah dipecah
"""

import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

async def setup(bot):
    """Setup semua admin cogs"""
    try:
        # Load semua admin cogs
        admin_cogs = [
            'src.cogs.admin_base',
            'src.cogs.admin_store', 
            'src.cogs.admin_balance',
            'src.cogs.admin_system',
            'src.cogs.admin_transaction',
            'src.cogs.admin_backup'  # Tambahan untuk backup/restore
        ]
        
        for cog in admin_cogs:
            try:
                await bot.load_extension(cog)
                logger.info(f"✅ Loaded {cog}")
            except Exception as e:
                logger.error(f"❌ Failed to load {cog}: {e}")
                
        logger.info("Admin cogs setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup admin cogs: {e}")
        raise
