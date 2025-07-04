"""
Database Migrations untuk Sistem Tenant
Script untuk membuat tabel-tabel tenant dan produk tenant
"""

import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_tenant_tables():
    """Buat tabel-tabel untuk sistem tenant"""
    try:
        # Connect ke database utama
        conn = sqlite3.connect('/home/user/workspace/dashboard/rental_bot.db')
        cursor = conn.cursor()
        
        # Tabel tenants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT UNIQUE NOT NULL,
                discord_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                plan TEXT NOT NULL DEFAULT 'basic',
                features TEXT DEFAULT '{}',
                channels TEXT DEFAULT '{}',
                permissions TEXT DEFAULT '{}',
                bot_config TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Tabel tenant_products
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenant_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT,
                category TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(tenant_id, code),
                FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
            )
        """)
        
        # Tabel tenant_stocks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenant_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                product_code TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'available',
                added_by TEXT NOT NULL,
                buyer_id TEXT,
                seller_id TEXT,
                purchase_price INTEGER,
                added_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
                FOREIGN KEY (tenant_id, product_code) REFERENCES tenant_products (tenant_id, code)
            )
        """)
        
        # Tabel tenant_transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenant_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                transaction_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                product_code TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                payment_method TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
            )
        """)
        
        # Index untuk performa
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenants_discord_id ON tenants (discord_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenant_products_tenant_id ON tenant_products (tenant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenant_stocks_tenant_product ON tenant_stocks (tenant_id, product_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenant_transactions_tenant_id ON tenant_transactions (tenant_id)")
        
        conn.commit()
        conn.close()
        
        logger.info("Tabel tenant berhasil dibuat")
        return True
        
    except Exception as e:
        logger.error(f"Error creating tenant tables: {e}")
        return False

def seed_sample_data():
    """Insert sample data untuk testing"""
    try:
        conn = sqlite3.connect('/home/user/workspace/dashboard/rental_bot.db')
        cursor = conn.cursor()
        
        # Sample tenant
        sample_tenant = {
            'tenant_id': 'tenant_sample01',
            'discord_id': '123456789012345678',
            'guild_id': '987654321098765432',
            'name': 'Sample Store',
            'status': 'active',
            'plan': 'premium',
            'features': '{"shop": true, "leveling": true, "automod": true}',
            'channels': '{"live_stock": "1234567890", "purchase_log": "0987654321"}',
            'permissions': '{"manage_products": true, "view_analytics": true}',
            'bot_config': '{"prefix": "!", "language": "id"}',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        cursor.execute("""
            INSERT OR IGNORE INTO tenants 
            (tenant_id, discord_id, guild_id, name, status, plan, features, channels, permissions, bot_config, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(sample_tenant.values()))
        
        # Sample products
        sample_products = [
            ('tenant_sample01', 'DL', 'Diamond Lock', 50000, 'Diamond Lock GT', 'locks'),
            ('tenant_sample01', 'WL', 'World Lock', 3000, 'World Lock GT', 'locks'),
            ('tenant_sample01', 'BGL', 'Blue Gem Lock', 150000, 'Blue Gem Lock GT', 'locks')
        ]
        
        for product in sample_products:
            cursor.execute("""
                INSERT OR IGNORE INTO tenant_products 
                (tenant_id, code, name, price, description, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, product + (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info("Sample data berhasil diinsert")
        return True
        
    except Exception as e:
        logger.error(f"Error seeding sample data: {e}")
        return False

if __name__ == "__main__":
    print("Membuat tabel tenant...")
    if create_tenant_tables():
        print("✅ Tabel tenant berhasil dibuat")
        
        print("Menambahkan sample data...")
        if seed_sample_data():
            print("✅ Sample data berhasil ditambahkan")
        else:
            print("❌ Gagal menambahkan sample data")
    else:
        print("❌ Gagal membuat tabel tenant")
