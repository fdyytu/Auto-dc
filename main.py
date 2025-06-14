#!/usr/bin/env python3
"""
Discord Bot untuk Store DC
Entry point utama aplikasi

Author: fdyyuk
Restructured: 2025-01-XX
"""

import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import core modules
from core.logging import logging_manager
from core.startup import startup_manager
from core.bot import StoreBot

async def main():
    """Fungsi utama untuk menjalankan bot"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Setup logging
        if not logging_manager.setup_logging():
            print("Gagal setup logging system")
            sys.exit(1)
        
        logger = logging.getLogger(__name__)
        logger.info("Memulai Discord Bot...")
        
        # Jalankan startup checks
        if not startup_manager.run_startup_checks():
            logger.critical("Startup checks gagal!")
            sys.exit(1)
        
        # Inisialisasi dan jalankan bot
        bot = StoreBot()
        
        async with bot:
            await bot.start(bot.config['token'])
            
            # Tunggu bot siap dengan timeout
            try:
                await asyncio.wait_for(bot._ready.wait(), timeout=60)
                logger.info("Bot berhasil dijalankan!")
            except asyncio.TimeoutError:
                logger.critical("Bot gagal siap dalam 60 detik")
                await bot.close()
                return
    
    except KeyboardInterrupt:
        logger.info("Bot dihentikan oleh user")
    except Exception as e:
        logger.critical(f"Bot crash: {e}", exc_info=True)
    finally:
        if 'bot' in locals() and not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
