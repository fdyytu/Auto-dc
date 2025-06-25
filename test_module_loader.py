#!/usr/bin/env python3
"""
Test script untuk menguji sistem pemuatan modul bot
Tanpa perlu koneksi Discord yang sebenarnya
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.bot.module_loader import ModuleLoader

class MockBot:
    """Mock bot untuk testing module loader"""
    
    def __init__(self):
        self.extensions = {}
        self.loaded_extensions = []
        self.failed_extensions = []
    
    async def load_extension(self, name):
        """Mock load_extension"""
        try:
            # Simulasi import module
            import importlib
            module = importlib.import_module(name)
            
            # Cek apakah ada setup function
            if hasattr(module, 'setup'):
                # Simulasi pemanggilan setup
                if asyncio.iscoroutinefunction(module.setup):
                    await module.setup(self)
                else:
                    module.setup(self)
            
            self.extensions[name] = module
            self.loaded_extensions.append(name)
            print(f"✅ Successfully loaded: {name}")
            
        except Exception as e:
            self.failed_extensions.append((name, str(e)))
            print(f"❌ Failed to load {name}: {e}")
            raise e
    
    async def unload_extension(self, name):
        """Mock unload_extension"""
        if name in self.extensions:
            del self.extensions[name]
            if name in self.loaded_extensions:
                self.loaded_extensions.remove(name)
            print(f"🔄 Unloaded: {name}")

async def test_module_loader():
    """Test fungsi module loader"""
    print("🧪 Testing Module Loader System...")
    print("=" * 50)
    
    # Buat mock bot
    mock_bot = MockBot()
    
    # Buat module loader
    loader = ModuleLoader(mock_bot)
    
    # Test pemuatan semua modul
    print("\n🚀 Testing load_all_modules()...")
    success = await loader.load_all_modules()
    
    print("\n📊 Hasil Testing:")
    print(f"Success: {success}")
    print(f"Loaded modules: {len(loader.get_loaded_modules())}")
    print(f"Failed modules: {len(loader.get_failed_modules())}")
    
    print("\n✅ Modul yang berhasil dimuat:")
    for module in loader.get_loaded_modules():
        print(f"   - {module}")
    
    if loader.get_failed_modules():
        print("\n❌ Modul yang gagal dimuat:")
        for module, error in loader.get_failed_modules():
            print(f"   - {module}: {error}")
    
    print("\n🔄 Testing unload_all_cogs()...")
    await loader.unload_all_cogs()
    
    print("\n✅ Test selesai!")

if __name__ == "__main__":
    asyncio.run(test_module_loader())
