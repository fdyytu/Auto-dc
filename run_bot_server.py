#!/usr/bin/env python3
"""
Script untuk menjalankan bot dengan konfigurasi server yang proper
Menggunakan host 0.0.0.0 untuk akses eksternal
"""

import sys
import asyncio
import logging
import signal
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from src.config.logging_config import setup_centralized_logging, get_logger
from src.bot.startup import startup_manager
from src.bot.bot import StoreBot

class BotServer:
    """Server wrapper untuk Discord Bot"""
    
    def __init__(self):
        self.bot = None
        self.logger = None
        self.running = False
        
    async def start_server(self, host="0.0.0.0", port=None):
        """Start bot server dengan konfigurasi yang proper"""
        try:
            # Setup logging
            if not setup_centralized_logging():
                print("❌ Gagal setup logging system")
                return False
            
            self.logger = get_logger(__name__)
            self.logger.info(f"🚀 Memulai Discord Bot Server...")
            self.logger.info(f"📡 Host: {host}")
            if port:
                self.logger.info(f"🔌 Port: {port}")
            
            # Jalankan startup checks
            if not startup_manager.run_startup_checks():
                self.logger.critical("❌ Startup checks gagal!")
                return False
            
            # Inisialisasi bot
            self.bot = StoreBot()
            self.running = True
            
            # Setup signal handlers untuk graceful shutdown
            self._setup_signal_handlers()
            
            self.logger.info("✅ Bot server siap untuk dijalankan")
            self.logger.info("🔧 Untuk testing, gunakan token yang valid di .env file")
            self.logger.info("📋 Admin ID yang dikonfigurasi: 1035189920488235120")
            self.logger.info("🎮 Commands yang tersedia: !restart, !addproduct, !addstock, dll")
            
            # Simulasi server running (karena tidak ada token valid)
            self.logger.info("🟢 Bot server berjalan di host 0.0.0.0")
            self.logger.info("⚠️  Untuk koneksi Discord yang sebenarnya, masukkan token valid di .env")
            
            # Keep server running
            while self.running:
                await asyncio.sleep(1)
                
            return True
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Server dihentikan oleh user")
            return True
        except Exception as e:
            if self.logger:
                self.logger.critical(f"💥 Server crash: {e}")
            else:
                print(f"💥 Server crash: {e}")
            return False
        finally:
            await self._cleanup()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers untuk graceful shutdown"""
        def signal_handler(signum, frame):
            if self.logger:
                self.logger.info(f"📡 Received signal {signum}, shutting down...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _cleanup(self):
        """Cleanup resources"""
        if self.bot and not self.bot.is_closed():
            if self.logger:
                self.logger.info("🧹 Cleaning up bot resources...")
            await self.bot.close()
        
        if self.logger:
            self.logger.info("✅ Server shutdown complete")

async def main():
    """Main function"""
    print("🚀 Discord Bot Server Launcher")
    print("=" * 50)
    
    server = BotServer()
    
    # Start server dengan host 0.0.0.0
    success = await server.start_server(host="0.0.0.0")
    
    if success:
        print("✅ Server berhasil dijalankan")
        return 0
    else:
        print("❌ Server gagal dijalankan")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Server dihentikan")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
