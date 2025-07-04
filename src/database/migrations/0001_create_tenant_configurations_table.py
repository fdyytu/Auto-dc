"""
Migration to create tenant_configurations table
"""

def upgrade(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenant_configurations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT UNIQUE NOT NULL,
        bot_token TEXT NOT NULL,
        donation_channel_id TEXT,
        other_channel_ids TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

def downgrade(cursor):
    cursor.execute("DROP TABLE IF EXISTS tenant_configurations")
