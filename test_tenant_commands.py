#!/usr/bin/env python3
"""
Test Tenant Commands Functionality
Test command tenant tanpa perlu koneksi Discord aktual
"""

import sys
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from src.services.tenant_service import TenantService
from src.database.connection import DatabaseManager

async def test_tenant_folder_creation():
    """Test pembuatan folder tenant"""
    print("📁 Testing tenant folder creation...")
    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        tenant_service = TenantService(db_manager)
        
        # Test create tenant folder structure
        test_tenant_id = "test_tenant_123"
        test_discord_id = "123456789"
        test_guild_id = "987654321"
        test_bot_token = "test_token"
        
        # Clean up if exists
        tenant_path = tenant_service._get_tenant_folder_path(test_tenant_id)
        if tenant_path.exists():
            import shutil
            shutil.rmtree(tenant_path)
        
        # Test creation
        response = await tenant_service.create_tenant_folder_structure(
            test_tenant_id, test_discord_id, test_guild_id, test_bot_token
        )
        
        assert response.success, f"Failed to create tenant folder: {response.message}"
        assert tenant_path.exists(), "Tenant folder was not created"
        
        # Verify config file
        config_path = tenant_path / "config" / "tenant_config.json"
        assert config_path.exists(), "Config file was not created"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        assert config['tenant_info']['tenant_id'] == test_tenant_id
        assert config['tenant_info']['discord_id'] == test_discord_id
        assert config['tenant_info']['guild_id'] == test_guild_id
        
        print("✅ Tenant folder creation: PASSED")
        
        # Clean up
        import shutil
        shutil.rmtree(tenant_path)
        
        await db_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ Tenant folder creation: FAILED - {e}")
        return False

async def test_tenant_config_reading():
    """Test pembacaan konfigurasi tenant"""
    print("📖 Testing tenant config reading...")
    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        tenant_service = TenantService(db_manager)
        
        # Create a test tenant first
        test_tenant_id = "test_read_123"
        test_discord_id = "123456789"
        test_guild_id = "987654321"
        test_bot_token = "test_token"
        
        # Clean up if exists
        tenant_path = tenant_service._get_tenant_folder_path(test_tenant_id)
        if tenant_path.exists():
            import shutil
            shutil.rmtree(tenant_path)
        
        # Create tenant
        create_response = await tenant_service.create_tenant_folder_structure(
            test_tenant_id, test_discord_id, test_guild_id, test_bot_token
        )
        assert create_response.success, "Failed to create tenant for reading test"
        
        # Test reading
        read_response = await tenant_service.get_tenant_config_from_file(test_tenant_id)
        assert read_response.success, f"Failed to read tenant config: {read_response.message}"
        
        config = read_response.data
        assert config['tenant_info']['tenant_id'] == test_tenant_id
        assert config['tenant_info']['discord_id'] == test_discord_id
        
        print("✅ Tenant config reading: PASSED")
        
        # Clean up
        import shutil
        shutil.rmtree(tenant_path)
        
        await db_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ Tenant config reading: FAILED - {e}")
        return False

async def test_tenant_folder_removal():
    """Test penghapusan folder tenant dengan backup"""
    print("🗑️ Testing tenant folder removal...")
    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        tenant_service = TenantService(db_manager)
        
        # Create a test tenant first
        test_tenant_id = "test_remove_123"
        test_discord_id = "123456789"
        test_guild_id = "987654321"
        test_bot_token = "test_token"
        
        # Clean up if exists
        tenant_path = tenant_service._get_tenant_folder_path(test_tenant_id)
        if tenant_path.exists():
            import shutil
            shutil.rmtree(tenant_path)
        
        # Create tenant
        create_response = await tenant_service.create_tenant_folder_structure(
            test_tenant_id, test_discord_id, test_guild_id, test_bot_token
        )
        assert create_response.success, "Failed to create tenant for removal test"
        assert tenant_path.exists(), "Tenant folder was not created"
        
        # Test removal
        remove_response = await tenant_service.remove_tenant_folder_structure(test_tenant_id)
        assert remove_response.success, f"Failed to remove tenant folder: {remove_response.message}"
        assert not tenant_path.exists(), "Tenant folder was not removed"
        
        # Check if backup was created
        backup_path = Path(remove_response.data['backup_path'])
        assert backup_path.exists(), "Backup was not created"
        
        print("✅ Tenant folder removal: PASSED")
        
        # Clean up backup
        import shutil
        shutil.rmtree(backup_path)
        
        await db_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ Tenant folder removal: FAILED - {e}")
        return False

async def test_tenant_cog_methods():
    """Test method tenant cog yang sudah diperbaiki"""
    print("🔧 Testing tenant cog methods...")
    try:
        from src.cogs.tenant_bot_manager import TenantBotManager
        
        # Mock bot object
        mock_bot = Mock()
        
        # Create TenantBotManager instance
        tenant_manager = TenantBotManager(mock_bot)
        
        # Check if methods exist and are callable
        assert hasattr(tenant_manager, 'instance_status'), "Method instance_status tidak ada"
        assert callable(getattr(tenant_manager, 'instance_status')), "Method instance_status tidak callable"
        
        # Check if old method is removed
        assert not hasattr(tenant_manager, 'bot_instance_status'), "Method bot_instance_status masih ada"
        
        # Check other methods
        assert hasattr(tenant_manager, 'create_bot_instance'), "Method create_bot_instance tidak ada"
        assert hasattr(tenant_manager, 'start_bot_instance'), "Method start_bot_instance tidak ada"
        assert hasattr(tenant_manager, 'stop_bot_instance'), "Method stop_bot_instance tidak ada"
        
        print("✅ Tenant cog methods: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Tenant cog methods: FAILED - {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Tenant Commands Tests...")
    print("=" * 50)
    
    tests = [
        test_tenant_folder_creation,
        test_tenant_config_reading,
        test_tenant_folder_removal,
        test_tenant_cog_methods
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
        print("🎉 All tenant tests PASSED! Tenant functionality is working correctly.")
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
