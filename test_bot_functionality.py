#!/usr/bin/env python3
"""
Test Script untuk Bot Functionality
Test fungsionalitas kritis bot tanpa perlu koneksi Discord
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from src.services.tenant_service import TenantService
from src.database.connection import DatabaseManager
from src.bot.config import config_manager

async def test_config_loading():
    """Test loading konfigurasi bot"""
    print("🔧 Testing config loading...")
    try:
        config = config_manager.load_config()
        assert config is not None
        assert 'token' in config
        assert 'guild_id' in config
        print("✅ Config loading: PASSED")
        return True
    except Exception as e:
        print(f"❌ Config loading: FAILED - {e}")
        return False

async def test_database_connection():
    """Test koneksi database"""
    print("🗄️ Testing database connection...")
    try:
        db_manager = DatabaseManager()
        success = await db_manager.initialize()
        if success:
            print("✅ Database connection: PASSED")
            await db_manager.close()
            return True
        else:
            print("❌ Database connection: FAILED")
            return False
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
        return False

async def test_tenant_service():
    """Test tenant service functionality"""
    print("🏢 Testing tenant service...")
    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        tenant_service = TenantService(db_manager)
        
        # Test folder path methods
        tenant_path = tenant_service._get_tenant_folder_path("test_tenant")
        template_path = tenant_service._get_template_folder_path()
        
        assert tenant_path is not None
        assert template_path is not None
        
        print("✅ Tenant service: PASSED")
        await db_manager.close()
        return True
    except Exception as e:
        print(f"❌ Tenant service: FAILED - {e}")
        return False

async def test_tenant_folder_structure():
    """Test struktur folder tenant"""
    print("📁 Testing tenant folder structure...")
    try:
        # Check if tenant folders exist
        tenant_root = Path("tenants")
        template_path = tenant_root / "template"
        active_path = tenant_root / "active"
        backups_path = tenant_root / "backups"
        
        assert tenant_root.exists(), "Folder tenants tidak ada"
        assert template_path.exists(), "Folder template tidak ada"
        assert active_path.exists(), "Folder active tidak ada"
        assert backups_path.exists(), "Folder backups tidak ada"
        
        # Check template config
        config_file = template_path / "config" / "tenant_config.json"
        assert config_file.exists(), "File tenant_config.json tidak ada"
        
        print("✅ Tenant folder structure: PASSED")
        return True
    except Exception as e:
        print(f"❌ Tenant folder structure: FAILED - {e}")
        return False

async def test_cog_loading():
    """Test apakah cog dapat dimuat"""
    print("🔌 Testing cog loading...")
    try:
        # Import cog yang sudah diperbaiki
        from src.cogs.tenant_bot_manager import TenantBotManager
        
        # Check if method name is correct
        assert hasattr(TenantBotManager, 'instance_status'), "Method instance_status tidak ada"
        assert not hasattr(TenantBotManager, 'bot_instance_status'), "Method bot_instance_status masih ada"
        
        print("✅ Cog loading: PASSED")
        return True
    except Exception as e:
        print(f"❌ Cog loading: FAILED - {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Bot Functionality Tests...")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_database_connection,
        test_tenant_service,
        test_tenant_folder_structure,
        test_cog_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
        print("-" * 30)
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! Bot functionality is working correctly.")
        return True
    else:
        print(f"⚠️ {total - passed} tests FAILED. Please check the issues above.")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
