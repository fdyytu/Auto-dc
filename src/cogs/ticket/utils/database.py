"""
Ticket Database Handler
Handles all database operations for the ticket system
"""

import sqlite3
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class TicketDB:
    def __init__(self):
        self.db_path = "shop.db"

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def setup_tables(self):
        """Setup necessary database tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Ticket settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_settings (
                    guild_id TEXT PRIMARY KEY,
                    category_id TEXT,
                    log_channel_id TEXT,
                    support_role_id TEXT,
                    max_tickets INTEGER DEFAULT 1,
                    ticket_format TEXT DEFAULT 'ticket-{user}-{number}',
                    auto_close_hours INTEGER DEFAULT 48,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tickets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    reason TEXT,
                    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    closed_by TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Ticket responses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE CASCADE
                )
            """)

            # Create indexes
            indexes = [
                ("idx_tickets_guild", "tickets(guild_id)"),
                ("idx_tickets_channel", "tickets(channel_id)"),
                ("idx_tickets_user", "tickets(user_id)"),
                ("idx_tickets_status", "tickets(status)"),
                ("idx_ticket_responses_ticket", "ticket_responses(ticket_id)"),
                ("idx_ticket_responses_user", "ticket_responses(user_id)")
            ]

            for idx_name, idx_cols in indexes:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_cols}")

            conn.commit()
            logger.info("✅ Ticket system tables setup completed")

        except sqlite3.Error as e:
            logger.error(f"❌ Failed to setup ticket tables: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def get_guild_settings(self, guild_id: int) -> Dict:
        """Get ticket settings for a guild"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM ticket_settings WHERE guild_id = ?
            """, (str(guild_id),))
            
            data = cursor.fetchone()
            
            if not data:
                return {
                    'category_id': None,
                    'log_channel_id': None,
                    'support_role_id': None,
                    'max_tickets': 1,
                    'ticket_format': 'ticket-{user}-{number}',
                    'auto_close_hours': 48
                }
                
            return dict(data)

        except sqlite3.Error as e:
            logger.error(f"Error fetching guild settings: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def create_ticket(self, guild_id: str, channel_id: str, user_id: str, reason: str) -> Optional[int]:
        """Create a new ticket record"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO tickets (guild_id, channel_id, user_id, reason)
                VALUES (?, ?, ?, ?)
            """, (guild_id, channel_id, user_id, reason))
            
            ticket_id = cursor.lastrowid
            
            # Log creation
            cursor.execute("""
                INSERT INTO admin_logs (admin_id, action, target, details)
                VALUES (?, ?, ?, ?)
            """, (user_id, 'ticket_create', channel_id, f"Ticket created: {reason}"))
            
            conn.commit()
            return ticket_id

        except sqlite3.Error as e:
            logger.error(f"Error creating ticket: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def close_ticket(self, ticket_id: int, closed_by: str) -> bool:
        """Close a ticket"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE tickets 
                SET status = 'closed', 
                    closed_at = CURRENT_TIMESTAMP,
                    closed_by = ?
                WHERE id = ?
            """, (closed_by, ticket_id))

            cursor.execute("""
                INSERT INTO admin_logs (admin_id, action, target, details)
                VALUES (?, ?, ?, ?)
            """, (closed_by, 'ticket_close', str(ticket_id), f"Ticket {ticket_id} closed"))

            conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Error closing ticket: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def save_responses(self, ticket_id: int, messages: List[Dict]) -> bool:
        """Save ticket responses/transcript"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for msg in messages:
                cursor.execute("""
                    INSERT INTO ticket_responses (ticket_id, user_id, content)
                    VALUES (?, ?, ?)
                """, (ticket_id, msg['author'], msg['content']))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving ticket responses: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def update_settings(self, guild_id: str, setting: str, value: str) -> bool:
        """Update ticket settings for a guild"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                INSERT OR REPLACE INTO ticket_settings (guild_id, {setting})
                VALUES (?, ?)
            """, (guild_id, value))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error updating ticket settings: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_active_tickets(self, guild_id: str, user_id: str) -> int:
        """Get count of active tickets for a user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM tickets 
                WHERE guild_id = ? AND user_id = ? AND status = 'open'
            """, (guild_id, user_id))
            
            return cursor.fetchone()[0]

        except sqlite3.Error as e:
            logger.error(f"Error getting active tickets: {e}")
            return 0
        finally:
            if conn:
                conn.close()
